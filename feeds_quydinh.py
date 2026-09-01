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
    # ---------- NGUỒN VĂN BẢN CHÍNH ----------
    # Khôi phục sau khi ThuVienPhapLuat chặn máy chủ GitHub (403 Forbidden,
    # xác nhận trong log 01/09/2026). Đây là nguồn văn bản pháp quy DUY NHẤT
    # đã kiểm chứng là tải được từ máy chủ.
    # Đặc thù: thẻ <title> để TRỐNG, trích yếu nằm trong <description>,
    # số hiệu chỉ có trong URL -> cần bộ tách riêng (parser "congbao").
    # Đánh đổi: Công báo đăng chậm hơn ban hành khoảng 2 tuần.
    "https://congbao.chinhphu.vn/cac-van-ban-moi-ban-hanh.rss":
        ("Công báo Chính phủ", "vanban", "congbao"),

    # ---------- XƯƠNG SỐNG (đang bị chặn) ----------
    # 403 Forbidden từ máy chủ GitHub. Vẫn giữ trong danh sách và thử mỗi lần
    # với bộ header giống trình duyệt - nếu TVPL nới chặn thì tự dùng lại.
    # Đã kiểm chứng 01/09/2026: 451 văn bản, phủ 17 ngày, ~27 văn bản/ngày.
    # Tiêu đề chứa sẵn số hiệu, có thẻ <category> phân loại. Chất lượng cao nhất.
    # RỦI RO: TVPL có cơ chế chống bot. Nếu runner GitHub bị chặn (403),
    # script tự bỏ qua và chạy tiếp bằng các nguồn còn lại.
    "https://thuvienphapluat.vn/rss.xml": ("ThuVienPhapLuat", "vanban", "std"),

    # ---------- ĐÃ GỠ: BHXH Việt Nam ----------
    # 5 kênh RSS của baohiemxahoi.gov.vn trả về đường dẫn nội bộ
    # FW.aspx?ItemID=N -> Page not found. Không dựng lại được địa chỉ thật
    # vì thiếu mã chuyên mục. Nguồn cấp sai link thì không dùng được.

    # ---------- BÁO CHÍ (bắt nhanh, kém chính xác hơn) ----------
    "https://vnexpress.net/rss/phap-luat.rss":  ("VnExpress - Pháp luật", "tin", "std"),
    "https://tuoitre.vn/nld/rss/nld/lao-dong/chinh-sach.rss":
        ("NLĐ - Lao động/Chính sách", "tin", "std"),
    "https://tuoitre.vn/nld/rss/nld/lao-dong/an-sinh-xa-hoi.rss":
        ("NLĐ - Lao động/An sinh xã hội", "tin", "std"),

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
SCORE_THRESHOLD = 4

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
    # Công văn cơ quan thuế: feed có 80 công văn, 28 về thuế. Loại này không
    # mang dấu QĐ-UBND nên không bị lọc theo tỉnh, chỉ cần trúng từ khóa.
    "chính sách thuế", "miễn thuế", "giảm thuế", "hoàn thuế", "khấu trừ thuế",
    "lệ phí trước bạ", "hóa đơn", "kê khai thuế", "mã số thuế",
    # lao động
    "bộ luật lao động", "hợp đồng lao động", "quan hệ lao động", "công đoàn",
    "an toàn lao động", "vệ sinh lao động", "làm thêm giờ", "thời giờ làm việc",
    "thỏa ước lao động", "nội quy lao động", "kỷ luật lao động",
    "xuất khẩu lao động", "người lao động", "sử dụng lao động",
    # nhân sự khu vực công / DNNN
    "vị trí việc làm", "tinh giản biên chế", "tuyển dụng công chức",
    "tuyển dụng viên chức", "đánh giá xếp loại chất lượng",
]

# Tầng giữa - lý do tồn tại:
# Đo trên 451 văn bản thật, cấu hình 2 tầng cũ bỏ sót các văn bản như
#   "Văn bản hợp nhất 10/2026/VBHN-NĐ-BNV về tuyển dụng, sử dụng và quản lý
#    công chức"  -> chỉ 2đ, bị loại
# vì STRONG_KW có cụm liền "tuyển dụng công chức" nhưng tiêu đề viết tách ra.
# Thêm tầng 2đ + nâng ngưỡng lên 4: bắt đủ các văn bản bị sót, số văn bản
# lọt qua chỉ tăng 32 -> 35, không kéo theo nhiễu.
MEDIUM_KW = [
    "công chức", "viên chức", "cán bộ", "tuyển dụng",
    "lao động hợp đồng", "quản lý công chức", "sử dụng công chức",
    "bố trí công chức", "chế độ đối với",
    "đăng ký thuế", "quản lý thuế",
]

WEAK_KW = [
    "lao động", "việc làm", "nhân sự", "tuyển dụng", "công chức", "viên chức",
    "biên chế", "cán bộ", "nghỉ hưu", "chế độ", "chính sách", "lương",
    "bảo hiểm", "thuế", "đào tạo", "bồi dưỡng", "nhân lực",
    "doanh nghiệp nhà nước", "người có công",
]

# ======================================================================
# NHẬN DIỆN VĂN BẢN ĐỊA PHƯƠNG
# ======================================================================
# TRƯỚC ĐÂY: chặn cứng mọi văn bản UBND/HĐND tỉnh khác TP.HCM.
# ĐO LẠI TRÊN DỮ LIỆU THẬT (451 văn bản, 17 ngày): cách đó loại 131 văn bản,
# trong đó có 8 văn bản thật sự liên quan nghiệp vụ - ví dụ quyết định về
# chế độ lao động hợp đồng, tiêu chuẩn chức danh viên chức.
#
# Sai lầm là lọc theo CẤP BAN HÀNH thay vì theo MỨC LIÊN QUAN. Bộ lọc từ
# khóa vốn đã loại 123 văn bản còn lại (giá đất, quy hoạch...) mà không cần
# chặn theo tỉnh.
#
# NAY: không chặn nữa. Chỉ ĐÁNH DẤU để xếp vào mục riêng ở cuối bản tin,
# tránh văn bản địa phương lấn át văn bản trung ương.
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
        "quyết toán thuế", "thu nhập chịu thuế", "người nộp thuế",
    # Công văn cơ quan thuế: feed có 80 công văn, 28 về thuế. Loại này không
    # mang dấu QĐ-UBND nên không bị lọc theo tỉnh, chỉ cần trúng từ khóa.
    "chính sách thuế", "miễn thuế", "giảm thuế", "hoàn thuế", "khấu trừ thuế",
    "lệ phí trước bạ", "hóa đơn", "kê khai thuế", "mã số thuế", "thuế",
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

# Mục riêng cho văn bản do UBND/HĐND tỉnh khác ban hành.
GROUP_LOCAL = "VĂN BẢN ĐỊA PHƯƠNG KHÁC (tham khảo)"
