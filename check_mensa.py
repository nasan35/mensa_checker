import requests
from bs4 import BeautifulSoup
import difflib
import os
import smtplib
from email.message import EmailMessage
import re

URL = "https://mensa.jp/exam/"
SECTION_START = "近畿地方"
SECTION_END = "中国地方"
CACHE_FILE = "cached_section.html"

def fetch_page():
    response = requests.get(URL)
    response.raise_for_status()
    return response.text

def extract_target_text(html):
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text()
    start = text.find(SECTION_START)
    end = text.find(SECTION_END, start)
    return text[start:end] if start != -1 and end != -1 else ""

def extract_target_html(html):
    soup = BeautifulSoup(html, "html.parser")
    content = soup.get_text()
    start = content.find(SECTION_START)
    end = content.find(SECTION_END, start)
    if start != -1 and end != -1:
        full_text = soup.get_text()
        return full_text[start:end]
    else:
        return ""

def load_cached_section():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return f.read()
    return ""

def save_cached_section(section_text):
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        f.write(section_text)

def get_plain_diff(old, new):
    diff = difflib.unified_diff(
        old.splitlines(),
        new.splitlines(),
        lineterm="",
        n=2
    )
    diff_lines = list(diff)
    cleaned_lines = [
        re.sub(r"<[^>]+>", "", line) for line in diff_lines if line.startswith("+ ") or line.startswith("- ")
    ]
    return "\n".join(cleaned_lines)

def send_email(diff_text):
    email_from = os.environ["EMAIL_FROM"]
    email_to = os.environ["EMAIL_TO"]
    email_password = os.environ["EMAIL_PASSWORD"]

    msg = EmailMessage()
    msg["Subject"] = "【MENSA】受験情報ページに更新があります"
    msg["From"] = email_from
    msg["To"] = email_to
    msg.set_content(f"""以下の内容が変更されました：

{diff_text}
""")

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(email_from, email_password)
            smtp.send_message(msg)
        print("✅ メールを送信しました")
    except Exception as e:
        print("❌ メール送信に失敗しました:", e)

def main():
    new_html = fetch_page()
    new_section = extract_target_html(new_html)
    old_section = load_cached_section()

    if extract_target_text(old_section) != extract_target_text(new_html):
        diff_text = get_plain_diff(old_section, new_section)
        send_email(diff_text)
        save_cached_section(new_section)
    else:
        print("変更はありません")

if __name__ == "__main__":
    main()
    # テスト送信用（必要に応じてコメントアウト解除）
    # send_email("これはテスト送信です。実際の変更はありません。")
