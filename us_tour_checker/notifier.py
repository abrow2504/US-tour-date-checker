import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests

def send_email_notification(new_dates, config):
    sender_email = os.getenv('EMAIL_ADDRESS')
    sender_password = os.getenv('EMAIL_PASSWORD')
    recipient_email = os.getenv('RECIPIENT_EMAIL')
    if not all([sender_email, sender_password, recipient_email]):
        print("Error: Email environment variables not set")
        return
    subject = f"{config['notifications']['email'].get('subject_prefix', '🎵 NEW')} {config['notifications']['email'].get('subject_suffix', 'Tour Dates Found!')}"
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = sender_email
    msg['To'] = recipient_email
    text = "New US tour dates have been found!\n\n"
    html = "<html><body><h2>🎵 New US Tour Dates!</h2><table border='1'><tr><th>Date</th><th>City</th><th>Venue</th><th>Link</th></tr>"
    for date_info in new_dates:
        link = date_info.get('link') or config['site']['url']
        text += f"- {date_info['date']}: {date_info['city']} at {date_info['venue']} {link}\n"
        html += f"<tr><td>{date_info['date']}</td><td>{date_info['city']}</td><td>{date_info['venue']}</td><td><a href=\"{link}\">Link</a></td></tr>"
    html += "</table></body></html>"
    part1 = MIMEText(text, 'plain')
    part2 = MIMEText(html, 'html')
    msg.attach(part1)
    msg.attach(part2)
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, recipient_email, msg.as_string())
    print(f"✅ Email sent! {len(new_dates)} new US dates found.")

def send_telegram_notification(new_dates, config):
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    if not all([bot_token, chat_id]):
        print('DEBUG: Telegram env vars not set; skipping Telegram notification')
        return
    lines = []
    for d in new_dates:
        link = d.get('link') or config['site']['url']
        lines.append(f"{d['date']}: {d['city']} at {d['venue']} — {link}")
    text = "🎵 New tour dates!\n" + "\n".join(lines)
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {'chat_id': chat_id, 'text': text}
    r = requests.post(url, data=payload, timeout=10)
    if r.status_code == 200:
        print('✅ Telegram notification sent')
    else:
        print(f'Error sending Telegram message: HTTP {r.status_code} {r.text}')
