# -*- coding: utf-8 -*-
"""
Danh sách nguồn RSS cho bản tin C&B.

CẬP NHẬT 10/09/2026 - căn cứ kết quả đo thật của kiem_tra_nguon.py:
  - GỠ 11 kênh NLĐ trên tuoitre.vn: feed vẫn trả 50 mục và vẫn cập nhật
    lastBuildDate mỗi ngày, nhưng bài mới nhất dừng ở 28-30/06/2026.
    Đã kiểm tra cả tên miền cũ nld.com.vn -> chuyển hướng về đúng nội dung
    chết đó. Không khôi phục được, phải thay nguồn khác.
  - GỠ Dân Trí Xã hội (mới nhất 14/05/2026) và Dân Trí Sức mạnh số
    (mới nhất 16/02/2025) - cũng đứng yên.
  - GIỮ các kênh tuoitre.vn: chúng SỐNG, trước đây bị báo "không đọc được
    ngày" chỉ vì ghi múi giờ dạng "GMT+7". main.py đã vá.
  - THÊM các nguồn đã đo và xác nhận còn sống.

Ghi chú độ tin cậy:
  [OK]  = đã chạy thành công trong log thực tế
  [ĐO]  = đã đo bằng kiem_tra_nguon.py ngày 10/09/2026, còn sống
  [??]  = suy từ quy luật URL, CHƯA kiểm chứng - xem log để giữ hay bỏ

Điều khoản: các báo cung cấp RSS miễn phí cho cá nhân / phi lợi nhuận.
"""

FEEDS = {
    # ================= THỜI SỰ - TỔNG HỢP =================
    "https://vnexpress.net/rss/tin-noi-bat.rss":        "VnExpress - Nổi bật",        # [ĐO]
    "https://vnexpress.net/rss/thoi-su.rss":            "VnExpress - Thời sự",        # [ĐO]
    "https://vnexpress.net/rss/phap-luat.rss":          "VnExpress - Pháp luật",      # [ĐO]
    "https://vnexpress.net/rss/the-gioi.rss":           "VnExpress - Thế giới",       # [ĐO]
    "https://vnexpress.net/rss/giao-duc.rss":           "VnExpress - Giáo dục",       # [ĐO]
    "https://vnexpress.net/rss/suc-khoe.rss":           "VnExpress - Sức khỏe",       # [ĐO]
    "https://tuoitre.vn/thoi-su.rss":                   "Tuổi Trẻ - Thời sự",         # [ĐO] sống, cần vá GMT+7
    "https://tuoitre.vn/phap-luat.rss":                 "Tuổi Trẻ - Pháp luật",       # [ĐO] sống, cần vá GMT+7
    "https://tuoitre.vn/the-gioi.rss":                  "Tuổi Trẻ - Thế giới",        # [ĐO] sống, cần vá GMT+7
    "https://thanhnien.vn/rss/thoi-su.rss":             "Thanh Niên - Thời sự",       # [ĐO]
    "https://vietnamnet.vn/rss/thoi-su.rss":            "VietnamNet - Thời sự",       # [ĐO] mới

    # ================= LAO ĐỘNG - TIỀN LƯƠNG - BHXH - THUẾ =================
    # Nguồn quan trọng nhất với nghiệp vụ C&B, cũng là chỗ vừa mất 11 kênh NLĐ.
    # Hiện chỉ còn 3 nguồn chuyên đề -> mảng này đang MỎNG, cần bổ sung tiếp
    # bằng đợt ứng viên kế tiếp trong kiem_tra_nguon.py (UNG_VIEN_DOT2).
    "https://dantri.com.vn/rss/lao-dong-viec-lam.rss":  "Dân Trí - LĐ Việc làm",      # [ĐO] mới
    "https://dantri.com.vn/rss/phap-luat.rss":          "Dân Trí - Pháp luật",        # [ĐO] mới
    "https://thanhnien.vn/rss/doi-song.rss":            "Thanh Niên - Đời sống",      # [ĐO] mới

    # ================= TÀI CHÍNH - KINH TẾ =================
    "https://vnexpress.net/rss/kinh-doanh.rss":         "VnExpress - Kinh doanh",     # [ĐO]
    "https://tuoitre.vn/kinh-doanh.rss":                "Tuổi Trẻ - Kinh doanh",      # [ĐO] cần vá GMT+7
    "https://thanhnien.vn/rss/kinh-te.rss":             "Thanh Niên - Kinh tế",       # [ĐO]
    "https://dantri.com.vn/rss/kinh-doanh.rss":         "Dân Trí - Kinh doanh",       # [ĐO]
    "https://cafef.vn/vi-mo-dau-tu.rss":                "CafeF - Vĩ mô",              # [ĐO]
    "https://cafef.vn/tai-chinh-ngan-hang.rss":         "CafeF - Tài chính NH",       # [ĐO]
    "https://cafef.vn/thi-truong-chung-khoan.rss":      "CafeF - Chứng khoán",        # [ĐO] mới

    # ================= CÔNG NGHỆ - AI =================
    "https://vnexpress.net/rss/khoa-hoc-cong-nghe.rss": "VnExpress - Khoa học CN",    # [ĐO]
    "https://tuoitre.vn/nhip-song-so.rss":              "Tuổi Trẻ - Công nghệ",       # [ĐO] cần vá GMT+7
    "https://tuoitre.vn/khoa-hoc.rss":                  "Tuổi Trẻ - Khoa học",        # [ĐO] cần vá GMT+7
    "https://thanhnien.vn/rss/cong-nghe.rss":           "Thanh Niên - Công nghệ",     # [ĐO]
    "https://genk.vn/rss/home.rss":                     "GenK - Công nghệ",           # [ĐO]

    # ================= AI QUỐC TẾ (nguồn tiếng Anh) =================
    # AI trong HR gần như không có báo Việt nào theo dõi thường xuyên.
    # AI sẽ tóm tắt lại bằng tiếng Việt.
    "https://techcrunch.com/category/artificial-intelligence/feed/":
        "TechCrunch - AI",                                                            # [ĐO]
    "https://www.hrdive.com/feeds/news/":
        "HR Dive - Nhân sự quốc tế",                                                  # [ĐO]
    # VentureBeat trả 429 (Too Many Requests) với dải IP GitHub, hỏng lúc được
    # lúc không. Giữ lại vì hỏng một nguồn không làm chết script.
    "https://venturebeat.com/category/ai/feed/":
        "VentureBeat - AI",                                                           # [??] hay 429

    # ================= ĐÃ GỠ 10/09/2026 - ĐỪNG THÊM LẠI =================
    # 11 kênh NLĐ trên tuoitre.vn/nld/rss/...  : đứng yên từ 28-30/06/2026
    # https://dantri.com.vn/rss/xa-hoi.rss     : đứng yên từ 14/05/2026
    # https://dantri.com.vn/rss/suc-manh-so.rss: đứng yên từ 16/02/2025
    # https://dantri.com.vn/rss/an-sinh.rss    : đứng yên từ 28/02/2025
    # https://vietnamnet.vn/rss/kinh-doanh.rss : đứng yên từ 08/08/2026
    # https://laodong.vn/rss/*.rss             : trả 200 nhưng feed RỖNG
    # https://baochinhphu.vn/rss/*.rss         : 404
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
# chuyên mục "Lao động - Việc làm" thì gần như chắc chắn thuộc mảng C&B,
# kể cả khi tiêu đề không chứa từ khóa nào.
#
# Cơ chế tra là startswith(tiền tố) trên TÊN nguồn ở trên -> sửa tên nguồn
# thì phải sửa cả bảng này, nếu không điểm ưu tiên lặng lẽ về 0.
SOURCE_BOOST_CB = {
    "Dân Trí - LĐ Việc làm": 6,
    "HR Dive": 5,
    "Thanh Niên - Đời sống": 2,
}
SOURCE_BOOST_TECH = {
    "TechCrunch - AI": 6,
    "VentureBeat - AI": 6,
    "GenK": 4,
    "CafeF": 4,
    "Thanh Niên - Công nghệ": 3,
    "Tuổi Trẻ - Công nghệ": 3,
    "Tuổi Trẻ - Khoa học": 3,
    "VnExpress - Khoa học CN": 3,
}
