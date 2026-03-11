from us_tour_checker.config import load_config
from us_tour_checker.scraper import fetch_website, extract_all_events
from us_tour_checker.notifier import send_email_notification, send_telegram_notification
from us_tour_checker.state import load_seen_dates, save_seen_dates, save_all_events
from us_tour_checker.filter import apply_filtering

from datetime import datetime
import os


def _event_key(event):
    return "_".join([
        str(event.get('date', '')),
        str(event.get('city', '')),
        str(event.get('venue', '')),
        str(event.get('address', '')),
        str(event.get('link', '')),
    ])

def main():
    config = load_config()
    print(f"[{datetime.now()}] Starting tour date check for {config['site']['name']}...")
    html = fetch_website(
        config['site']['url'],
        config['scraping']['wait_for_element'],
        config['scraping'].get('wait_timeout', 10)
    )
    debug_file = config.get('debug_html_file', 'debug_html.txt')
    with open(debug_file, 'w', encoding='utf-8') as f:
        f.write(html)
    selectors = config['scraping']['selectors']
    all_events = extract_all_events(html, selectors)
    print(f"Found {len(all_events)} total events on website")
    save_all_events(all_events)
    current_dates = apply_filtering(all_events, config.get('filtering', {}))
    if config.get('filtering', {}).get('enabled'):
        print(f"After filtering: {len(current_dates)} events match filter '{config['filtering'].get('type')}'")
    seen_dates = load_seen_dates()
    current_date_strings = [_event_key(d) for d in current_dates]
    new_date_strings = [d for d in current_date_strings if d not in seen_dates]
    if new_date_strings:
        print(f"Found {len(new_date_strings)} new US dates!")
        new_dates = [d for d in current_dates if _event_key(d) in new_date_strings]
        send_email_notification(new_dates, config)
        send_telegram_notification(new_dates, config)
    else:
        print("No new US dates found.")
    save_seen_dates(current_date_strings)
    print("State saved for next run.")

if __name__ == "__main__":
    main()
