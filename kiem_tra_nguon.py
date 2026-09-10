# -*- coding: utf-8 -*-
"""
kiem_tra_nguon.py - Đo sức khỏe từng nguồn RSS.  (bản 2, 10/09/2026)

Chạy:
    python kiem_tra_nguon.py            # kiểm tra các nguồn trong feeds.py
    python kiem_tra_nguon.py ungvien    # kiểm tra thêm nhóm nguồn ứng viên

Bản 2 sửa lỗi của bản 1: phải vá múi giờ dạng "+07" trước khi parse, nếu
không mọi feed của tuoitre.vn đều bị báo nhầm là "không có ngày".

Cột đọc thế nào:
    MỚI NHẤT    ngày bài mới nhất trong feed
    TUỔI        bài mới nhất cách bao lâu. > 4 ngày = NGUỒN CHẾT, phải thay.
    <26h        số mục lọt cửa sổ bản tin
    K.NGÀY      số mục không đọc được ngày. Khác 0 = feed sai định dạng.
"""

import re
import sys
import calendar
import urllib.request
from datetime import datetime, timedelta, timezone
from concurrent.futures import ThreadPoolExecutor

import feedparser

VN = timezone(timedelta(hours=7))
MAX_AGE_HOURS = 26
DEAD_DAYS = 4
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/125.0 Safari/537.36")

# "26 Jun 2026 03:08:00 +07"  ->  "... +0700"
_RE_TZ_SHORT = re.compile(rb"(\d{2}:\d{2}:\d{2}\s*[+-]\d{2})(\s*<)")


def fix_short_tz(raw):
    return _RE_TZ_SHORT.sub(rb"\g<1>00\g<2>", raw)


# Nguồn ứng viên thay cho 11 kênh NLĐ đã chết.
# [??] = SUY TỪ QUY LUẬT URL, CHƯA KIỂM CHỨNG. Chạy script rồi giữ cái nào sống.
UNG_VIEN = {
    "https://laodong.vn/rss/cong-doan.rss":            "Lao Động - Công đoàn [??]",
    "https://laodong.vn/rss/xa-hoi.rss":               "Lao Động - Xã hội [??]",
    "https://laodong.vn/rss/thoi-su.rss":              "Lao Động - Thời sự [??]",
    "https://laodong.vn/rss/kinh-doanh.rss":           "Lao Động - Kinh doanh [??]",
    "https://laodong.vn/rss/cong-nghe.rss":            "Lao Động - Công nghệ [??]",
    "https://dantri.com.vn/rss/lao-dong-viec-lam.rss": "Dân Trí - LĐ Việc làm [??]",
    "https://dantri.com.vn/rss/an-sinh.rss":           "Dân Trí - An sinh [??]",
    "https://dantri.com.vn/rss/phap-luat.rss":         "Dân Trí - Pháp luật [??]",
    "https://vietnamnet.vn/rss/kinh-doanh.rss":        "VietnamNet - Kinh doanh [??]",
    "https://vietnamnet.vn/rss/thoi-su.rss":           "VietnamNet - Thời sự [??]",
    "https://baochinhphu.vn/rss/chinh-sach-moi.rss":   "Báo CP - Chính sách [??]",
    "https://baochinhphu.vn/rss/kinh-te.rss":          "Báo CP - Kinh tế [??]",
    "https://thanhnien.vn/rss/doi-song.rss":           "Thanh Niên - Đời sống [??]",
    "https://cafef.vn/thi-truong-chung-khoan.rss":     "CafeF - Chứng khoán [??]",
}


def do_mot_nguon(pair):
    url, ten = pair
    now = datetime.now(timezone.utc)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read()
    except Exception as ex:
        return (ten, None, f"KHÔNG TẢI ĐƯỢC: {type(ex).__name__} - {str(ex)[:60]}")

    parsed = feedparser.parse(fix_short_tz(raw))
    entries = parsed.entries or []
    if not entries:
        return (ten, None, "FEED RỖNG")

    dates, khong_ngay = [], 0
    for e in entries:
        st = e.get("published_parsed") or e.get("updated_parsed")
        if st:
            dates.append(datetime.fromtimestamp(calendar.timegm(st),
                                                tz=timezone.utc))
        else:
            khong_ngay += 1

    if not dates:
        return (ten, None, f"{len(entries)} mục, KHÔNG mục nào đọc được ngày")

    moi = max(dates)
    tuoi = (now - moi).total_seconds() / 86400
    trong_cua_so = sum(
        1 for d in dates
        if timedelta(0) <= (now - d) <= timedelta(hours=MAX_AGE_HOURS))
    return (ten, {
        "so_muc": len(entries),
        "moi_nhat": moi,
        "tuoi": tuoi,
        "trong_cua_so": trong_cua_so,
        "khong_ngay": khong_ngay,
        "song": tuoi <= DEAD_DAYS,
    }, None)


def main():
    from feeds import FEEDS
    danh_sach = dict(FEEDS)
    if len(sys.argv) > 1 and sys.argv[1].lower().startswith("ungvien"):
        danh_sach.update(UNG_VIEN)

    now = datetime.now(timezone.utc)
    print(f"Giờ chạy : {now.astimezone(VN):%d/%m/%Y %H:%M} (VN)")
    print(f"Cửa sổ   : {MAX_AGE_HOURS}h   |   Ngưỡng nguồn chết: {DEAD_DAYS} ngày")
    print(f"Số nguồn : {len(danh_sach)}\n")

    head = (f"{'NGUỒN':<34}{'MỤC':>5}{'MỚI NHẤT':>15}{'TUỔI':>9}"
            f"{'<26h':>6}{'K.NGÀY':>8}  TRẠNG THÁI")
    print(head)
    print("-" * len(head))

    with ThreadPoolExecutor(max_workers=8) as pool:
        ket_qua = list(pool.map(do_mot_nguon, danh_sach.items()))

    chet, hong = [], []
    for ten, r, loi in sorted(ket_qua, key=lambda x: x[0]):
        if loi:
            print(f"{ten:<34}{'-':>5}{'-':>15}{'-':>9}{'-':>6}{'-':>8}  {loi}")
            hong.append(ten)
            continue
        trang_thai = "ok" if r["song"] else "*** CHẾT ***"
        if not r["song"]:
            chet.append(f"{ten}  (mới nhất {r['moi_nhat'].astimezone(VN):%d/%m/%Y})")
        if r["khong_ngay"]:
            trang_thai += "  <- có mục sai định dạng ngày"
        print(f"{ten:<34}{r['so_muc']:>5}"
              f"{r['moi_nhat'].astimezone(VN):%d/%m %H:%M}"
              f"{r['tuoi']:>8.1f}d{r['trong_cua_so']:>6}{r['khong_ngay']:>8}"
              f"  {trang_thai}")

    print()
    if chet:
        print("=== NGUỒN CHẾT / ĐỨNG YÊN - PHẢI THAY ===")
        for t in chet:
            print(f"  - {t}")
        print()
    if hong:
        print("=== NGUỒN KHÔNG TẢI ĐƯỢC ===")
        for t in hong:
            print(f"  - {t}")
        print()
    if not chet and not hong:
        print("Tất cả nguồn đều sống.")


if __name__ == "__main__":
    main()
