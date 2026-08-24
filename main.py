# -*- coding: utf-8 -*-
"""
Bản tin tổng hợp hằng ngày.
Luồng: RSS -> lọc 24h -> Gemini tóm tắt/xếp hạng -> gửi Telegram.
"""

import os
import re
import sys
import html
import time
import calendar
from datetime import datetime, timedelta, timezone
from concurrent.futures import ThreadPoolExecutor

import feedparser
import urllib.request
import urllib.parse

from feeds import FEEDS, KEYWORDS_CB

# ----------------------------------------------------------------------
# Cấu hình
# ----------------------------------------------------------------------
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "").strip()
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "").strip()

MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
HOURS_BACK = int(os.environ.get("HOURS_BACK", "26"))   # 26h để không hụt tin sát giờ
MAX_PER_FEED = 30
MAX_ITEMS_TO_AI = 220
VN_TZ = timezone(timedelta(hours=7))

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/125.0 Safari/537.36")


def log(msg):
    print(f"[{datetime.now(VN_TZ):%H:%M:%S}] {msg}", flush=True)


# ----------------------------------------------------------------------
# 1. Đọc RSS
# ----------------------------------------------------------------------
def clean(text, limit=180):
    """Bỏ thẻ HTML, gộp khoảng trắng, cắt ngắn."""
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:limit]


def fetch_one(item):
    url, source = item
    out = []
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=25) as resp:
            raw = resp.read()
        parsed = feedparser.parse(raw)
        if not parsed.entries:
            log(f"  (trống) {source}")
            return out
        for e in parsed.entries[:MAX_PER_FEED]:
            struct = e.get("published_parsed") or e.get("updated_parsed")
            if struct:
                published = datetime.fromtimestamp(
                    calendar.timegm(struct), tz=timezone.utc)
            else:
                published = None
            out.append({
                "title": clean(e.get("title", ""), 250),
                "summary": clean(e.get("summary", "") or e.get("description", "")),
                "link": (e.get("link") or "").strip(),
                "source": source,
                "published": published,
            })
        log(f"  OK  {source}: {len(out)} tin")
    except Exception as ex:
        log(f"  LỖI {source}: {type(ex).__name__} - {ex}")
    return out


def collect():
    log(f"Đọc {len(FEEDS)} nguồn RSS...")
    items = []
    with ThreadPoolExecutor(max_workers=8) as pool:
        for chunk in pool.map(fetch_one, FEEDS.items()):
            items.extend(chunk)

    cutoff = datetime.now(timezone.utc) - timedelta(hours=HOURS_BACK)
    fresh, seen = [], set()
    for it in items:
        if not it["title"] or not it["link"]:
            continue
        if it["published"] and it["published"] < cutoff:
            continue
        key = re.sub(r"[^a-z0-9à-ỹ]+", "", it["title"].lower())[:70]
        if key in seen:
            continue
        seen.add(key)
        fresh.append(it)

    fresh.sort(key=lambda x: x["published"] or datetime.min.replace(tzinfo=timezone.utc),
               reverse=True)
    log(f"Còn {len(fresh)} tin trong {HOURS_BACK}h qua (đã khử trùng lặp).")
    return fresh[:MAX_ITEMS_TO_AI]


def is_cb(item):
    blob = (item["title"] + " " + item["summary"]).lower()
    return any(k in blob for k in KEYWORDS_CB)


# ----------------------------------------------------------------------
# 2. Gọi Gemini
# ----------------------------------------------------------------------
PROMPT = """Bạn là trợ lý biên tập bản tin nội bộ cho một chuyên viên Lao động - Tiền lương \
tại một tổng công ty nhà nước ngành điện. Bản tin này sẽ được chuyển cho lãnh đạo đọc.

Dưới đây là danh sách tin bài đã xuất bản trong 24 giờ qua, lấy từ RSS của các báo điện tử \
chính thống. Tin nào có dấu [*] ở đầu là tin đã được lọc sơ bộ thuộc mảng lao động - tiền \
lương - bảo hiểm - thuế.

NHIỆM VỤ:

PHẦN A - TIN NỔI BẬT TRONG NGÀY
Chọn 10-12 tin quan trọng nhất, bao quát nhiều lĩnh vực (thời sự, kinh tế, pháp luật, \
quốc tế, công nghệ, xã hội). Ưu tiên tin có tác động rộng, tránh tin vụ án lặt vặt, tin \
giải trí, tin thể thao thường ngày, tin quảng cáo trá hình.
Mỗi tin viết đúng 2 dòng:
  Dòng 1: tiêu đề rút gọn dưới 15 từ
  Dòng 2: một câu nêu điểm cốt lõi, kèm tên báo và link

PHẦN B - CHUYÊN ĐỀ LAO ĐỘNG, TIỀN LƯƠNG, BHXH, THUẾ TNCN
Liệt kê TOÀN BỘ tin liên quan mảng này (kể cả tin nhỏ), tối đa 8 tin.
QUY TẮC BẮT BUỘC cho phần này:
- Chỉ nêu tiêu đề, tên cơ quan ban hành hoặc phát ngôn, tên báo và link.
- TUYỆT ĐỐI KHÔNG diễn giải nội dung pháp lý.
- TUYỆT ĐỐI KHÔNG trích số điều, khoản, tỷ lệ phần trăm, mức tiền, bậc thuế, \
số hiệu văn bản, ngày hiệu lực - trừ khi con số đó xuất hiện nguyên văn ngay trong \
tiêu đề tin được cung cấp.
- Không suy diễn, không bổ sung kiến thức của bạn.
- Nếu không có tin nào, ghi: "Không ghi nhận tin đáng chú ý trong 24h qua."

YÊU CẦU TRÌNH BÀY:
- Tiếng Việt, văn phong trang trọng, ngắn gọn.
- VĂN BẢN THUẦN. Không dùng dấu *, #, -, bảng, emoji, hay bất kỳ ký hiệu markdown nào. \
Đánh số thứ tự bằng "1." "2." "3.".
- Không viết lời mở đầu hay lời kết. Bắt đầu ngay bằng "PHAN A - TIN NOI BAT TRONG NGAY" \
(có dấu tiếng Việt đầy đủ).
- Chỉ dùng thông tin có trong danh sách dưới đây. Không bịa. Nếu một tin mơ hồ, bỏ qua.

DANH SÁCH TIN:
{items}
"""


def build_items_text(items):
    lines = []
    for i, it in enumerate(items, 1):
        flag = "[*] " if is_cb(it) else ""
        t = it["published"].astimezone(VN_TZ).strftime("%d/%m %H:%M") if it["published"] else "??"
        lines.append(f"{i}. {flag}{it['title']} | {it['summary']} | "
                     f"{it['source']} | {t} | {it['link']}")
    return "\n".join(lines)


def summarize(items):
    from google import genai
    client = genai.Client(api_key=GEMINI_API_KEY)
    prompt = PROMPT.format(items=build_items_text(items))
    log(f"Gửi {len(items)} tin cho {MODEL} (~{len(prompt)} ký tự)...")

    last_err = None
    for attempt in range(3):
        try:
            resp = client.models.generate_content(model=MODEL, contents=prompt)
            text = (resp.text or "").strip()
            if text:
                return text
            last_err = "phản hồi rỗng"
        except Exception as ex:
            last_err = f"{type(ex).__name__}: {ex}"
            log(f"  Gemini lỗi lần {attempt+1}: {last_err}")
            time.sleep(5 * (attempt + 1))
    raise RuntimeError(f"Gemini thất bại sau 3 lần: {last_err}")


# ----------------------------------------------------------------------
# 3. Gửi Telegram
# ----------------------------------------------------------------------
def send_telegram(text):
    api = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    # Telegram giới hạn 4096 ký tự/tin nhắn -> cắt theo dòng
    chunks, cur = [], ""
    for line in text.split("\n"):
        if len(cur) + len(line) + 1 > 3800:
            chunks.append(cur)
            cur = ""
        cur += line + "\n"
    if cur.strip():
        chunks.append(cur)

    for idx, chunk in enumerate(chunks, 1):
        suffix = f"\n\n(phần {idx}/{len(chunks)})" if len(chunks) > 1 else ""
        data = urllib.parse.urlencode({
            "chat_id": TELEGRAM_CHAT_ID,
            "text": chunk + suffix,
            "disable_web_page_preview": "true",
        }).encode()
        req = urllib.request.Request(api, data=data)
        with urllib.request.urlopen(req, timeout=30) as resp:
            resp.read()
        log(f"Đã gửi Telegram phần {idx}/{len(chunks)}")
        time.sleep(1)


# ----------------------------------------------------------------------
def main():
    missing = [n for n, v in [("GEMINI_API_KEY", GEMINI_API_KEY),
                              ("TELEGRAM_TOKEN", TELEGRAM_TOKEN),
                              ("TELEGRAM_CHAT_ID", TELEGRAM_CHAT_ID)] if not v]
    if missing:
        log(f"THIẾU biến môi trường: {', '.join(missing)}")
        sys.exit(1)

    items = collect()
    if not items:
        send_telegram("Bản tin hôm nay: không lấy được tin nào từ các nguồn RSS. "
                      "Kiểm tra lại log GitHub Actions.")
        return

    body = summarize(items)
    header = f"BẢN TIN TỔNG HỢP {datetime.now(VN_TZ):%d/%m/%Y}\n" + "=" * 32 + "\n\n"
    footer = ("\n\n" + "-" * 32 +
              "\nNguồn: RSS các báo điện tử. Nội dung do AI tổng hợp, "
              "vui lòng kiểm chứng văn bản gốc trước khi trích dẫn.")
    send_telegram(header + body + footer)
    log("Xong.")


if __name__ == "__main__":
    main()
