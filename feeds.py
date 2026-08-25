# -*- coding: utf-8 -*-
"""
Danh sách nguồn RSS.
Feed nào hỏng sẽ tự động bị bỏ qua, không làm chết script.
Điều khoản: các báo cung cấp RSS miễn phí cho cá nhân / phi lợi nhuận.
"""

FEEDS = {
    # ---------- VnExpress (đã kiểm chứng, chạy tốt) ----------
    "https://vnexpress.net/rss/tin-noi-bat.rss":        "VnExpress - Nổi bật",
    "https://vnexpress.net/rss/thoi-su.rss":            "VnExpress - Thời sự",
    "https://vnexpress.net/rss/kinh-doanh.rss":         "VnExpress - Kinh doanh",
    "https://vnexpress.net/rss/phap-luat.rss":          "VnExpress - Pháp luật",
    "https://vnexpress.net/rss/the-gioi.rss":           "VnExpress - Thế giới",
    "https://vnexpress.net/rss/khoa-hoc-cong-nghe.rss": "VnExpress - Khoa học CN",
    "https://vnexpress.net/rss/giao-duc.rss":           "VnExpress - Giáo dục",
    "https://vnexpress.net/rss/suc-khoe.rss":           "VnExpress - Sức khỏe",

    # ---------- Tuổi Trẻ (đã kiểm chứng, chạy tốt) ----------
    "https://tuoitre.vn/thoi-su.rss":       "Tuổi Trẻ - Thời sự",
    "https://tuoitre.vn/kinh-doanh.rss":    "Tuổi Trẻ - Kinh doanh",
    "https://tuoitre.vn/phap-luat.rss":     "Tuổi Trẻ - Pháp luật",
    "https://tuoitre.vn/nhip-song-so.rss":  "Tuổi Trẻ - Công nghệ",
    "https://tuoitre.vn/the-gioi.rss":      "Tuổi Trẻ - Thế giới",

    # ---------- Thanh Niên / Dân Trí (đã kiểm chứng, chạy tốt) ----------
    "https://thanhnien.vn/rss/thoi-su.rss":     "Thanh Niên - Thời sự",
    "https://thanhnien.vn/rss/kinh-te.rss":     "Thanh Niên - Kinh tế",
    "https://dantri.com.vn/rss/xa-hoi.rss":     "Dân Trí - Xã hội",
    "https://dantri.com.vn/rss/kinh-doanh.rss": "Dân Trí - Kinh doanh",

    # ---------- Người Lao Động — MẢNG LAO ĐỘNG (nguồn quan trọng nhất) ----------
    # NLĐ đã chuyển hệ thống sang tên miền tuoitre.vn/nld/.
    # Các URL dưới lấy từ trang RSS chính thức của NLĐ.
    "https://tuoitre.vn/nld/rss/lao-dong.rss":
        "NLĐ - Lao động",
    "https://tuoitre.vn/nld/rss/nld/lao-dong/chinh-sach.rss":
        "NLĐ - Lao động/Chính sách",
    "https://tuoitre.vn/nld/rss/nld/lao-dong/an-sinh-xa-hoi.rss":
        "NLĐ - Lao động/An sinh xã hội",
    "https://tuoitre.vn/nld/rss/nld/lao-dong/cong-doan-cong-nhan.rss":
        "NLĐ - Lao động/Công đoàn",
    "https://tuoitre.vn/nld/rss/nld/lao-dong/viec-lam.rss":
        "NLĐ - Lao động/Việc làm",
    "https://tuoitre.vn/nld/rss/kinh-te.rss":
        "NLĐ - Kinh tế",

    # ---------- ĐÃ GỠ ----------
    # Báo Chính phủ (baochinhphu.vn/rss/home.rss, /chinh-sach-moi.rss): trả 404.
    #   Chưa xác định được URL đúng. Nếu cần, tự tìm mục RSS trên baochinhphu.vn.
    # VietnamPlus (vietnamplus.vn/rss/kinhte.rss): trả về feed rỗng.
    #   Trang chỉ mục RSS của họ là vietnamplus.vn/rss.vnp
    # nld.com.vn/rss/cong-doan.rss: 404 (đã thay bằng URL mới ở trên).
}

# Từ khóa để đánh dấu tin thuộc mảng nghiệp vụ C&B.
# Tin trúng từ khóa được gắn cờ [*] khi gửi cho AI, để không bị bỏ sót.
KEYWORDS_CB = [
    "lao động", "tiền lương", "tiền công", "lương tối thiểu", "lương hưu",
    "bảo hiểm xã hội", "bhxh", "bảo hiểm y tế", "bhyt", "thất nghiệp", "bhtn",
    "thuế thu nhập cá nhân", "thuế tncn", "giảm trừ gia cảnh", "quyết toán thuế",
    "hợp đồng lao động", "công đoàn", "nghỉ hưu", "biên chế", "công chức",
    "viên chức", "tinh giản", "trợ cấp", "phụ cấp", "làm thêm giờ", "nghỉ lễ",
    "bộ luật lao động", "nghị định", "thông tư", "an toàn lao động",
    "tuyển dụng", "sa thải", "việc làm", "nhân sự", "evn", "điện lực",
    "an sinh xã hội", "xuất khẩu lao động",
]
