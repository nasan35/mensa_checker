import os
import requests
import difflib
import smtplib
from bs4 import BeautifulSoup
from email.message import EmailMessage

URL = "https://mensa.jp/exam/"
SECTION_START = "近畿地方"
SECTION_END = "中国地方"
CACHE_FILE = "latest_section.txt"

def extract_target_section(html):
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text()
    start_index = text.find(SECTION_START)
    end_index = text.find(SECTION_END)
    if start_index == -1 or end_index == -1 or start_index >= end_index:
        return ""
    return text[start_index:end_index].strip()

def load_cached_section():
    if not os.path.exists(CACHE_FILE):
        return ""
    with open(CACHE_FILE, "r", encoding="utf-8") as f:
        return f.read()

def save_section(text):
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        f.write(text)

def send_email(diff_text):
    email_from = os.environ["EMAIL_FROM"]
    email_to = os.environ["EMAIL_TO"]
    email_password = os.environ["EMAIL_PASSWORD"]

    msg = EmailMessage()
    msg["Subject"] = "【MENSA】試験情報に更新がありました"
    msg["From"] = email_from
    msg["To"] = email_to
    msg.set_content(f"""MENSAの試験情報ページに以下の更新がありました：

{diff_text}
""")

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(email_from, email_password)
        smtp.send_message(msg)

def main():
    response = requests.get(URL)
    new_section = extract_target_section(response.text)
    old_section = load_cached_section()

    if new_section != old_section:
        diff = difflib.unified_diff(
            old_section.splitlines(),
            new_section.splitlines(),
            lineterm=""
        )
        diff_text = "\n".join(diff)
        if diff_text.strip():  # 差分が存在する場合
            send_email(diff_text)
            save_section(new_section)

if __name__ == "__main__":
    main()
