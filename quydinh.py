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

from feeds_quydinh import (FEEDS, STRONG_KW, MEDIUM_KW, WEAK_KW, SCORE_THRESHOLD,
                           LOCAL_MARKERS, LOCAL_KEEP, GROUPS, GROUP_OTHER,
                           GROUP_LOCAL)

# ----------------------------------------------------------------------
# Cấu hình
# ----------------------------------------------------------------------
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN_QUYDINH", "").strip()
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
FORCE_RUN = os.environ.get("FORCE_RUN", "").strip().lower() in ("1", "true", "yes")

# ---------------------------------------------------------------
# CẦU LẤY RSS QUA CLOUDFLARE WORKER
# ---------------------------------------------------------------
# ThuVienPhapLuat trả 403 Forbidden cho máy chủ GitHub Actions (dải IP
# Azure). Worker chạy trên hạ tầng Cloudflare - dải IP khác hẳn, nên có
# cơ hội lấy được feed mà GitHub không lấy được.
#
# Không khai hai biến này thì script vẫn chạy bình thường, chỉ là gọi
# thẳng như cũ và TVPL sẽ tiếp tục 403.
FEED_PROXY = os.environ.get("FEED_PROXY", "").strip().rstrip("/")
FEED_PROXY_SECRET = os.environ.get("FEED_PROXY_SECRET", "").strip()

# Nguồn nào đi qua cầu. Khóa là ĐOẠN NHẬN DẠNG trong URL, không phải URL
# đầy đủ - tra bằng phép kiểm tra chuỗi con, tránh lỗi khớp chính xác.
PROXY_SOURCES = {"thuvienphapluat.vn/rss.xml": "tvpl"}

SEEN_FILE = "seen_quydinh.json"
# Ghi dấu ngày đã gửi. Có HAI lịch cùng bắn (Cloudflare repository_dispatch
# chạy đúng giờ + GitHub schedule dự phòng chạy trễ). Từ khi bot báo cả khi
# không có văn bản mới, thiếu file này sẽ nhận 2 tin nhắn mỗi ngày.
LAST_RUN_FILE = "last_run_quydinh.txt"
SEEN_MAX = 600          # giữ tối đa 600 văn bản gần nhất, tránh file phình to
# Giới hạn số mục lấy về theo từng nguồn.
# TVPL là xương sống, có ~450 văn bản xếp theo NGÀY BAN HÀNH (không phải ngày
# lên feed) nên phải lấy hết; cắt 60 mục đầu sẽ mất gần như toàn bộ văn bản HR.
MAX_PER_FEED_DEFAULT = 40
MAX_PER_FEED_TVPL = 600
# Công báo cũng là nguồn văn bản -> lấy rộng hơn nguồn tin thường.
# Log 01/09 cho thấy nó bị cắt còn 40 mục, trong khi feed có nhiều hơn.
MAX_PER_FEED_CONGBAO = 150

# Bỏ mục quá cũ. Feed BHXH lẫn cả tin từ 2017, 2021 xen giữa tin 2026.
MAX_AGE_DAYS = 45

MAX_VANBAN_IN_MSG = 20   # số văn bản tối đa mỗi bản tin
MAX_TIN_IN_MSG = 5       # tin ngành chỉ là phụ, chặn cứng để không lấn át
MAX_LOCAL_IN_MSG = 6     # văn bản tỉnh khác: hữu ích để tham khảo nhưng
                         # không được lấn át văn bản trung ương
VN_TZ = timezone(timedelta(hours=7))

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/125.0 Safari/537.36")

# Một số trang (ThuVienPhapLuat) chặn máy chủ dựa trên bộ header.
# Gửi kèm bộ header giống trình duyệt thật để tăng khả năng qua được.
# KHÔNG đảm bảo: nếu họ chặn theo dải IP của Azure/GitHub thì vô hiệu.
BROWSER_HEADERS = {
    "User-Agent": UA,
    "Accept": "application/rss+xml, application/xml, text/xml, */*;q=0.8",
    "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept-Encoding": "identity",
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
}

# Nhận diện số hiệu ngay đầu tiêu đề. Đo thực tế trên 451 văn bản TVPL: khớp 91%.
RE_SOHIEU = re.compile(
    r"^(Nghị định|Thông tư|Thông tư liên tịch|Quyết định|Nghị quyết|Luật|"
    r"Pháp lệnh|Công văn|Kế hoạch|Chỉ thị|Công điện|Văn bản hợp nhất|Quy chuẩn)"
    r"\s+([\w\d/\-\.]+)", re.UNICODE)

# Bản tiếng Anh của cùng văn bản, TVPL đăng song song -> bỏ để khỏi trùng
RE_ENGLISH = re.compile(
    r"^(Decree|Circular|Decision|Law|Resolution|Ordinance|Directive|"
    r"Official Dispatch|Joint Circular)\s+No\.?", re.I)

# ----------------------------------------------------------------------
# CHUẨN HÓA NGÀY THÁNG TRONG XML THÔ  (nguyên nhân gốc của tin cũ)
# ----------------------------------------------------------------------
# Ba họ nguồn ghi ngày sai chuẩn RFC 822. feedparser trả None mà KHÔNG báo
# lỗi, nên mọi mục của nguồn đó mất ngày và lọt qua bộ lọc thời gian.
# Đo thực tế 10/09/2026:
#   tuoitre.vn/nld/...   "Fri, 26 Jun 2026 03:08:00 +07"      -> thiếu 2 số phút
#   tuoitre.vn/rss/...   "Sun, 14 Jun 2026 18:23:42 GMT+7"    -> "GMT+7" không hợp lệ
#   tuoitre.vn/<mục>.rss "9/1/2026 10:52:00 AM"               -> định dạng Mỹ, không múi giờ
# Vá ngay trên chuỗi XML thô, trước khi giao cho feedparser.

# (1) Múi giờ rút gọn / có tiền tố GMT  ->  +0700
_RE_TZ_FIX = re.compile(
    rb"(\d{2}:\d{2}:\d{2})\s*(?:GMT\s*)?([+-])(\d{1,2})(?::?(\d{2}))?(?![\d:])")

# (2) Ngày kiểu Mỹ M/D/YYYY h:mm:ss AM|PM. Chỉ thay TRONG thẻ ngày, không
#     đụng tới nội dung bài viết (mô tả có thể chứa chuỗi ngày tương tự).
_RE_USDATE = re.compile(
    rb"(<\s*(?:pubDate|lastBuildDate|dc:date)\s*>\s*(?:<!\[CDATA\[\s*)?)"
    rb"(\d{1,2})/(\d{1,2})/(\d{4})\s+(\d{1,2}):(\d{2}):(\d{2})\s*([AaPp])[Mm]")


def _tz_repl(m):
    gio = m.group(3)
    if len(gio) == 1:
        gio = b"0" + gio
    phut = m.group(4) or b"00"
    return m.group(1) + b" " + m.group(2) + gio + phut


def _us_repl(m):
    thang, ngay, nam = int(m.group(2)), int(m.group(3)), int(m.group(4))
    gio, phut, giay = int(m.group(5)), int(m.group(6)), int(m.group(7))
    chieu = m.group(8) in (b"P", b"p")
    if chieu and gio != 12:
        gio += 12
    if not chieu and gio == 12:
        gio = 0
    # Nguồn ghi giờ Việt Nam (lastBuildDate của chính feed ghi GMT+7).
    iso = f"{nam:04d}-{thang:02d}-{ngay:02d}T{gio:02d}:{phut:02d}:{giay:02d}+07:00"
    return m.group(1) + iso.encode()


# (3) Khoảng trắng Unicode. tuoitre.vn ngăn cách giây và AM/PM bằng
#     U+202F NARROW NO-BREAK SPACE (bytes \xe2\x80\xaf), KHÔNG phải dấu cách
#     thường. Trong regex kiểu bytes, "\s" chỉ khớp khoảng trắng ASCII nên
#     mọi mẫu ở trên đều trượt. Đây là lý do bản vá (2) không ăn ở lần thử
#     đầu - nhìn log chỉ thấy "9/10/2026 8:08:00 AM", tưởng là dấu cách.
#     Quy hết về dấu cách thường trước khi làm gì khác.
_RE_KHOANG_TRANG_LA = re.compile(
    rb"\xc2\xa0"                 # U+00A0 no-break space
    rb"|\xe2\x80[\x80-\x8a\xaf]"  # U+2000..U+200A, U+202F
    rb"|\xe2\x81\x9f"             # U+205F medium mathematical space
    rb"|\xe3\x80\x80")            # U+3000 ideographic space


def fix_short_tz(raw):
    """Chuẩn hóa mọi biến thể ngày về dạng feedparser đọc được.

    khoảng trắng Unicode         -> dấu cách thường
    'GMT+7' / '+07' / 'GMT+07:00' -> '+0700'
    '9/1/2026 10:52:00 AM'        -> '2026-09-01T10:52:00+07:00'
    Chuỗi đã đúng chuẩn ('+0700', '-0500', 'GMT') giữ nguyên.
    """
    raw = _RE_KHOANG_TRANG_LA.sub(b" ", raw)
    # TZ_FIX chạy TRƯỚC, nếu không nó sẽ đụng vào chuỗi ISO "+07:00" mà
    # USDATE vừa sinh ra và tách thành "T08:08:00 +0700" (vẫn đọc được
    # nhưng bẩn). Ngày kiểu Mỹ không có dấu +/- nên TZ_FIX không chạm tới.
    raw = _RE_TZ_FIX.sub(_tz_repl, raw)
    return _RE_USDATE.sub(_us_repl, raw)


# --- Chẩn đoán: in ra chuỗi ngày THÔ khi không parse được ---
# Đã ba lần đoán sai định dạng ngày của tuoitre.vn. Thay vì đoán tiếp,
# in thẳng chuỗi thô lấy từ XML ra log để nhìn tận mắt.
_RE_MAU_NGAY = re.compile(
    rb"<\s*(pubDate|lastBuildDate|dc:date|updated|published)[^>]*>"
    rb"\s*(?:<!\[CDATA\[)?\s*([^<\]]{1,80})",
    re.IGNORECASE)


def mau_ngay_tho(raw, n=3):
    """Trích tối đa n chuỗi ngày thô để in ra log khi feedparser bó tay."""
    ra = []
    for m in _RE_MAU_NGAY.finditer(raw):
        s = m.group(2).decode("utf-8", "replace").strip()
        if s:
            ra.append(f"<{m.group(1).decode()}> {s!r}")
        if len(ra) >= n:
            break
    return ra or ["(feed KHÔNG có thẻ ngày hợp lệ)"]


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

LOAI_MAP = {
    "nghi-dinh": "Nghị định", "thong-tu": "Thông tư",
    "thong-tu-lien-tich": "Thông tư liên tịch", "quyet-dinh": "Quyết định",
    "nghi-quyet": "Nghị quyết", "luat": "Luật", "phap-lenh": "Pháp lệnh",
    "cong-dien": "Công điện", "chi-thi": "Chỉ thị", "cong-van": "Công văn",
    "van-ban-hop-nhat": "Văn bản hợp nhất",
}
CODE_MAP = {"ND": "NĐ", "QD": "QĐ", "CD": "CĐ", "TTG": "TTg", "TD": "TĐ"}

def parse_congbao_slug(link):
    """Công báo để TRỐNG thẻ <title>; số hiệu chỉ nằm trong URL.
    vd .../nghi-dinh-so-320-2026-nd-cp-470285.htm -> ('Nghị định','320/2026/NĐ-CP')
    Đã kiểm chứng đúng 10/10 trên URL thật lấy từ feed."""
    m = re.search(r"/([a-z0-9\-]+?)-(\d+)\.htm", link)
    if not m:
        return "", ""
    slug = m.group(1)
    if "-so-" not in slug:
        return LOAI_MAP.get(slug, ""), ""
    prefix, rest = slug.split("-so-", 1)
    loai = LOAI_MAP.get(prefix, prefix.replace("-", " ").capitalize())
    nums, codes = [], []
    for t in rest.split("-"):
        if t.isdigit() and not codes:
            nums.append(t)
        else:
            codes.append(t)
    code = "-".join(CODE_MAP.get(c.upper(), c.upper()) for c in codes)
    return loai, "/".join(nums) + ("/" + code if code else "")

def fetch_one(entry):
    url, cfg = entry
    source, kind = cfg[0], cfg[1]
    parser = cfg[2] if len(cfg) > 2 else "std"
    out = []

    # Chọn đường đi: qua trạm trung chuyển nếu nguồn này bị chặn và
    # trạm đã được cấu hình; nếu không thì gọi thẳng.
    proxy_key = next((v for k, v in PROXY_SOURCES.items() if k in url), None)
    attempts = []
    if proxy_key and FEED_PROXY:
        h = dict(BROWSER_HEADERS)
        h["X-Proxy-Secret"] = FEED_PROXY_SECRET
        attempts.append((f"{FEED_PROXY}/feed?src={proxy_key}", h, "qua trạm"))
    attempts.append((url, BROWSER_HEADERS, "gọi thẳng"))

    raw, last_err = None, None
    for target, headers, how in attempts:
        try:
            req = urllib.request.Request(target, headers=headers)
            with urllib.request.urlopen(req, timeout=45) as resp:
                raw = resp.read()
            if len(attempts) > 1:
                log(f"  ({how} thành công) {source}")
            break
        except Exception as ex:
            last_err = ex
            if len(attempts) > 1:
                log(f"  ({how} thất bại) {source}: {type(ex).__name__} - {ex}")

    if raw is None:
        log(f"  LỖI {source}: {type(last_err).__name__} - {last_err}")
        return (source, out, False)

    try:
        parsed = feedparser.parse(fix_short_tz(raw))
        if not parsed.entries:
            log(f"  (trống) {source}")
            return (source, out, False)
        if "thuvienphapluat" in url:
            limit = MAX_PER_FEED_TVPL
        elif "congbao" in url:
            limit = MAX_PER_FEED_CONGBAO
        else:
            limit = MAX_PER_FEED_DEFAULT
        for e in parsed.entries[:limit]:
            struct = e.get("published_parsed") or e.get("updated_parsed")
            pub = (datetime.fromtimestamp(calendar.timegm(struct), tz=timezone.utc)
                   if struct else None)
            link = (e.get("link") or "").strip()
            title = clean(e.get("title", ""))
            cat = clean(e.get("category", ""), 60)

            if parser == "congbao":
                # Ghép lại tiêu đề: "<Loại> <số hiệu> <trích yếu>"
                trichyeu = clean(e.get("summary", "") or e.get("description", ""))
                loai, sohieu = parse_congbao_slug(link)
                if loai and sohieu:
                    title = f"{loai} {sohieu} {trichyeu}".strip()
                    cat = loai
                elif trichyeu:
                    title = trichyeu

            out.append({
                "title": title, "link": link, "cat": cat,
                "source": source, "kind": kind, "pub": pub,
            })
        # Ngày mới nhất của nguồn: nguồn văn bản đứng yên nhiều tuần là dấu
        # hiệu nguồn chết, phải nhìn thấy trong log chứ không im lặng.
        dates = [x["pub"] for x in out if x["pub"]]
        if dates:
            moi = max(dates)
            tuoi = (datetime.now(timezone.utc) - moi).total_seconds() / 86400
            log(f"  OK  {source}: {len(out)} mục | mới nhất "
                f"{moi.astimezone(VN_TZ):%d/%m/%Y} (cách {tuoi:.1f} ngày)")
        else:
            log(f"  OK  {source}: {len(out)} mục | KHÔNG mục nào đọc được ngày")
            for d in mau_ngay_tho(raw):
                log(f"       ngày thô: {d}")
        return (source, out, True)
    except Exception as ex:
        log(f"  LỖI {source}: {type(ex).__name__} - {ex}")
    return (source, out, False)

def collect():
    # In cấu hình trạm ra log. FEED_PROXY để dạng Variable (không phải Secret)
    # nên giá trị hiện rõ - sai chính tả tên miền là thấy ngay.
    if FEED_PROXY:
        log(f"Trạm lấy RSS: {FEED_PROXY}  | mã bí mật: "
            f"{'có, ' + str(len(FEED_PROXY_SECRET)) + ' ký tự' if FEED_PROXY_SECRET else 'CHƯA CÓ'}")
    else:
        log("Trạm lấy RSS: CHƯA KHAI (FEED_PROXY rỗng) -> mọi nguồn gọi thẳng.")
    log(f"Đọc {len(FEEDS)} nguồn...")
    items, nguon_ok, nguon_loi = [], [], []
    with ThreadPoolExecutor(max_workers=6) as pool:
        for source, chunk, ok in pool.map(fetch_one, FEEDS.items()):
            items.extend(chunk)
            (nguon_ok if ok else nguon_loi).append(source)
    log(f"Thu được {len(items)} mục thô. "
        f"Nguồn lấy được: {len(nguon_ok)}/{len(FEEDS)}.")
    if nguon_loi:
        log(f"Nguồn KHÔNG lấy được: {', '.join(nguon_loi)}")
    return items, nguon_ok, nguon_loi

# ----------------------------------------------------------------------
# 2. Lọc
# ----------------------------------------------------------------------
def score(item):
    t = item["title"].lower()
    s = 3 * sum(1 for k in STRONG_KW if k in t)
    s += 2 * sum(1 for k in MEDIUM_KW if k in t)
    s += 1 * sum(1 for k in WEAK_KW if k in t)
    return s

def is_other_province(title):
    """Văn bản do UBND/HĐND tỉnh KHÁC TP.HCM ban hành.
    Chỉ dùng để ĐÁNH DẤU xếp vào mục riêng, KHÔNG loại bỏ - đo trên dữ liệu
    thật cho thấy loại thẳng sẽ mất 8 văn bản liên quan nghiệp vụ."""
    if not any(m in title for m in LOCAL_MARKERS):
        return False
    low = title.lower()
    return not any(k in low for k in LOCAL_KEEP)

def sohieu_of(item):
    m = RE_SOHIEU.match(item["title"])
    return (m.group(1), m.group(2)) if m else (item.get("cat") or "", "")

def filter_items(items, seen):
    kept = []
    stats = {"english": 0, "lowscore": 0, "seen": 0, "cu": 0}
    titles_seen = set()
    near_miss = []
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
        sc = score(it)
        if sc < SCORE_THRESHOLD:
            stats["lowscore"] += 1
            # Giữ lại các mục SUÝT đạt ngưỡng để in ra log. Đây là cách duy
            # nhất đo được bộ lọc có bỏ sót gì không: nếu trong danh sách này
            # có thứ đáng đọc -> ngưỡng đang quá chặt, cần thêm từ khóa.
            if sc > 0 and it["kind"] == "vanban":
                near_miss.append((sc, it["title"]))
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
        it["local"] = is_other_province(it["title"])
        kept.append(it)

    log(f"Đã lọc bỏ: {stats['cu']} quá cũ (>{MAX_AGE_DAYS} ngày) | "
        f"{stats['english']} bản tiếng Anh | "
        f"{stats['lowscore']} không liên quan | {stats['seen']} đã gửi trước đó")
    nv = sum(1 for i in kept if i["kind"] == "vanban")
    nl = sum(1 for i in kept if i["kind"] == "vanban" and i.get("local"))
    log(f"Còn lại {len(kept)} mục MỚI ({nv} văn bản, trong đó {nl} của địa "
        f"phương khác; {len(kept)-nv} tin ngành).")

    # --- Bảng soát bỏ sót ---
    # In các văn bản đạt 1-2 điểm (ngay dưới ngưỡng {SCORE_THRESHOLD}).
    # Đọc danh sách này định kỳ: thấy tiêu đề nào đáng lẽ phải có trong bản
    # tin thì bổ sung từ khóa vào STRONG_KW/WEAK_KW trong feeds_quydinh.py.
    if near_miss:
        near_miss.sort(reverse=True)
        log(f"--- SOÁT BỎ SÓT: {len(near_miss)} văn bản đạt 1-{SCORE_THRESHOLD-1} "
            f"điểm (dưới ngưỡng {SCORE_THRESHOLD}). {min(len(near_miss), 15)} cái điểm cao nhất:")
        for sc, t in near_miss[:15]:
            log(f"      [{sc}đ] {t[:105]}")
        log("--- Hết bảng soát. Thấy cái nào đáng đọc -> thêm từ khóa.")

    stats["near_miss"] = near_miss
    return kept, stats

def group_of(item):
    if item.get("local"):
        return GROUP_LOCAL
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
        order = [g[0] for g in GROUPS] + [GROUP_OTHER, GROUP_LOCAL]
        buckets = {g: [] for g in order}
        for it in vanban:
            buckets[group_of(it)].append(it)
        n = 0
        n_local = 0
        for g in order:
            rows = buckets[g]
            if not rows:
                continue
            is_local_group = (g == GROUP_LOCAL)
            if not is_local_group and n >= MAX_VANBAN_IN_MSG:
                continue
            lines += [g, ""]
            for it in rows:
                # Hạn mức riêng: văn bản trung ương không bị văn bản tỉnh
                # chiếm chỗ, và ngược lại.
                if is_local_group:
                    if n_local >= MAX_LOCAL_IN_MSG:
                        break
                    n_local += 1
                elif n >= MAX_VANBAN_IN_MSG:
                    break
                else:
                    n += 1
                stt = n_local if is_local_group else n
                lines.append(f"{stt}. {it['title']}")
                ngay = (f"   Ban hành: {it['pub'].astimezone(VN_TZ):%d/%m/%Y}"
                        if it["pub"] else "   ")
                lines.append(f"{ngay}  |  Nguồn: {it['source']}")
                lines += [f"   {it['link']}", ""]
        shown = n + n_local
        if len(vanban) > shown:
            lines += [f"(còn {len(vanban) - shown} văn bản khác chưa liệt kê)", ""]
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
              "Nguồn: congbao.chinhphu.vn, thuvienphapluat.vn,",
              "baohiemxahoi.gov.vn và các báo điện tử."]
    return "\n".join(lines)

def build_trong(items, stats, seen, nguon_ok, ly_do):
    """Tin nhắn khi KHÔNG có văn bản mới.

    Theo thiết kế cũ bot im lặng để tránh nhiễu. Nay báo, nhưng phải kèm số
    liệu - nếu chỉ nhắn 'không có gì mới' thì sau hai tuần người đọc tắt
    thông báo, mà vẫn không phân biệt được 'thật sự không có' với 'hỏng'.
    """
    tong_nguon = len(FEEDS)
    lines = [
        f"QUY ĐỊNH HR - {datetime.now(VN_TZ):%d/%m/%Y %H:%M}",
        "=" * 34, "",
        ly_do, "",
        f"Đã quét : {len(items)} mục / {nguon_ok}/{tong_nguon} nguồn lấy được",
        f"Bỏ quá cũ (>{MAX_AGE_DAYS} ngày) : {stats.get('cu', 0)}",
        f"Bỏ do không đạt ngưỡng từ khóa   : {stats.get('lowscore', 0)}",
        f"Bỏ do đã gửi ở kỳ trước          : {stats.get('seen', 0)}",
        f"Bộ nhớ hiện có : {len(seen)} văn bản",
    ]
    nm = stats.get("near_miss") or []
    if nm:
        nm = sorted(nm, reverse=True)[:5]
        lines += ["", "Sát ngưỡng (không gửi, để anh soát bỏ sót):", ""]
        for sc, t in nm:
            lines.append(f"  [{sc}đ] {t[:110]}")
    lines += ["", "-" * 34, "Hệ thống hoạt động bình thường."]
    return "\n".join(lines)


def build_su_co(items, nguon_ok, nguon_loi):
    """Nguồn hỏng KHÁC HẲN 'không có văn bản mới'. Không được gộp làm một."""
    return "\n".join([
        f"CẢNH BÁO - QUY ĐỊNH HR - {datetime.now(VN_TZ):%d/%m/%Y %H:%M}",
        "=" * 34, "",
        "SỰ CỐ KỸ THUẬT, không phải 'không có văn bản mới'.", "",
        f"Chỉ {nguon_ok}/{len(FEEDS)} nguồn lấy được, thu {len(items)} mục.",
        f"Nguồn lỗi: {', '.join(nguon_loi) if nguon_loi else 'xem log'}",
        "", "-" * 34, "Mở GitHub Actions xem log để biết nguyên nhân.",
    ])


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
def da_gui_hom_nay():
    if FORCE_RUN:
        log("FORCE_RUN bật -> bỏ qua kiểm tra trùng ngày.")
        return False
    try:
        with open(LAST_RUN_FILE, encoding="utf-8") as f:
            last = f.read().strip()
    except FileNotFoundError:
        return False
    if last == today_vn():
        log(f"Đã gửi bản tin ngày {last} rồi -> thoát, không gửi lại.")
        return True
    log(f"Lần gửi gần nhất: {last or '(chưa có)'} | Hôm nay: {today_vn()}")
    return False


def ghi_dau_ngay():
    with open(LAST_RUN_FILE, "w", encoding="utf-8") as f:
        f.write(today_vn())
    log(f"Đã ghi dấu ngày gửi: {today_vn()}")


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
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                resp.read()
        except urllib.error.HTTPError as ex:
            # Telegram luôn kèm lý do cụ thể trong thân phản hồi.
            # Không đọc ra thì chỉ thấy "400 Bad Request" vô nghĩa.
            body = ""
            try:
                body = ex.read().decode("utf-8", "replace")[:300]
            except Exception:
                pass
            log(f"TELEGRAM TỪ CHỐI (mã {ex.code}): {body}")
            if "chat not found" in body:
                log("  -> Nguyên nhân: bot chưa từng có tương tác với chat này.")
                log("  -> Cách xử lý: mở bot trong Telegram và bấm Start,")
                log("     hoặc nhắn cho bot một tin bất kỳ, rồi chạy lại.")
            elif "bot was blocked" in body:
                log("  -> Nguyên nhân: bạn đã chặn bot. Bỏ chặn rồi chạy lại.")
            elif "unauthorized" in body.lower():
                log("  -> Nguyên nhân: sai TELEGRAM_TOKEN_QUYDINH.")
            elif "too long" in body:
                log("  -> Nguyên nhân: tin nhắn quá dài, giảm MAX_VANBAN_IN_MSG.")
            raise RuntimeError(f"Không gửi được Telegram: mã {ex.code}")
        log(f"Đã gửi Telegram phần {idx}/{len(chunks)}")
        time.sleep(1)

# ----------------------------------------------------------------------
def main():
    missing = [n for n, v in [("TELEGRAM_TOKEN_QUYDINH", TELEGRAM_TOKEN),
                              ("TELEGRAM_CHAT_ID", TELEGRAM_CHAT_ID)] if not v]
    if missing:
        log(f"THIẾU biến môi trường: {', '.join(missing)}")
        sys.exit(1)

    if da_gui_hom_nay():
        return

    seen = load_seen()
    items, nguon_ok, nguon_loi = collect()

    # Thứ Hai: gửi tổng kết tuần trước, để biết hệ thống vẫn sống
    if datetime.now(VN_TZ).weekday() == 0:
        send_telegram(build_weekly(seen))

    # Không lấy được gì = SỰ CỐ, phải nói rõ là sự cố.
    if not items:
        log("Không lấy được mục nào từ mọi nguồn.")
        send_telegram(build_su_co(items, len(nguon_ok), nguon_loi))
        ghi_dau_ngay()
        return

    fresh, stats = filter_items(items, seen)
    n_vanban = sum(1 for i in fresh if i["kind"] == "vanban")

    # Không có văn bản pháp quy mới -> vẫn BÁO, kèm số liệu.
    # Bot này tồn tại để báo VĂN BẢN. Nếu chỉ có tin ngành thì không được
    # gửi dưới tiêu đề "VĂN BẢN, QUY ĐỊNH MỚI" - sẽ sai bản chất.
    if n_vanban == 0:
        if not nguon_ok:
            send_telegram(build_su_co(items, len(nguon_ok), nguon_loi))
            ghi_dau_ngay()
            return
        ly_do = ("Không có văn bản pháp luật mới nào chưa từng gửi."
                 if not fresh else
                 f"Không có văn bản pháp luật mới. "
                 f"(Có {len(fresh)} tin ngành nhưng không phải văn bản pháp quy.)")
        log(f"{ly_do} -> gửi thông báo trống.")
        send_telegram(build_trong(items, stats, seen, len(nguon_ok), ly_do))
        if fresh:
            save_seen(seen, fresh)
        ghi_dau_ngay()
        return

    send_telegram(build_message(fresh))
    save_seen(seen, fresh)   # ghi nhớ cả mục chưa liệt kê, tránh lặp vô hạn
    ghi_dau_ngay()
    log("Xong.")

if __name__ == "__main__":
    main()
