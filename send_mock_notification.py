"""
Quick script to send a notification with mock US tour dates for portfolio screenshots.
Sends a real email using your configured credentials.
"""

from us_tour_checker.notifier import send_email_notification, send_telegram_notification
from us_tour_checker.config import load_config

# Mock realistic US tour dates
mock_dates = [
    {
        "date": "May 15, 2026",
        "city": "Los Angeles, CA",
        "venue": "Hollywood Bowl",
        "address": "2301 N Highland Ave, Los Angeles, CA 90068",
        "link": "https://example.com/tickets/la"
    },
    {
        "date": "June 3, 2026",
        "city": "New York, NY",
        "venue": "Madison Square Garden",
        "address": "4 Pennsylvania Plaza, New York, NY 10001",
        "link": "https://example.com/tickets/nyc"
    },
    {
        "date": "June 20, 2026",
        "city": "Chicago, IL",
        "venue": "United Center",
        "address": "1901 W Madison St, Chicago, IL 60612",
        "link": "https://example.com/tickets/chicago"
    }
]

if __name__ == "__main__":
    config = load_config()
    
    print("Sending mock notification with sample US tour dates...")
    print(f"Email will be sent to: {config.get('notifications', {}).get('email', {}).get('recipient') or 'env RECIPIENT_EMAIL'}")
    
    # Send email notification
    send_email_notification(mock_dates, config)
    
    # Optionally send Telegram too
    # send_telegram_notification(mock_dates, config)
    
    print("\n✅ Done! Check your inbox for the notification.")
    print("Take a screenshot of the email for your portfolio.")
