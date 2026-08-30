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

from feeds import (FEEDS, STRONG_CB, WEAK_CB, STRONG_TECH, WEAK_TECH,
                   SOURCE_BOOST_CB, SOURCE_BOOST_TECH, SCORE_THRESHOLD)

# ----------------------------------------------------------------------
# Cấu hình
# ----------------------------------------------------------------------
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "").strip()
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "").strip()

# Model chính: Gemini 3.7 Flash (mạnh nhất trong nhóm free tier của bạn).
# Nếu model này bị khai tử hoặc sai tên, script sẽ tự thử các model dự phòng,
# và cuối cùng tự dò danh sách model khả dụng từ API.
MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.7-flash")
# Thứ tự dự phòng phải nhảy sang model KHÁC DÒNG.
# Bài học từ log ngày 30/08: khi 3.7-flash quá tải (503), script nhảy sang
# "gemini-flash-latest" - nhưng đó chỉ là ALIAS trỏ về chính 3.7-flash, nên
# vẫn nghẽn y hệt. Alias giờ để cuối cùng, chỉ dùng khi mọi tên cứng đều sai.
MODEL_FALLBACKS = [
    "gemini-3.7-flash",        # mạnh nhất - ưu tiên độ chính xác
    "gemini-3.6-flash",        # khác dòng - thoát được nghẽn của 3.7
    "gemini-3.5-flash-lite",   # nhẹ, ít nghẽn nhất
    "gemini-flash-latest",     # alias - lưới an toàn khi Google đổi tên model
]

# Ngân sách thời gian cho toàn bộ khâu gọi AI (giây).
# Workflow bị cắt ở phút 15. Dừng thử ở phút 8 để còn kịp gửi bản tin dự phòng
# thay vì bị giết ngang và anh không nhận được gì.
AI_TIME_BUDGET = 480
HOURS_BACK = int(os.environ.get("HOURS_BACK", "26"))   # 26h để không hụt tin sát giờ
MAX_PER_FEED = 30
MAX_ITEMS_TO_AI = 280
QUOTA_CB = 70          # suất dành riêng cho tin lao động/BHXH/thuế
QUOTA_TECH = 70        # suất dành riêng cho tin tài chính/công nghệ/AI
VN_TZ = timezone(timedelta(hours=7))

# File ghi dấu ngày đã gửi, nằm ngay trong repository và được commit ngược lại.
# Mục đích: có 2 lịch chạy/ngày (lịch chính + lịch dự phòng khi GitHub trễ),
# file này đảm bảo chỉ gửi bản tin 1 lần/ngày.
STATE_FILE = "last_run.txt"
FORCE_RUN = os.environ.get("FORCE_RUN", "").strip().lower() in ("1", "true", "yes")

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
    return fresh


# --- Biên dịch sẵn regex ranh giới từ (chạy 1 lần, nhanh) ---
def _compile(words):
    # (?<!\w) ... (?!\w) = ranh giới từ, có hiểu ký tự tiếng Việt.
    # Nhờ vậy "ai" không còn khớp vào hai/tai/thai/khai/trai/mai/sai.
    return [re.compile(r"(?<!\w)" + re.escape(w) + r"(?!\w)", re.UNICODE)
            for w in words]

_RE_STRONG_CB = _compile(STRONG_CB)
_RE_WEAK_CB = _compile(WEAK_CB)
_RE_STRONG_TECH = _compile(STRONG_TECH)
_RE_WEAK_TECH = _compile(WEAK_TECH)


def _blob(item):
    return (item["title"] + " " + item["summary"]).lower()


def _source_boost(item, table):
    src = item["source"]
    for prefix, pts in table.items():
        if src.startswith(prefix):
            return pts
    return 0


def score_cb(item):
    """Điểm mức độ thuộc mảng lao động - tiền lương - BHXH - thuế."""
    b = _blob(item)
    s = _source_boost(item, SOURCE_BOOST_CB)
    s += 3 * sum(1 for r in _RE_STRONG_CB if r.search(b))
    s += 1 * sum(1 for r in _RE_WEAK_CB if r.search(b))
    return s


def score_tech(item):
    """Điểm mức độ thuộc mảng tài chính - công nghệ - AI."""
    b = _blob(item)
    s = _source_boost(item, SOURCE_BOOST_TECH)
    s += 3 * sum(1 for r in _RE_STRONG_TECH if r.search(b))
    s += 1 * sum(1 for r in _RE_WEAK_TECH if r.search(b))
    return s


def is_cb(item):
    return score_cb(item) >= SCORE_THRESHOLD


def is_tech(item):
    return score_tech(item) >= SCORE_THRESHOLD


def select_by_quota(items):
    """Cấp suất riêng cho từng mảng. Trong mỗi suất, chọn theo ĐIỂM LIÊN QUAN
    (cao xuống thấp), không phải theo độ mới - để một tin BHXH quan trọng
    không bị 70 tin 'công tác nhân sự' đăng sau đẩy văng ra ngoài."""
    used = set()
    chosen = []

    def take(scorer, quota, label):
        ranked = []
        for idx, it in enumerate(items):
            if idx in used:
                continue
            sc = scorer(it)
            if sc >= SCORE_THRESHOLD:
                # điểm cao trước; cùng điểm thì tin mới trước (idx nhỏ = mới hơn)
                ranked.append((-sc, idx, it))
        ranked.sort()
        for _, idx, it in ranked[:quota]:
            used.add(idx)
            chosen.append(it)
        log(f"  {label}: {len(ranked)} tin đạt ngưỡng, lấy {min(len(ranked), quota)}")
        return min(len(ranked), quota)

    n_cb = take(score_cb, QUOTA_CB, "Lao động")
    n_tech = take(score_tech, QUOTA_TECH, "Tài chính-Công nghệ")

    n_gen = 0
    for idx, it in enumerate(items):
        if len(chosen) >= MAX_ITEMS_TO_AI:
            break
        if idx in used:
            continue
        used.add(idx)
        chosen.append(it)
        n_gen += 1

    log(f"Chọn gửi AI: {n_cb} lao động | {n_tech} tài chính-công nghệ "
        f"| {n_gen} tổng hợp = {len(chosen)} tin")
    return chosen


# ----------------------------------------------------------------------
# 2. Gọi Gemini
# ----------------------------------------------------------------------
PROMPT = """Bạn là trợ lý biên tập bản tin nội bộ cho một chuyên viên Lao động - Tiền lương \
tại một tổng công ty nhà nước ngành điện. Bản tin này sẽ được chuyển cho lãnh đạo đọc.

Dưới đây là danh sách tin bài đã xuất bản trong 24 giờ qua, lấy từ RSS của các báo điện tử \
chính thống Việt Nam và một số nguồn quốc tế. Dấu ở đầu mỗi tin là kết quả lọc sơ bộ:
  [LD] = thuộc mảng lao động, tiền lương, bảo hiểm, thuế
  [CN] = thuộc mảng tài chính, công nghệ, AI
Một số tin bằng tiếng Anh: hãy tóm tắt lại bằng tiếng Việt, giữ nguyên tên riêng.

NHIỆM VỤ:

PHẦN A - TIN NỔI BẬT TRONG NGÀY
Chọn 8-10 tin quan trọng nhất, bao quát nhiều lĩnh vực (thời sự, kinh tế, pháp luật, \
quốc tế, xã hội). Không lặp lại tin đã đưa ở Phần B hoặc Phần C. Ưu tiên tin có tác động rộng, tránh tin vụ án lặt vặt, tin \
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

PHẦN C - TÀI CHÍNH, CÔNG NGHỆ VÀ AI
Chia làm 3 mục nhỏ, mỗi mục 2-3 tin, trình bày như Phần A:

C1. Tài chính - kinh tế: lãi suất, tỷ giá, chứng khoán, giá vàng, chính sách thuế - \
ngân sách, tín dụng, diễn biến vĩ mô. Ưu tiên tin có tác động tới doanh nghiệp nhà nước \
và chi phí nhân công.

C2. Công nghệ và AI: sản phẩm hoặc mô hình AI mới, cập nhật lớn của Microsoft 365, \
Power Platform, Excel, công cụ tự động hóa văn phòng, an ninh mạng, chuyển đổi số.

C3. AI ứng dụng trong nhân sự: AI trong tuyển dụng, chấm công, tính lương, phân tích \
dữ liệu nhân sự, hoặc tác động của AI tới việc làm và cơ cấu lao động. Với mỗi tin, thêm \
một câu nêu rõ có thể áp dụng gì vào công việc Lao động - Tiền lương. \
Nếu không có tin nào phù hợp, ghi: "Không ghi nhận tin đáng chú ý trong 24h qua."

YÊU CẦU TRÌNH BÀY:
- Toàn bộ bản tin viết bằng tiếng Việt, văn phong trang trọng, ngắn gọn.
- Tổng độ dài tối đa khoảng 700 từ.
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
        if is_cb(it):
            flag = "[LD] "
        elif is_tech(it):
            flag = "[CN] "
        else:
            flag = ""
        t = it["published"].astimezone(VN_TZ).strftime("%d/%m %H:%M") if it["published"] else "??"
        lines.append(f"{i}. {flag}{it['title']} | {it['summary']} | "
                     f"{it['source']} | {t} | {it['link']}")
    return "\n".join(lines)


def discover_models(client):
    """Hỏi thẳng API xem tài khoản này đang dùng được model nào.
    Dùng khi mọi tên model cứng đều sai/bị khai tử. Ưu tiên Flash, tránh Lite."""
    try:
        names = []
        for m in client.models.list():
            actions = getattr(m, "supported_actions", None) or []
            if "generateContent" not in actions:
                continue
            name = (m.name or "").replace("models/", "")
            if "gemini" in name and "flash" in name:
                names.append(name)
        # Ưu tiên bản không phải "lite", số hiệu lớn xếp trước
        names.sort(key=lambda n: ("lite" in n, n), reverse=False)
        names.sort(key=lambda n: "lite" in n)
        log(f"  Model khả dụng phát hiện được: {names[:5]}")
        return names[:3]
    except Exception as ex:
        log(f"  Không dò được danh sách model: {ex}")
        return []


def summarize(items):
    from google import genai
    client = genai.Client(api_key=GEMINI_API_KEY)
    prompt = PROMPT.format(items=build_items_text(items))

    # Thứ tự thử: model chỉ định -> danh sách dự phòng -> tự dò từ API.
    candidates = [MODEL] + [m for m in MODEL_FALLBACKS if m != MODEL]
    last_err = None
    discovered = False
    started = time.time()

    def out_of_time():
        spent = time.time() - started
        if spent > AI_TIME_BUDGET:
            log(f"  Đã dùng {spent:.0f}s, vượt ngân sách {AI_TIME_BUDGET}s -> dừng thử.")
            return True
        return False

    while candidates:
        model_name = candidates.pop(0)
        log(f"Gửi {len(items)} tin cho {model_name} (~{len(prompt)} ký tự)...")

        # Mỗi model được thử tối đa 3 lần, nhưng model đang quá tải thì
        # chỉ 2 lần rồi chuyển sang model khác - chờ lâu vô ích vì nghẽn
        # nằm ở phía Google, không phải phía mình.
        max_attempts = 3
        attempt = 0
        while attempt < max_attempts:
            if out_of_time():
                raise RuntimeError(f"Hết ngân sách thời gian. Lỗi cuối: {last_err}")
            attempt += 1
            try:
                resp = client.models.generate_content(model=model_name,
                                                      contents=prompt)
                text = (resp.text or "").strip()
                if text:
                    log(f"  Thành công với model {model_name} "
                        f"sau {time.time()-started:.0f}s")
                    return text
                last_err = "phản hồi rỗng"
            except Exception as ex:
                last_err = f"{type(ex).__name__}: {ex}"
                blob = str(ex).lower()
                short = last_err[:110]
                log(f"  {model_name} lỗi lần {attempt}: {short}")

                # (a) Model không tồn tại / bị khai tử -> nhảy model khác ngay
                if "not_found" in blob or "no longer available" in blob:
                    log(f"  Model {model_name} không dùng được, chuyển model khác.")
                    break

                # (b) Model quá tải phía Google (503). Không phải lỗi hạn mức
                #     của mình. Thử thêm 1 lần rồi chuyển model KHÁC DÒNG.
                if ("unavailable" in blob or "503" in blob
                        or "overloaded" in blob or "high demand" in blob):
                    max_attempts = 2
                    if attempt >= max_attempts:
                        log(f"  {model_name} đang quá tải, chuyển model khác.")
                        break
                    time.sleep(15)
                    continue

                # (c) Hết hạn mức của mình -> chờ lâu hơn rồi thử lại
                if "resource_exhausted" in blob or "429" in blob:
                    time.sleep(20 * attempt)
                    continue

                # (d) Lỗi khác (mạng, timeout...) -> chờ ngắn rồi thử lại
                time.sleep(5 * attempt)

        # Đã thử hết tên cứng mà vẫn hỏng -> hỏi API xem có model nào dùng được
        if not candidates and not discovered:
            discovered = True
            log("Mọi model cố định đều thất bại, đang dò danh sách từ API...")
            candidates = discover_models(client)

    raise RuntimeError(f"Tất cả model đều thất bại. Lỗi cuối: {last_err}")


def fallback_digest(items, err):
    """Khi AI hỏng hoàn toàn: gửi danh sách tiêu đề thô, để anh vẫn có tin."""
    cb = [i for i in items if is_cb(i)][:10]
    other = [i for i in items if not is_cb(i)][:12]

    lines = ["(*) AI KHONG PHAN HOI - DAY LA DANH SACH TIEU DE THO",
             f"Loi: {err}", "", "PHẦN A - TIN MỚI NHẤT", ""]
    for n, it in enumerate(other, 1):
        lines.append(f"{n}. {it['title']}")
        lines.append(f"   {it['source']} - {it['link']}")
    lines += ["", "PHẦN B - LAO ĐỘNG, TIỀN LƯƠNG, BHXH, THUẾ", ""]
    if cb:
        for n, it in enumerate(cb, 1):
            lines.append(f"{n}. {it['title']}")
            lines.append(f"   {it['source']} - {it['link']}")
    else:
        lines.append("Không ghi nhận tin đáng chú ý trong 24h qua.")
    return "\n".join(lines)


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
# 4. Chống gửi trùng trong ngày
# ----------------------------------------------------------------------
def today_vn():
    return datetime.now(VN_TZ).strftime("%Y-%m-%d")


def already_sent_today():
    if FORCE_RUN:
        log("FORCE_RUN bật -> bỏ qua kiểm tra trùng ngày.")
        return False
    try:
        with open(STATE_FILE, encoding="utf-8") as f:
            last = f.read().strip()
    except FileNotFoundError:
        return False
    if last == today_vn():
        log(f"Bản tin ngày {last} đã gửi rồi -> thoát, không gửi lại.")
        return True
    log(f"Lần gửi gần nhất: {last or '(chưa có)'} | Hôm nay: {today_vn()}")
    return False


def mark_sent():
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        f.write(today_vn())
    log(f"Đã ghi dấu ngày gửi: {today_vn()}")


# ----------------------------------------------------------------------
def main():
    missing = [n for n, v in [("GEMINI_API_KEY", GEMINI_API_KEY),
                              ("TELEGRAM_TOKEN", TELEGRAM_TOKEN),
                              ("TELEGRAM_CHAT_ID", TELEGRAM_CHAT_ID)] if not v]
    if missing:
        log(f"THIẾU biến môi trường: {', '.join(missing)}")
        sys.exit(1)

    if already_sent_today():
        return

    items = select_by_quota(collect())
    if not items:
        send_telegram("Bản tin hôm nay: không lấy được tin nào từ các nguồn RSS. "
                      "Kiểm tra lại log GitHub Actions.")
        return

    try:
        body = summarize(items)
    except Exception as ex:
        log(f"AI thất bại hoàn toàn -> gửi bản dự phòng. {ex}")
        body = fallback_digest(items, ex)

    header = f"BẢN TIN TỔNG HỢP {datetime.now(VN_TZ):%d/%m/%Y}\n" + "=" * 32 + "\n\n"
    footer = ("\n\n" + "-" * 32 +
              "\nNguồn: RSS các báo điện tử. Nội dung do AI tổng hợp, "
              "vui lòng kiểm chứng văn bản gốc trước khi trích dẫn.")
    send_telegram(header + body + footer)
    mark_sent()
    log("Xong.")


if __name__ == "__main__":
    main()
