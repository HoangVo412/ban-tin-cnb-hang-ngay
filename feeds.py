# -*- coding: utf-8 -*-
"""
Danh sách nguồn RSS.
Thêm/bớt tự do. Feed nào hỏng sẽ tự động bị bỏ qua, không làm chết script.
Điều khoản: các báo cung cấp RSS miễn phí cho cá nhân / phi lợi nhuận.
"""

FEEDS = {
    # ---------- VnExpress ----------
    "https://vnexpress.net/rss/tin-noi-bat.rss":        "VnExpress - Nổi bật",
    "https://vnexpress.net/rss/thoi-su.rss":            "VnExpress - Thời sự",
    "https://vnexpress.net/rss/kinh-doanh.rss":         "VnExpress - Kinh doanh",
    "https://vnexpress.net/rss/phap-luat.rss":          "VnExpress - Pháp luật",
    "https://vnexpress.net/rss/the-gioi.rss":           "VnExpress - Thế giới",
    "https://vnexpress.net/rss/khoa-hoc-cong-nghe.rss": "VnExpress - Khoa học CN",
    "https://vnexpress.net/rss/giao-duc.rss":           "VnExpress - Giáo dục",
    "https://vnexpress.net/rss/suc-khoe.rss":           "VnExpress - Sức khỏe",

    # ---------- Tuổi Trẻ ----------
    "https://tuoitre.vn/thoi-su.rss":       "Tuổi Trẻ - Thời sự",
    "https://tuoitre.vn/kinh-doanh.rss":    "Tuổi Trẻ - Kinh doanh",
    "https://tuoitre.vn/phap-luat.rss":     "Tuổi Trẻ - Pháp luật",
    "https://tuoitre.vn/nhip-song-so.rss":  "Tuổi Trẻ - Công nghệ",
    "https://tuoitre.vn/the-gioi.rss":      "Tuổi Trẻ - Thế giới",
    "https://tuoitre.vn/ban-doc.rss":       "Tuổi Trẻ - Bạn đọc",

    # ---------- Nguồn bổ sung ----------
    # Các URL dưới đây CHƯA được kiểm chứng từng cái một.
    # Script tự bỏ qua feed lỗi; anh chạy thử rồi xem log để giữ lại cái nào chạy được.
    "https://nld.com.vn/rss/cong-doan.rss":     "Người Lao Động - Công đoàn",
    "https://nld.com.vn/rss/kinh-te.rss":       "Người Lao Động - Kinh tế",
    "https://thanhnien.vn/rss/thoi-su.rss":     "Thanh Niên - Thời sự",
    "https://thanhnien.vn/rss/kinh-te.rss":     "Thanh Niên - Kinh tế",
    "https://dantri.com.vn/rss/xa-hoi.rss":     "Dân Trí - Xã hội",
    "https://dantri.com.vn/rss/kinh-doanh.rss": "Dân Trí - Kinh doanh",
    "https://baochinhphu.vn/rss/chinh-sach-moi.rss": "Báo Chính phủ - Chính sách mới",
    "https://baochinhphu.vn/rss/home.rss":      "Báo Chính phủ - Trang chủ",
    "https://www.vietnamplus.vn/rss/kinhte.rss": "VietnamPlus - Kinh tế",
}

# Từ khóa để đánh dấu tin thuộc mảng nghiệp vụ C&B.
# Tin nào trúng từ khóa sẽ được gắn cờ [*] khi gửi cho AI, để AI ưu tiên đưa vào
# phần chuyên đề thay vì bỏ sót giữa hàng trăm tin khác.
KEYWORDS_CB = [
    "lao động", "tiền lương", "tiền công", "lương tối thiểu", "lương hưu",
    "bảo hiểm xã hội", "bhxh", "bảo hiểm y tế", "bhyt", "thất nghiệp", "bhtn",
    "thuế thu nhập cá nhân", "thuế tncn", "giảm trừ gia cảnh", "quyết toán thuế",
    "hợp đồng lao động", "công đoàn", "nghỉ hưu", "biên chế", "công chức",
    "viên chức", "tinh giản", "trợ cấp", "phụ cấp", "làm thêm giờ", "nghỉ lễ",
    "bộ luật lao động", "nghị định", "thông tư", "an toàn lao động",
    "tuyển dụng", "sa thải", "việc làm", "nhân sự", "evn", "điện lực",
]
