import requests
import hashlib
import smtplib
import difflib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import re

URL = "https://mensa.jp/exam/"
SECTION_START = "近畿地方"
SECTION_END = "中国地方"
HASH_FILE = "section_hash.txt"
TEXT_FILE = "section_text.txt"

def get_section_text(html):
    start = html.find(SECTION_START)
    end = html.find(SECTION_END)
    if start == -1 or end == -1 or start >= end:
        return None
    return html[start:end]

def get_hash(text):
    return hashlib.md5(text.encode("utf-8")).hexdigest()

def load_previous_hash():
    if not os.path.exists(HASH_FILE):
        return None
    with open(HASH_FILE, "r", encoding="utf-8") as f:
        return f.read().strip()

def save_hash(hash_value):
    with open(HASH_FILE, "w", encoding="utf-8") as f:
        f.write(hash_value)

def load_previous_text():
    if not os.path.exists(TEXT_FILE):
        return ""
    with open(TEXT_FILE, "r", encoding="utf-8") as f:
        return f.read()

def save_text(text):
    with open(TEXT_FILE, "w", encoding="utf-8") as f:
        f.write(text)

def send_email(subject, body):
    EMAIL_FROM = os.getenv("EMAIL_FROM")
    EMAIL_TO = os.getenv("EMAIL_TO")
    EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
    if not all([EMAIL_FROM, EMAIL_TO, EMAIL_PASSWORD]):
        print("Missing email configuration.")
        return

    msg = MIMEMultipart()
    msg["From"] = EMAIL_FROM
    msg["To"] = EMAIL_TO
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL_FROM, EMAIL_PASSWORD)
        server.send_message(msg)

def main():
    response = requests.get(URL)
    html = response.text
    section_text = get_section_text(html)
    if section_text is None:
        print("Target section not found.")
        return

    current_hash = get_hash(section_text)
    previous_hash = load_previous_hash()

    if current_hash != previous_hash:
        previous_text = load_previous_text()
        diff = difflib.unified_diff(
            previous_text.splitlines(),
            section_text.splitlines(),
            lineterm="",
            n=3
        )
        diff_text = "\n".join(diff)
        subject = "【MENSA更新通知】"
        body = f"{URL} に変更が検出されました。\n\n▼ 差分（近畿地方〜中国地方の範囲のみ）:\n{diff_text}\n\n（定期監視ツールより自動送信）"
        send_email(subject, body)
        save_hash(current_hash)
        save_text(section_text)
    else:
        print("No change detected.")

if __name__ == "__main__":
    main()
