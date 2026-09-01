# -*- coding: utf-8 -*-
"""
Bot Quy định HR - tổng hợp văn bản pháp luật mới liên quan nghiệp vụ nhân sự.

KHÁC BIỆT CỐT LÕI so với bản tin C&B (main.py):

1. KHÔNG dùng AI. Chỉ lọc và liệt kê nguyên văn tiêu đề. Bản tin này phục vụ
   công việc nghiệp vụ; một con số do AI bịa ra có thể bị đem đi dùng thật.
   Không sinh chữ mới thì không thể bịa.

2. KHÔNG lọc theo cửa sổ thời gian. pubDate của ThuVienPhapLuat là NGÀY BAN
   HÀNH văn bản, không phải ngày lên feed - văn bản ban hành 19/08 có thể tới
   25/08 mới xuất hiện. Lọc 26h như bản tin C&B sẽ bỏ sót.
   Thay vào đó: ghi nhớ link đã gửi trong seen_quydinh.json, chỉ gửi cái mới.

3. CHỈ GỬI KHI CÓ VĂN BẢN MỚI. Ngày trống thì im lặng, tránh làm nhiễu.
   Riêng thứ Hai gửi thêm bản tổng kết tuần để biết hệ thống vẫn sống.
"""

import os
import re
import sys
import html
import json
import time
import calendar
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from concurrent.futures import ThreadPoolExecutor

import feedparser

from feeds_quydinh import (FEEDS, STRONG_KW, WEAK_KW, SCORE_THRESHOLD,
                           LOCAL_MARKERS, LOCAL_KEEP, GROUPS, GROUP_OTHER)

# ----------------------------------------------------------------------
# Cấu hình
# ----------------------------------------------------------------------
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN_QUYDINH", "").strip()
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
FORCE_RUN = os.environ.get("FORCE_RUN", "").strip().lower() in ("1", "true", "yes")

SEEN_FILE = "seen_quydinh.json"
SEEN_MAX = 600          # giữ tối đa 600 văn bản gần nhất, tránh file phình to
# Giới hạn số mục lấy về theo từng nguồn.
# TVPL là xương sống, có ~450 văn bản xếp theo NGÀY BAN HÀNH (không phải ngày
# lên feed) nên phải lấy hết; cắt 60 mục đầu sẽ mất gần như toàn bộ văn bản HR.
MAX_PER_FEED_DEFAULT = 40
MAX_PER_FEED_TVPL = 600

# Bỏ mục quá cũ. Feed BHXH lẫn cả tin từ 2017, 2021 xen giữa tin 2026.
MAX_AGE_DAYS = 45

MAX_VANBAN_IN_MSG = 20   # số văn bản tối đa mỗi bản tin
MAX_TIN_IN_MSG = 5       # tin ngành chỉ là phụ, chặn cứng để không lấn át
VN_TZ = timezone(timedelta(hours=7))

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/125.0 Safari/537.36")

# Nhận diện số hiệu ngay đầu tiêu đề. Đo thực tế trên 451 văn bản TVPL: khớp 91%.
RE_SOHIEU = re.compile(
    r"^(Nghị định|Thông tư|Thông tư liên tịch|Quyết định|Nghị quyết|Luật|"
    r"Pháp lệnh|Công văn|Kế hoạch|Chỉ thị|Công điện|Văn bản hợp nhất|Quy chuẩn)"
    r"\s+([\w\d/\-\.]+)", re.UNICODE)

# Bản tiếng Anh của cùng văn bản, TVPL đăng song song -> bỏ để khỏi trùng
RE_ENGLISH = re.compile(
    r"^(Decree|Circular|Decision|Law|Resolution|Ordinance|Directive|"
    r"Official Dispatch|Joint Circular)\s+No\.?", re.I)


def log(msg):
    print(f"[{datetime.now(VN_TZ):%H:%M:%S}] {msg}", flush=True)


def today_vn():
    return datetime.now(VN_TZ).strftime("%Y-%m-%d")


# ----------------------------------------------------------------------
# 1. Đọc RSS
# ----------------------------------------------------------------------
def clean(text, limit=400):
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()[:limit]


def fetch_one(entry):
    url, (source, kind) = entry
    out = []
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read()
        parsed = feedparser.parse(raw)
        if not parsed.entries:
            log(f"  (trống) {source}")
            return out
        limit = (MAX_PER_FEED_TVPL if "thuvienphapluat" in url
                 else MAX_PER_FEED_DEFAULT)
        for e in parsed.entries[:limit]:
            struct = e.get("published_parsed") or e.get("updated_parsed")
            pub = (datetime.fromtimestamp(calendar.timegm(struct), tz=timezone.utc)
                   if struct else None)
            out.append({
                "title": clean(e.get("title", "")),
                "link": (e.get("link") or "").strip(),
                "cat": clean(e.get("category", ""), 60),
                "source": source,
                "kind": kind,
                "pub": pub,
            })
        log(f"  OK  {source}: {len(out)} mục")
    except Exception as ex:
        log(f"  LỖI {source}: {type(ex).__name__} - {ex}")
    return out


def collect():
    log(f"Đọc {len(FEEDS)} nguồn...")
    items = []
    with ThreadPoolExecutor(max_workers=6) as pool:
        for chunk in pool.map(fetch_one, FEEDS.items()):
            items.extend(chunk)
    log(f"Thu được {len(items)} mục thô.")
    return items


# ----------------------------------------------------------------------
# 2. Lọc
# ----------------------------------------------------------------------
def score(item):
    t = item["title"].lower()
    s = 3 * sum(1 for k in STRONG_KW if k in t)
    s += 1 * sum(1 for k in WEAK_KW if k in t)
    return s


def is_other_province(title):
    """Văn bản của UBND/HĐND tỉnh khác -> bỏ. Giữ trung ương và TP.HCM."""
    if not any(m in title for m in LOCAL_MARKERS):
        return False                      # không phải văn bản địa phương
    low = title.lower()
    return not any(k in low for k in LOCAL_KEEP)


def sohieu_of(item):
    m = RE_SOHIEU.match(item["title"])
    return (m.group(1), m.group(2)) if m else (item.get("cat") or "", "")


def filter_items(items, seen):
    kept = []
    stats = {"english": 0, "province": 0, "lowscore": 0, "seen": 0, "cu": 0}
    titles_seen = set()
    cutoff = datetime.now(timezone.utc) - timedelta(days=MAX_AGE_DAYS)

    for it in items:
        if not it["title"] or not it["link"]:
            continue
        # Feed BHXH lẫn tin cũ từ nhiều năm trước -> loại theo tuổi
        if it["pub"] and it["pub"] < cutoff:
            stats["cu"] += 1
            continue
        if RE_ENGLISH.match(it["title"]):
            stats["english"] += 1
            continue
        if is_other_province(it["title"]):
            stats["province"] += 1
            continue
        if score(it) < SCORE_THRESHOLD:
            stats["lowscore"] += 1
            continue
        if it["link"] in seen:
            stats["seen"] += 1
            continue
        key = re.sub(r"[^a-z0-9à-ỹ]+", "", it["title"].lower())[:80]
        if key in titles_seen:
            continue
        titles_seen.add(key)
        loai, sh = sohieu_of(it)
        it["loai"], it["sohieu"] = loai, sh
        kept.append(it)

    log(f"Đã lọc bỏ: {stats['cu']} quá cũ (>{MAX_AGE_DAYS} ngày) | "
        f"{stats['english']} bản tiếng Anh | "
        f"{stats['province']} văn bản tỉnh khác | "
        f"{stats['lowscore']} không liên quan | {stats['seen']} đã gửi trước đó")
    nv = sum(1 for i in kept if i["kind"] == "vanban")
    log(f"Còn lại {len(kept)} mục MỚI ({nv} văn bản, {len(kept)-nv} tin ngành).")
    return kept


def group_of(item):
    t = item["title"].lower()
    for name, kws in GROUPS:
        if any(k in t for k in kws):
            return name
    return GROUP_OTHER


# ----------------------------------------------------------------------
# 3. Trình bày - văn bản thuần, không markdown
# ----------------------------------------------------------------------
def build_message(items):
    """Tách hẳn hai phần: VĂN BẢN (cốt lõi) và TIN NGÀNH (phụ, chặn cứng).
    Trộn chung thì tin tuyên truyền sẽ lấn át văn bản pháp quy."""
    vanban = [i for i in items if i["kind"] == "vanban"]
    tin = [i for i in items if i["kind"] != "vanban"]

    lines = [f"VĂN BẢN, QUY ĐỊNH MỚI - {datetime.now(VN_TZ):%d/%m/%Y}",
             "=" * 34, ""]

    if vanban:
        order = [g[0] for g in GROUPS] + [GROUP_OTHER]
        buckets = {g: [] for g in order}
        for it in vanban:
            buckets[group_of(it)].append(it)
        n = 0
        for g in order:
            rows = buckets[g]
            if not rows or n >= MAX_VANBAN_IN_MSG:
                continue
            lines += [g, ""]
            for it in rows:
                if n >= MAX_VANBAN_IN_MSG:
                    break
                n += 1
                lines.append(f"{n}. {it['title']}")
                ngay = (f"   Ban hành: {it['pub'].astimezone(VN_TZ):%d/%m/%Y}"
                        if it["pub"] else "   ")
                lines.append(f"{ngay}  |  Nguồn: {it['source']}")
                lines += [f"   {it['link']}", ""]
        if len(vanban) > n:
            lines += [f"(còn {len(vanban) - n} văn bản khác chưa liệt kê)", ""]
    else:
        lines += ["Không ghi nhận văn bản pháp luật mới trong đợt này.", ""]

    if tin:
        lines += ["TIN NGÀNH THAM KHẢO", ""]
        for i, it in enumerate(tin[:MAX_TIN_IN_MSG], 1):
            lines.append(f"{i}. {it['title']}")
            lines += [f"   {it['source']}  |  {it['link']}", ""]

    lines += ["-" * 34,
              "Bản tin chỉ liệt kê nguyên văn tiêu đề văn bản mới phát hiện.",
              "Nội dung, hiệu lực và số điều khoản phải tra cứu văn bản gốc",
              "trước khi áp dụng vào nghiệp vụ.",
              "Nguồn: thuvienphapluat.vn, baohiemxahoi.gov.vn, báo điện tử."]
    return "\n".join(lines)


def build_weekly(seen):
    """Tổng kết tuần, gửi sáng thứ Hai."""
    cutoff = (datetime.now(VN_TZ) - timedelta(days=7)).strftime("%Y-%m-%d")
    rows = [v for v in seen.values() if v.get("sent", "") >= cutoff]
    lines = [f"TỔNG KẾT TUẦN - {datetime.now(VN_TZ):%d/%m/%Y}", "=" * 34, ""]
    if not rows:
        lines.append("Tuần qua không ghi nhận văn bản mới liên quan")
        lines.append("nghiệp vụ lao động - tiền lương - bảo hiểm - thuế.")
    else:
        lines.append(f"Đã phát hiện {len(rows)} văn bản trong 7 ngày qua:")
        lines.append("")
        for i, r in enumerate(sorted(rows, key=lambda x: x.get("sent", ""),
                                     reverse=True)[:20], 1):
            lines.append(f"{i}. {r.get('title', '')[:130]}")
    lines += ["", "-" * 34, "Hệ thống đang hoạt động bình thường."]
    return "\n".join(lines)


# ----------------------------------------------------------------------
# 4. Bộ nhớ văn bản đã gửi
# ----------------------------------------------------------------------
def load_seen():
    try:
        with open(SEEN_FILE, encoding="utf-8") as f:
            data = json.load(f)
        log(f"Đã nhớ {len(data)} văn bản gửi trước đó.")
        return data
    except (FileNotFoundError, json.JSONDecodeError):
        log("Chưa có bộ nhớ, khởi tạo mới.")
        return {}


def save_seen(seen, new_items):
    for it in new_items:
        seen[it["link"]] = {"title": it["title"], "sent": today_vn()}
    if len(seen) > SEEN_MAX:
        kept = sorted(seen.items(), key=lambda kv: kv[1].get("sent", ""),
                      reverse=True)[:SEEN_MAX]
        seen = dict(kept)
        log(f"Đã cắt bộ nhớ về {SEEN_MAX} mục gần nhất.")
    with open(SEEN_FILE, "w", encoding="utf-8") as f:
        json.dump(seen, f, ensure_ascii=False, indent=1)
    log(f"Đã lưu bộ nhớ: {len(seen)} văn bản.")


# ----------------------------------------------------------------------
# 5. Gửi Telegram
# ----------------------------------------------------------------------
def send_telegram(text):
    api = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
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
    missing = [n for n, v in [("TELEGRAM_TOKEN_QUYDINH", TELEGRAM_TOKEN),
                              ("TELEGRAM_CHAT_ID", TELEGRAM_CHAT_ID)] if not v]
    if missing:
        log(f"THIẾU biến môi trường: {', '.join(missing)}")
        sys.exit(1)

    seen = load_seen()
    items = collect()

    if not items:
        log("Không lấy được mục nào từ mọi nguồn.")
        send_telegram("Bot Quy định HR: không lấy được dữ liệu từ nguồn nào. "
                      "Kiểm tra log GitHub Actions.")
        return

    fresh = filter_items(items, seen)

    # Thứ Hai: gửi tổng kết tuần trước, để biết hệ thống vẫn sống
    is_monday = datetime.now(VN_TZ).weekday() == 0
    if is_monday:
        send_telegram(build_weekly(seen))

    if not fresh:
        if FORCE_RUN:
            # Chạy tay: phải phản hồi để anh biết hệ thống còn sống,
            # nếu im lặng thì không phân biệt được "không có gì" với "hỏng".
            send_telegram(
                f"Bot Quy định HR - {datetime.now(VN_TZ):%d/%m/%Y %H:%M}\n\n"
                f"Đã quét {len(items)} mục từ {len(FEEDS)} nguồn.\n"
                f"Không có văn bản mới nào chưa từng gửi.\n"
                f"Bộ nhớ hiện có {len(seen)} văn bản.")
        else:
            log("Không có văn bản mới -> im lặng (đúng thiết kế, tránh nhiễu).")
        return

    send_telegram(build_message(fresh))
    save_seen(seen, fresh)   # ghi nhớ cả mục chưa liệt kê, tránh lặp vô hạn
    log("Xong.")


if __name__ == "__main__":
    main()
