# -*- coding: utf-8 -*-
"""
Nguồn và bộ lọc cho bot Quy định HR.

Khác với bản tin C&B: bot này KHÔNG dùng AI. Chỉ lọc và liệt kê nguyên văn
tiêu đề văn bản. Lý do: bản tin đi vào việc nghiệp vụ, một con số bịa ra
có thể bị dùng thật. Không sinh chữ mới thì không thể bịa.
"""

# ======================================================================
# NGUỒN
# ======================================================================
# kind = "vanban" -> mục văn bản pháp luật, có số hiệu
# kind = "tin"    -> tin tức ngành, không có số hiệu

FEEDS = {
    # ---------- XƯƠNG SỐNG ----------
    # Đã kiểm chứng 01/09/2026: 451 văn bản, phủ 17 ngày, ~27 văn bản/ngày.
    # Tiêu đề chứa sẵn số hiệu, có thẻ <category> phân loại. Chất lượng cao nhất.
    # RỦI RO: TVPL có cơ chế chống bot. Nếu runner GitHub bị chặn (403),
    # script tự bỏ qua và chạy tiếp bằng các nguồn còn lại.
    "https://thuvienphapluat.vn/rss.xml": ("ThuVienPhapLuat", "vanban"),

    # ---------- BỔ SUNG CHUYÊN NGÀNH ----------
    # Đã kiểm chứng 01/09/2026: feed sống, tiêu đề đầy đủ.
    # Đây là TIN NGÀNH, không phải văn bản -> không có số hiệu.
    "https://baohiemxahoi.gov.vn/pages/chi-tiet-kenh-rss.aspx?ItemID=2":
        ("BHXH Việt Nam - Tin tức", "tin"),
    "https://baohiemxahoi.gov.vn/pages/chi-tiet-kenh-rss.aspx?ItemID=3":
        ("BHXH Việt Nam - Hoạt động ngành", "tin"),
    "https://baohiemxahoi.gov.vn/pages/chi-tiet-kenh-rss.aspx?ItemID=4":
        ("BHXH Việt Nam - Luật BHXH, BHYT", "tin"),
    "https://baohiemxahoi.gov.vn/pages/chi-tiet-kenh-rss.aspx?ItemID=8":
        ("BHXH Việt Nam - Ốm đau, thai sản", "tin"),
    "https://baohiemxahoi.gov.vn/pages/chi-tiet-kenh-rss.aspx?ItemID=10":
        ("BHXH Việt Nam - Cải cách TTHC", "tin"),

    # ---------- BÁO CHÍ (bắt nhanh, kém chính xác hơn) ----------
    "https://vnexpress.net/rss/phap-luat.rss":  ("VnExpress - Pháp luật", "tin"),
    "https://tuoitre.vn/nld/rss/nld/lao-dong/chinh-sach.rss":
        ("NLĐ - Lao động/Chính sách", "tin"),
    "https://tuoitre.vn/nld/rss/nld/lao-dong/an-sinh-xa-hoi.rss":
        ("NLĐ - Lao động/An sinh xã hội", "tin"),

    # ---------- ĐÃ LOẠI ----------
    # Cục Thuế (gdt.gov.vn/wps/wcm/...): feed hỏng, mọi mục đều có tiêu đề
    #   "Lib Site", không có tiêu đề thật lẫn link riêng. Không dùng được.
    #   Không mất mát đáng kể vì TVPL đã bao trùm cả mảng thuế.
    # Công báo Chính phủ: bỏ theo yêu cầu.
}

# ======================================================================
# BỘ LỌC TỪ KHÓA
# ======================================================================
# Cơ chế chấm điểm giống bản tin C&B: từ mạnh 3 điểm, từ yếu 1 điểm,
# đạt SCORE_THRESHOLD mới được đưa vào bản tin.
SCORE_THRESHOLD = 3

STRONG_KW = [
    # tiền lương
    "tiền lương", "tiền công", "lương tối thiểu", "lương cơ sở", "lương hưu",
    "thang bảng lương", "nâng bậc lương", "phụ cấp", "trợ cấp", "thưởng tết",
    "chế độ tiền lương", "định mức lao động", "tiền lương tối thiểu",
    # bảo hiểm
    "bảo hiểm xã hội", "bhxh", "bảo hiểm y tế", "bhyt", "bảo hiểm thất nghiệp",
    "bhtn", "trợ cấp thất nghiệp", "ốm đau", "thai sản", "tai nạn lao động",
    "bệnh nghề nghiệp", "an sinh xã hội", "hưu trí", "tuổi nghỉ hưu",
    # thuế
    "thuế thu nhập cá nhân", "thuế tncn", "giảm trừ gia cảnh",
    "quyết toán thuế", "thu nhập chịu thuế", "người nộp thuế",
    # lao động
    "bộ luật lao động", "hợp đồng lao động", "quan hệ lao động", "công đoàn",
    "an toàn lao động", "vệ sinh lao động", "làm thêm giờ", "thời giờ làm việc",
    "thỏa ước lao động", "nội quy lao động", "kỷ luật lao động",
    "xuất khẩu lao động", "người lao động", "sử dụng lao động",
    # nhân sự khu vực công / DNNN
    "vị trí việc làm", "tinh giản biên chế", "tuyển dụng công chức",
    "tuyển dụng viên chức", "đánh giá xếp loại chất lượng",
]

WEAK_KW = [
    "lao động", "việc làm", "nhân sự", "tuyển dụng", "công chức", "viên chức",
    "biên chế", "cán bộ", "nghỉ hưu", "chế độ", "chính sách", "lương",
    "bảo hiểm", "thuế", "đào tạo", "bồi dưỡng", "nhân lực",
    "doanh nghiệp nhà nước", "người có công",
]

# ======================================================================
# LỌC PHẠM VI ĐỊA PHƯƠNG
# ======================================================================
# Feed TVPL có nhiều quyết định của UBND các tỉnh khác (Quảng Ninh,
# Lâm Đồng...). Đo thực tế: 8/24 văn bản HR là cấp tỉnh không liên quan.
# Chỉ giữ văn bản trung ương và của TP.HCM.
LOCAL_MARKERS = ["QĐ-UBND", "NQ-HĐND", "QĐ-HĐND", "KH-UBND", "CT-UBND"]
LOCAL_KEEP = ["hồ chí minh", "tp.hcm", "tphcm", "thành phố hồ chí minh"]

# ======================================================================
# NHÓM HIỂN THỊ TRONG BẢN TIN
# ======================================================================
# Thứ tự trong danh sách quyết định thứ tự nhóm khi trình bày.
GROUPS = [
    ("TIỀN LƯƠNG - THU NHẬP", [
        "tiền lương", "tiền công", "lương tối thiểu", "lương cơ sở",
        "thang bảng lương", "nâng bậc lương", "phụ cấp", "thưởng",
        "lương hưu", "định mức lao động",
    ]),
    ("BẢO HIỂM XÃ HỘI - Y TẾ - THẤT NGHIỆP", [
        "bảo hiểm xã hội", "bhxh", "bảo hiểm y tế", "bhyt",
        "bảo hiểm thất nghiệp", "bhtn", "ốm đau", "thai sản",
        "hưu trí", "an sinh xã hội", "tai nạn lao động", "bệnh nghề nghiệp",
    ]),
    ("THUẾ THU NHẬP CÁ NHÂN", [
        "thuế thu nhập cá nhân", "thuế tncn", "giảm trừ gia cảnh",
        "quyết toán thuế", "thu nhập chịu thuế", "người nộp thuế", "thuế",
    ]),
    ("LAO ĐỘNG - HỢP ĐỒNG - CÔNG ĐOÀN", [
        "hợp đồng lao động", "bộ luật lao động", "công đoàn",
        "an toàn lao động", "làm thêm giờ", "quan hệ lao động",
        "xuất khẩu lao động", "thời giờ làm việc",
    ]),
    ("CÁN BỘ - CÔNG CHỨC - VIÊN CHỨC", [
        "công chức", "viên chức", "biên chế", "vị trí việc làm",
        "tuyển dụng", "cán bộ", "đánh giá xếp loại",
    ]),
]
GROUP_OTHER = "KHÁC"
