# -*- coding: utf-8 -*-
"""
Danh sách nguồn RSS.
Feed nào hỏng sẽ tự động bị bỏ qua và ghi vào log, không làm chết script.
Điều khoản: các báo cung cấp RSS miễn phí cho cá nhân / phi lợi nhuận.

Ghi chú độ tin cậy:
  [OK]  = đã chạy thành công trong log thực tế
  [CT]  = lấy từ trang RSS chính thức của báo, chưa chạy thực tế
  [??]  = suy từ quy luật URL, CHƯA kiểm chứng - xem log để giữ hay bỏ
"""

FEEDS = {
    # ================= THỜI SỰ - TỔNG HỢP =================
    "https://vnexpress.net/rss/tin-noi-bat.rss":        "VnExpress - Nổi bật",        # [OK]
    "https://vnexpress.net/rss/thoi-su.rss":            "VnExpress - Thời sự",        # [OK]
    "https://vnexpress.net/rss/phap-luat.rss":          "VnExpress - Pháp luật",      # [OK]
    "https://vnexpress.net/rss/the-gioi.rss":           "VnExpress - Thế giới",       # [OK]
    "https://vnexpress.net/rss/giao-duc.rss":           "VnExpress - Giáo dục",       # [OK]
    "https://vnexpress.net/rss/suc-khoe.rss":           "VnExpress - Sức khỏe",       # [OK]
    "https://tuoitre.vn/thoi-su.rss":                   "Tuổi Trẻ - Thời sự",         # [OK]
    "https://tuoitre.vn/phap-luat.rss":                 "Tuổi Trẻ - Pháp luật",       # [OK]
    "https://tuoitre.vn/the-gioi.rss":                  "Tuổi Trẻ - Thế giới",        # [OK]
    "https://thanhnien.vn/rss/thoi-su.rss":             "Thanh Niên - Thời sự",       # [OK]
    "https://dantri.com.vn/rss/xa-hoi.rss":             "Dân Trí - Xã hội",           # [OK]

    # ================= LAO ĐỘNG - TIỀN LƯƠNG - BHXH - THUẾ =================
    # Nguồn quan trọng nhất với nghiệp vụ C&B.
    "https://tuoitre.vn/nld/rss/lao-dong.rss":
        "NLĐ - Lao động",                                                             # [CT]
    "https://tuoitre.vn/nld/rss/nld/lao-dong/chinh-sach.rss":
        "NLĐ - Lao động/Chính sách",                                                  # [CT]
    "https://tuoitre.vn/nld/rss/nld/lao-dong/an-sinh-xa-hoi.rss":
        "NLĐ - Lao động/An sinh xã hội",                                              # [CT]
    "https://tuoitre.vn/nld/rss/nld/lao-dong/cong-doan-cong-nhan.rss":
        "NLĐ - Lao động/Công đoàn",                                                   # [CT]
    "https://tuoitre.vn/nld/rss/nld/lao-dong/viec-lam.rss":
        "NLĐ - Lao động/Việc làm",                                                    # [CT]
    "https://tuoitre.vn/nld/rss/nld/lao-dong/xuat-khau-lao-dong.rss":
        "NLĐ - Lao động/Xuất khẩu LĐ",                                                # [CT]

    # ================= TÀI CHÍNH - KINH TẾ =================
    "https://vnexpress.net/rss/kinh-doanh.rss":         "VnExpress - Kinh doanh",     # [OK]
    "https://tuoitre.vn/kinh-doanh.rss":                "Tuổi Trẻ - Kinh doanh",      # [OK]
    "https://thanhnien.vn/rss/kinh-te.rss":             "Thanh Niên - Kinh tế",       # [OK]
    "https://dantri.com.vn/rss/kinh-doanh.rss":         "Dân Trí - Kinh doanh",       # [OK]
    "https://tuoitre.vn/nld/rss/kinh-te.rss":           "NLĐ - Kinh tế",              # [OK]
    "https://tuoitre.vn/nld/rss/nld/kinh-te/tai-chinh-chung-khoan.rss":
        "NLĐ - Tài chính/Chứng khoán",                                                # [CT]
    "https://tuoitre.vn/nld/rss/dong-tien-thong-minh.rss":
        "NLĐ - Đồng tiền thông minh",                                                 # [CT]
    "https://cafef.vn/tai-chinh-ngan-hang.rss":         "CafeF - Tài chính NH",       # [??]
    "https://cafef.vn/vi-mo-dau-tu.rss":                "CafeF - Vĩ mô",              # [??]

    # ================= CÔNG NGHỆ - AI =================
    "https://vnexpress.net/rss/khoa-hoc-cong-nghe.rss": "VnExpress - Khoa học CN",    # [OK]
    "https://tuoitre.vn/nhip-song-so.rss":              "Tuổi Trẻ - Công nghệ",       # [OK]
    "https://tuoitre.vn/khoa-hoc.rss":                  "Tuổi Trẻ - Khoa học",        # [CT]
    "https://tuoitre.vn/nld/rss/ai-365.rss":
        "NLĐ - AI 365",                                                               # [CT]
    "https://tuoitre.vn/nld/rss/nld/ai-365/cong-nghe-so.rss":
        "NLĐ - AI 365/Công nghệ số",                                                  # [CT]
    "https://thanhnien.vn/rss/cong-nghe.rss":           "Thanh Niên - Công nghệ",     # [??]
    "https://dantri.com.vn/rss/suc-manh-so.rss":        "Dân Trí - Sức mạnh số",      # [??]
    "https://genk.vn/rss/home.rss":                     "GenK - Công nghệ",           # [??]

    # ================= AI QUỐC TẾ (nguồn tiếng Anh) =================
    # AI trong HR gần như không có báo Việt nào theo dõi thường xuyên.
    # Các feed dưới là tiếng Anh; AI sẽ tóm tắt lại bằng tiếng Việt.
    "https://techcrunch.com/category/artificial-intelligence/feed/":
        "TechCrunch - AI",                                                            # [??]
    "https://venturebeat.com/category/ai/feed/":
        "VentureBeat - AI",                                                           # [??]
    "https://www.hrdive.com/feeds/news/":
        "HR Dive - Nhân sự quốc tế",                                                  # [??]
}

# ======================================================================
# TỪ KHÓA PHÂN LOẠI - CÓ CHẤM ĐIỂM
# ======================================================================
# So khớp theo RANH GIỚI TỪ, không phải chuỗi con.
# Lý do: từ khóa "ai" nếu khớp chuỗi con sẽ dính vào hai, tai, thai, khai,
# trai, mai, sai... tức gần như mọi tin tiếng Việt.
#
# Tin phải đạt tối thiểu SCORE_THRESHOLD điểm mới được gắn cờ.
#   từ mạnh  = 3 điểm   (đặc thù, gần như không thể nhầm)
#   từ yếu   = 1 điểm   (phổ thông, cần cộng dồn mới đủ tin cậy)
#   nguồn    = xem SOURCE_BOOST bên dưới

SCORE_THRESHOLD = 3

# ---------------------- LAO ĐỘNG - TIỀN LƯƠNG - BHXH - THUẾ ----------------------
STRONG_CB = [
    "tiền lương", "tiền công", "lương tối thiểu", "lương hưu", "lương cơ sở",
    "bảo hiểm xã hội", "bhxh", "bảo hiểm y tế", "bhyt", "bảo hiểm thất nghiệp",
    "bhtn", "trợ cấp thất nghiệp", "thuế thu nhập cá nhân", "thuế tncn",
    "giảm trừ gia cảnh", "quyết toán thuế", "hợp đồng lao động", "bộ luật lao động",
    "an toàn lao động", "làm thêm giờ", "tăng ca", "nghỉ hưu", "tuổi nghỉ hưu",
    "xuất khẩu lao động", "công đoàn", "người lao động", "an sinh xã hội",
    "thang bảng lương", "nâng bậc lương", "phụ cấp", "thưởng tết", "lương thưởng",
    "tinh giản biên chế", "định biên", "sa thải", "thất nghiệp",
    "thai sản", "chế độ thai sản", "ốm đau", "tai nạn lao động", "bệnh nghề nghiệp",
    "nghỉ phép", "phép năm", "chấm công", "định mức lao động", "năng suất lao động",
    "thỏa ước lao động", "nội quy lao động", "kỷ luật lao động", "đình công",
    "quan hệ lao động", "tiền lương tối thiểu", "thu nhập bình quân",
    # tiếng Anh
    "payroll", "human resources", "compensation and benefits", "labor law",
    "minimum wage", "workforce", "layoff", "severance", "employee benefits",
]
WEAK_CB = [
    "lao động", "việc làm", "nhân sự", "tuyển dụng", "nghị định", "thông tư",
    "công chức", "viên chức", "biên chế", "trợ cấp", "nghỉ lễ", "chế độ",
    "lương", "bảo hiểm", "thuế", "evn", "điện lực", "doanh nghiệp nhà nước",
    "hiring", "recruit", "employee", "hr", "labour",
]

# ---------------------- TÀI CHÍNH - CÔNG NGHỆ - AI ----------------------
STRONG_TECH = [
    "trí tuệ nhân tạo", "chatgpt", "gemini", "claude", "openai", "anthropic",
    "copilot", "chuyển đổi số", "tự động hóa", "machine learning", "deep learning",
    "an ninh mạng", "bảo mật", "power bi", "power automate", "power query",
    "artificial intelligence", "generative ai", "llm", "automation",
    "chứng khoán", "vn-index", "lãi suất", "tỷ giá", "trái phiếu", "cổ phiếu",
    "lạm phát", "tín dụng", "ngân hàng nhà nước", "giá vàng", "thuế quan",
    # viết tắt / tên riêng - dùng ranh giới từ nên an toàn
    "ai", "gdp", "fed", "usd", "api",
]
WEAK_TECH = [
    "công nghệ", "phần mềm", "dữ liệu", "số hóa", "chip", "bán dẫn", "excel",
    "startup", "đầu tư", "tài chính", "ngân hàng", "ngân sách", "vàng",
    "google", "microsoft", "apple", "meta", "nvidia", "samsung",
    "model", "agent", "cloud", "data", "software", "chatbot",
]

# ---------------------- ƯU TIÊN THEO NGUỒN ----------------------
# Nguồn chuyên đề là tín hiệu đáng tin hơn mọi từ khóa: một bài nằm trong
# chuyên mục "Lao động/Chính sách" thì gần như chắc chắn thuộc mảng C&B,
# kể cả khi tiêu đề không chứa từ khóa nào.
SOURCE_BOOST_CB = {
    "NLĐ - Lao động": 6,
    "HR Dive": 5,
}
SOURCE_BOOST_TECH = {
    "NLĐ - AI 365": 6,
    "TechCrunch - AI": 6,
    "VentureBeat - AI": 6,
    "GenK": 4,
    "CafeF": 4,
    "NLĐ - Tài chính": 4,
    "NLĐ - Đồng tiền": 4,
    "Dân Trí - Sức mạnh số": 4,
    "Thanh Niên - Công nghệ": 3,
    "Tuổi Trẻ - Công nghệ": 3,
    "VnExpress - Khoa học CN": 3,
}
