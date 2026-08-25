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
    "https://vneconomy.vn/rss/tai-chinh.rss":           "VnEconomy - Tài chính",      # [??]
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

# ----------------------------------------------------------------------
# Từ khóa phân loại. Tin trúng từ khóa sẽ được cấp "suất" riêng khi gửi
# cho AI, tránh bị tin thời sự dồn dập đẩy văng khỏi danh sách.
# ----------------------------------------------------------------------

KEYWORDS_CB = [
    "lao động", "tiền lương", "tiền công", "lương tối thiểu", "lương hưu",
    "bảo hiểm xã hội", "bhxh", "bảo hiểm y tế", "bhyt", "thất nghiệp", "bhtn",
    "thuế thu nhập cá nhân", "thuế tncn", "giảm trừ gia cảnh", "quyết toán thuế",
    "hợp đồng lao động", "công đoàn", "nghỉ hưu", "biên chế", "công chức",
    "viên chức", "tinh giản", "trợ cấp", "phụ cấp", "làm thêm giờ", "nghỉ lễ",
    "bộ luật lao động", "nghị định", "thông tư", "an toàn lao động",
    "tuyển dụng", "sa thải", "việc làm", "nhân sự", "evn", "điện lực",
    "an sinh xã hội", "xuất khẩu lao động",
    # tiếng Anh (cho các feed quốc tế)
    "hr ", "human resources", "payroll", "workforce", "employee", "hiring",
    "layoff", "recruit", "labor", "labour", "compensation", "benefits",
]

KEYWORDS_TECH = [
    # công nghệ & AI
    "ai", "trí tuệ nhân tạo", "chatgpt", "gemini", "claude", "openai",
    "anthropic", "google", "microsoft", "copilot", "chuyển đổi số",
    "tự động hóa", "phần mềm", "dữ liệu", "big data", "machine learning",
    "công nghệ", "số hóa", "chip", "bán dẫn", "an ninh mạng", "bảo mật",
    "excel", "power bi", "automation", "artificial intelligence", "llm",
    "agent", "model", "startup", "cloud",
    # tài chính
    "tài chính", "chứng khoán", "ngân hàng", "lãi suất", "tỷ giá", "vn-index",
    "trái phiếu", "cổ phiếu", "vàng", "lạm phát", "tín dụng", "đầu tư",
    "gdp", "thuế", "ngân sách", "fed", "usd",
]
