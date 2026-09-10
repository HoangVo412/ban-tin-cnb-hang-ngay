#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
kiem_tra_nguon.py — Đo sức khỏe từng nguồn RSS trước khi tin vào nó.

Chạy:  python kiem_tra_nguon.py
Yêu cầu: pip install feedparser

In ra bảng: mỗi nguồn -> số mục, ngày bài mới nhất, tuổi bài mới nhất,
số mục lọt cửa sổ 30h, số mục KHÔNG có ngày.
Nguồn nào có "bài mới nhất" cách > 4 ngày = nguồn CHẾT, phải thay.
"""

import calendar
import socket
from datetime import datetime, timedelta, timezone

import feedparser

socket.setdefaulttimeout(25)

VN = timezone(timedelta(hours=7))
MAX_AGE_HOURS = 30      # cửa sổ tin thời sự
DEAD_DAYS = 4           # ngưỡng coi nguồn là chết

# ---------------------------------------------------------------------------
# Dán đúng danh sách nguồn đang dùng trong feeds_*.py vào đây.
# Danh sách dưới đây gồm 11 nguồn NLĐ đã xác nhận ĐỨNG YÊN từ 30/06/2026
# + vài nguồn sống để đối chứng + vài nguồn ứng viên thay thế [??].
# ---------------------------------------------------------------------------
FEEDS = {
    # --- NLĐ trên tuoitre.vn: ĐÃ KIỂM CHỨNG 09/09/2026 là đứng yên từ 30/06 ---
    "NLĐ - Lao động":              "https://tuoitre.vn/nld/rss/lao-dong.rss",
    "NLĐ - LĐ/Chính sách":         "https://tuoitre.vn/nld/rss/nld/lao-dong/chinh-sach.rss",
    "NLĐ - LĐ/An sinh xã hội":     "https://tuoitre.vn/nld/rss/nld/lao-dong/an-sinh-xa-hoi.rss",
    "NLĐ - LĐ/Việc làm":           "https://tuoitre.vn/nld/rss/nld/lao-dong/viec-lam.rss",
    "NLĐ - LĐ/Công đoàn":          "https://tuoitre.vn/nld/rss/nld/lao-dong/cong-doan-cong-nhan.rss",
    "NLĐ - LĐ/Xuất khẩu LĐ":       "https://tuoitre.vn/nld/rss/nld/lao-dong/xuat-khau-lao-dong.rss",
    "NLĐ - Kinh tế":               "https://tuoitre.vn/nld/rss/kinh-te.rss",
    "NLĐ - Tài chính/CK":          "https://tuoitre.vn/nld/rss/nld/kinh-te/tai-chinh-chung-khoan.rss",
    "NLĐ - Đồng tiền thông minh":  "https://tuoitre.vn/nld/rss/dong-tien-thong-minh.rss",
    "NLĐ - AI 365":                "https://tuoitre.vn/nld/rss/ai-365.rss",
    "NLĐ - AI 365/Công nghệ số":   "https://tuoitre.vn/nld/rss/nld/ai-365/cong-nghe-so.rss",

    # --- Đối chứng: nguồn đang sống ---
    "Tuổi Trẻ - Kinh doanh":       "https://tuoitre.vn/rss/kinh-doanh.rss",
    "Tuổi Trẻ - Pháp luật":        "https://tuoitre.vn/rss/phap-luat.rss",

    # --- Ứng viên thay thế: [??] CHƯA KIỂM CHỨNG, xem kết quả rồi giữ/bỏ ---
    "Lao Động - Công đoàn [??]":   "https://laodong.vn/rss/cong-doan.rss",
    "Lao Động - Xã hội [??]":      "https://laodong.vn/rss/xa-hoi.rss",
    "Lao Động - Kinh doanh [??]":  "https://laodong.vn/rss/kinh-doanh.rss",
    "Dân Trí - Việc làm [??]":     "https://dantri.com.vn/viec-lam.rss",
    "Dân Trí - An sinh [??]":      "https://dantri.com.vn/an-sinh.rss",
    "VnExpress - Kinh doanh":      "https://vnexpress.net/rss/kinh-doanh.rss",
    "Báo Chính phủ - Chính sách [??]": "https://baochinhphu.vn/rss/chinh-sach-moi.rss",
}


def parse_dt(entry):
    """feedparser trả struct_time theo UTC -> phải dùng calendar.timegm.
    Dùng time.mktime là SAI (mktime hiểu struct_time là giờ local)."""
    for key in ("published_parsed", "updated_parsed", "created_parsed"):
        st = entry.get(key)
        if st:
            try:
                return datetime.fromtimestamp(calendar.timegm(st), tz=timezone.utc)
            except Exception:
                continue
    return None


def main():
    now = datetime.now(timezone.utc)
    print(f"Giờ chạy: {now.astimezone(VN):%d/%m/%Y %H:%M} (VN)")
    print(f"Cửa sổ tin: {MAX_AGE_HOURS}h | Ngưỡng chết: {DEAD_DAYS} ngày\n")

    header = f"{'NGUỒN':<32}{'MỤC':>5}{'MỚI NHẤT':>16}{'TUỔI':>9}{'<30h':>6}{'KHÔNG NGÀY':>12}  TRẠNG THÁI"
    print(header)
    print("-" * len(header))

    chet, khong_lay_duoc = [], []

    for ten, url in FEEDS.items():
        try:
            d = feedparser.parse(url)
            entries = d.entries or []
        except Exception as e:
            print(f"{ten:<32}{'LỖI':>5}   {type(e).__name__}")
            khong_lay_duoc.append(ten)
            continue

        if not entries:
            print(f"{ten:<32}{0:>5}{'-':>16}{'-':>9}{'-':>6}{'-':>12}  FEED RỖNG")
            khong_lay_duoc.append(ten)
            continue

        dates = [dt for dt in (parse_dt(e) for e in entries) if dt]
        khong_ngay = len(entries) - len(dates)

        if not dates:
            print(f"{ten:<32}{len(entries):>5}{'-':>16}{'-':>9}{'-':>6}{khong_ngay:>12}  KHÔNG CÓ NGÀY")
            chet.append(ten)
            continue

        moi_nhat = max(dates)
        tuoi_ngay = (now - moi_nhat).total_seconds() / 86400
        trong_cua_so = sum(1 for dt in dates
                           if timedelta(0) <= (now - dt) <= timedelta(hours=MAX_AGE_HOURS))
        song = tuoi_ngay <= DEAD_DAYS
        if not song:
            chet.append(ten)

        print(f"{ten:<32}{len(entries):>5}"
              f"{moi_nhat.astimezone(VN):%d/%m %H:%M}"
              f"{tuoi_ngay:>8.1f}d{trong_cua_so:>6}{khong_ngay:>12}"
              f"  {'ok' if song else '*** CHẾT ***'}")

    print()
    if chet:
        print("=== NGUỒN CHẾT / ĐỨNG YÊN — PHẢI THAY ===")
        for t in chet:
            print(f"  - {t}")
    if khong_lay_duoc:
        print("=== NGUỒN KHÔNG LẤY ĐƯỢC ===")
        for t in khong_lay_duoc:
            print(f"  - {t}")
    if not chet and not khong_lay_duoc:
        print("Tất cả nguồn đều sống.")


if __name__ == "__main__":
    main()
