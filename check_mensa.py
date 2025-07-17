import difflib
import requests
from bs4 import BeautifulSoup
from email.message import EmailMessage
import smtplib

URL = "https://mensa.jp/exam/"
CACHE_FILE = "cached_section.txt"

FROM_EMAIL = "your_email@example.com"  # 差出人のメールアドレス
TO_EMAIL = "your_email@example.com"    # 宛先のメールアドレス（FROMと同じでもOK）
APP_PASSWORD = "your_app_password"     # Gmailなどで生成したアプリパスワード


def extract_target_section(html):
    soup = BeautifulSoup(html, "html.parser")
    full_text = soup.get_text()
    start = full_text.find("近畿地方")
    end = full_text.find("中国地方") + len("中国地方")
    return full_text[start:end].strip()


def load_cached_section():
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return ""


def save_section(section):
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        f.write(section)


def send_email(diff_text):
    msg = EmailMessage()
    msg["Subject"] = "MENSA試験ページの更新検知"
    msg["From"] = FROM_EMAIL
    msg["To"] = TO_EMAIL

    body = f"""https://mensa.jp/exam/

{diff_text}
"""
    msg.set_content(body)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(FROM_EMAIL, APP_PASSWORD)
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

        cleaned_diff_lines = []
        for line in diff:
            if line.startswith('+++') or line.startswith('---') or line.startswith('@@'):
                continue
            elif line.startswith('+') or line.startswith('-'):
                cleaned_diff_lines.append(line[1:].strip())

        diff_text = "\n".join(cleaned_diff_lines)

        if diff_text.strip():
            send_email(diff_text)
            save_section(new_section)


if __name__ == "__main__":
    main()
