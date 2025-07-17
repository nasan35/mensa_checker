import os
import smtplib
import difflib
import time
import requests
from bs4 import BeautifulSoup
from email.message import EmailMessage
from pathlib import Path

CACHE_FILE = "./cache.txt"
URL = "https://mensa.jp/exam/"
AREA_START = "近畿地方"
AREA_END = "中国地方"

def fetch_page():
    response = requests.get(URL)
    response.raise_for_status()
    return response.text

def extract_target_text(html):
    start = html.find(AREA_START)
    end = html.find(AREA_END)
    if start == -1 or end == -1 or start >= end:
        return ""
    return html[start:end]

def get_plain_diff(old_html, new_html):
    old_text = extract_target_text(old_html)
    new_text = extract_target_text(new_html)
    old_plain = BeautifulSoup(old_text, "html.parser").get_text()
    new_plain = BeautifulSoup(new_text, "html.parser").get_text()
    diff = difflib.unified_diff(
        old_plain.splitlines(),
        new_plain.splitlines(),
        fromfile='before',
        tofile='after',
        lineterm=''
    )
    return "\n".join(diff)

def send_email(diff_text):
    msg = EmailMessage()
    msg["Subject"] = "【Mensa試験情報】ページに更新がありました"
    msg["From"] = os.environ["EMAIL_FROM"]
    msg["To"] = os.environ["EMAIL_TO"]
    msg.set_content(f"""[変更が検出されました]

ページ: {URL}

変更内容（抜粋）:
{diff_text}
""")

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(os.environ["EMAIL_FROM"], os.environ["EMAIL_PASSWORD"])
        smtp.send_message(msg)

def main():
    new_html = fetch_page()

    if Path(CACHE_FILE).exists():
        old_html = Path(CACHE_FILE).read_text(encoding="utf-8")
        if extract_target_text(old_html) != extract_target_text(new_html):
            diff_text = get_plain_diff(old_html, new_html)
            send_email(diff_text)
        else:
            print("変更なし")
    else:
        print("初回キャッシュ作成")

    Path(CACHE_FILE).write_text(new_html, encoding="utf-8")

if __name__ == "__main__":
    main()
