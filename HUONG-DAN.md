# Bản tin tổng hợp hằng ngày — Hướng dẫn cài đặt

Chạy trên GitHub Actions (miễn phí, không cần bật máy). Kết quả gửi về Telegram lúc 6h30 sáng T2–T6.

Tổng thời gian cài đặt lần đầu: khoảng 30 phút.

---

## BƯỚC 1 — Tạo bot Telegram và lấy chat_id

*Mục đích: có nơi nhận bản tin.*

1. Cài Telegram trên điện thoại, đăng ký bằng số điện thoại.
2. Tìm tài khoản **@BotFather** (có tick xanh), bấm Start.
3. Gõ `/newbot` → đặt tên hiển thị (vd: `Ban tin C&B`) → đặt username phải kết thúc bằng `bot` (vd: `bantin_cb_vh_bot`).
4. BotFather trả về một chuỗi dạng `8123456789:AAH...` → đây là **TELEGRAM_TOKEN**, lưu lại.
5. Tìm bot vừa tạo theo username, bấm **Start** và nhắn một câu bất kỳ (bắt buộc — bot không nhắn được cho người chưa từng nhắn nó trước).
6. Lấy **chat_id**: mở trình duyệt, dán địa chỉ sau (thay TOKEN của anh vào):

```
https://api.telegram.org/bot<TOKEN>/getUpdates
```

Tìm đoạn `"chat":{"id":123456789,` → số đó là **TELEGRAM_CHAT_ID**.

---

## BƯỚC 2 — Lấy API key Gemini

*Mục đích: AI lọc và viết bản tin.*

1. Vào **aistudio.google.com/apikey**, đăng nhập bằng Gmail cá nhân.
2. Bấm **Create API key** → chọn tạo project mới nếu được hỏi.
3. Copy chuỗi `AIza...` → đây là **GEMINI_API_KEY**.

Lưu ý: đây là key free tier, khác với gói Google AI Pro. Một lần chạy mỗi ngày dùng chưa tới 1% hạn mức miễn phí.

---

## BƯỚC 3 — Tạo repository trên GitHub

*Mục đích: nơi chứa code và nơi chạy tự động.*

1. Đăng ký tài khoản tại **github.com** (miễn phí).
2. Bấm dấu **+** góc phải trên → **New repository**.
3. Đặt tên: `ban-tin-hang-ngay`. Chọn **Private**. Bấm **Create repository**.

---

## BƯỚC 4 — Tải code lên

*Mục đích: đưa 4 file vào repository.*

Cách dễ nhất, không cần cài Git:

1. Giải nén file `ban-tin.zip` ra một thư mục trên máy.
2. Ở trang repository vừa tạo, bấm **uploading an existing file**.
3. Kéo thả các file: `main.py`, `feeds.py`, `requirements.txt`, `HUONG-DAN.md` vào.
4. Bấm **Commit changes**.
5. Thư mục `.github/workflows` cần tạo riêng vì GitHub không cho kéo thả thư mục ẩn:
   - Bấm **Add file** → **Create new file**
   - Ở ô tên file, gõ chính xác: `.github/workflows/bantin.yml` (gõ dấu `/` sẽ tự tạo thư mục)
   - Mở file `bantin.yml` trong thư mục đã giải nén bằng Notepad, copy toàn bộ nội dung, dán vào
   - Bấm **Commit changes**

---

## BƯỚC 5 — Khai báo 3 khóa bí mật

*Mục đích: để code dùng được token mà không lộ ra trong file.*

Trong repository: **Settings** → cột trái chọn **Secrets and variables** → **Actions** → bấm **New repository secret**.

Tạo lần lượt 3 secret, tên phải gõ **chính xác** như sau:

| Name | Secret |
|---|---|
| `GEMINI_API_KEY` | chuỗi `AIza...` ở Bước 2 |
| `TELEGRAM_TOKEN` | chuỗi `8123...:AAH...` ở Bước 1 |
| `TELEGRAM_CHAT_ID` | dãy số ở Bước 1 |

---

## BƯỚC 6 — Chạy thử

1. Vào tab **Actions** của repository.
2. Nếu hiện thông báo hỏi có bật workflow không, bấm **I understand my workflows, go ahead and enable them**.
3. Cột trái chọn **Ban tin hang ngay** → bên phải bấm **Run workflow** → **Run workflow**.
4. Đợi 1–2 phút, bấm vào lần chạy để xem log.
5. Kiểm tra Telegram.

**Đọc log để dọn nguồn RSS:** trong log sẽ có các dòng `OK  <tên nguồn>: N tin` và `LỖI <tên nguồn>`. Nguồn nào báo LỖI ở mọi lần chạy thì mở `feeds.py`, xóa dòng đó đi cho gọn. Script vẫn chạy bình thường dù có nguồn hỏng.

---

## Tùy chỉnh về sau

**Đổi giờ chạy** — sửa dòng `cron` trong `bantin.yml`. GitHub dùng giờ UTC, giờ VN = UTC + 7.
- 6h30 VN → `30 23 * * 0-4`
- 7h00 VN → `0 0 * * 1-5`
- 8h00 VN → `0 1 * * 1-5`

*Lưu ý: GitHub Actions thường chạy trễ 5–20 phút so với giờ hẹn khi hệ thống bận. Đây là đặc tính của dịch vụ miễn phí, không sửa được.*

**Thêm nguồn báo** — mở `feeds.py`, thêm một dòng vào `FEEDS`. Tìm link RSS bằng cách vào trang `<tên báo>.vn/rss.htm`.

**Đổi độ dài, cách viết bản tin** — sửa biến `PROMPT` trong `main.py`. Phần B đang bị khóa chặt (cấm AI diễn giải nội dung pháp lý, cấm trích số điều khoản). Đừng nới lỏng chỗ đó.

**Đổi model** — sửa `MODEL` trong `main.py` hoặc thêm secret `GEMINI_MODEL`.

---

## Ba điều cần biết

1. **GitHub tự tắt lịch chạy nếu repository không có hoạt động gì trong 60 ngày.** Sẽ có email cảnh báo. Khi đó chỉ cần vào Actions bấm **Run workflow** một lần là kích hoạt lại.

2. **Phần B là radar, không phải nguồn trích dẫn.** Prompt đã cấm AI diễn giải nội dung pháp lý, nhưng trước khi báo cáo lãnh đạo bất kỳ con số nào, vẫn phải mở văn bản gốc kiểm chứng.

3. **RSS của các báo được cấp miễn phí cho cá nhân và tổ chức phi lợi nhuận.** Dùng nội bộ thì không vấn đề gì; nếu sau này phát tán rộng thì phải ghi rõ nguồn.
