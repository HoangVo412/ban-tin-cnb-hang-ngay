# -*- coding: utf-8 -*-
"""
Dò lệnh gửi từ Telegram và kích hoạt bản tin.

Cách hoạt động: GitHub Actions chạy file này định kỳ. Mỗi lần chạy nó hỏi
Telegram "có tin nhắn mới nào không", nếu thấy lệnh /run thì chạy bản tin.

Lệnh hỗ trợ:
    /run     - chạy bản tin ngay, kể cả hôm nay đã gửi rồi
    /status  - xem lần gửi gần nhất
    /help    - danh sách lệnh
"""

import os
import sys
import json
import time
import urllib.parse
import urllib.request
from datetime import datetime

import main as bantin   # dùng lại toàn bộ logic của bản tin

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "").strip()
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
OFFSET_FILE = "last_update_id.txt"
API = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

CMD_RUN = {"/run", "run", "/start", "start", "chay", "/chay"}
CMD_STATUS = {"/status", "status", "/trangthai"}
CMD_HELP = {"/help", "help", "/tro giup", "?"}


def log(msg):
    print(f"[{datetime.now(bantin.VN_TZ):%H:%M:%S}] {msg}", flush=True)


def api_call(method, params=None):
    url = f"{API}/{method}"
    data = urllib.parse.urlencode(params or {}).encode()
    req = urllib.request.Request(url, data=data)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode())


def reply(text):
    """Gửi tin nhắn ngắn về đúng chat của chủ bot."""
    try:
        api_call("sendMessage", {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": text,
            "disable_web_page_preview": "true",
        })
    except Exception as ex:
        log(f"Không gửi được phản hồi: {ex}")


def read_offset():
    try:
        with open(OFFSET_FILE, encoding="utf-8") as f:
            return int(f.read().strip())
    except (FileNotFoundError, ValueError):
        return 0


def write_offset(value):
    with open(OFFSET_FILE, "w", encoding="utf-8") as f:
        f.write(str(value))


def main():
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        log("Thiếu TELEGRAM_TOKEN hoặc TELEGRAM_CHAT_ID.")
        sys.exit(1)

    last_id = read_offset()
    log(f"Đang kiểm tra lệnh mới (offset={last_id})...")

    try:
        res = api_call("getUpdates", {"offset": last_id + 1, "timeout": 0})
    except Exception as ex:
        log(f"Lỗi gọi getUpdates: {ex}")
        sys.exit(1)

    updates = res.get("result", [])
    if not updates:
        log("Không có lệnh mới.")
        return

    log(f"Nhận được {len(updates)} cập nhật.")
    max_id = last_id
    want_run = False
    want_status = False
    want_help = False

    for u in updates:
        max_id = max(max_id, u.get("update_id", 0))
        msg = u.get("message") or u.get("edited_message") or {}
        text = (msg.get("text") or "").strip().lower()
        chat_id = str((msg.get("chat") or {}).get("id", ""))

        # BẢO MẬT: username của bot là công khai, ai cũng nhắn được.
        # Chỉ chấp nhận lệnh từ đúng chat của chủ bot, bỏ qua tất cả người khác.
        if chat_id != TELEGRAM_CHAT_ID:
            log(f"  Bỏ qua tin nhắn từ chat lạ: {chat_id}")
            continue

        if not text:
            continue
        log(f"  Lệnh: {text}")
        if text in CMD_RUN:
            want_run = True
        elif text in CMD_STATUS:
            want_status = True
        elif text in CMD_HELP:
            want_help = True
        else:
            want_help = True   # gõ sai thì nhắc danh sách lệnh

    # Ghi offset TRƯỚC khi chạy, để nếu bản tin lỗi thì cũng không
    # bị lặp lại lệnh cũ ở lần dò kế tiếp.
    write_offset(max_id)
    log(f"Đã ghi offset mới: {max_id}")

    if want_status:
        try:
            with open(bantin.STATE_FILE, encoding="utf-8") as f:
                last = f.read().strip()
        except FileNotFoundError:
            last = "(chưa có)"
        reply(f"Lần gửi bản tin gần nhất: {last}\n"
              f"Hôm nay: {bantin.today_vn()}")

    if want_help and not want_run:
        reply("Các lệnh có thể dùng:\n"
              "/run - chạy bản tin ngay\n"
              "/status - xem lần gửi gần nhất\n"
              "/help - danh sách lệnh")

    if want_run:
        reply("Đã nhận lệnh. Đang tổng hợp bản tin, chờ khoảng 1 phút...")
        log("Bắt đầu chạy bản tin theo lệnh /run")
        bantin.FORCE_RUN = True        # bỏ qua kiểm tra trùng ngày
        try:
            bantin.main()
        except Exception as ex:
            log(f"Bản tin lỗi: {ex}")
            reply(f"Bản tin chạy lỗi: {type(ex).__name__}. "
                  f"Kiểm tra log trên GitHub Actions.")
            sys.exit(1)


if __name__ == "__main__":
    main()
