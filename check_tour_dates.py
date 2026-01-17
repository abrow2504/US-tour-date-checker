"""
Tour Date Checker - Monitors for new US concert dates
"""
import os
import json
import smtplib
import re
import urllib.parse
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
# Global configuration
CONFIG = None

def load_config(config_path='config.json'):
    """
    Load configuration from JSON file.
    
    Args:
        config_path (str): Path to the configuration file
        
    Returns:
        dict: Configuration dictionary
    """
    global CONFIG
    
    if not os.path.exists(config_path):
        print(f"Error: Configuration file '{config_path}' not found!")
        print("Please copy 'config.example.json' to 'config.json' and customize it.")
        exit(1)
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            CONFIG = json.load(f)
            print(f"Loaded configuration for: {CONFIG['site']['name']}")
            return CONFIG
    except Exception as e:
        print(f"Error loading config file: {e}")
        exit(1)

def fetch_website():
    """
    Fetch the concert website using Selenium (headless browser) to render JavaScript.
    Uses configuration to determine URL and wait conditions.
    
    Returns:
        str: The HTML content of the webpage after JavaScript is executed, or None if request fails
    """
    url = CONFIG['site']['url']
    wait_element = CONFIG['scraping']['wait_for_element']
    wait_timeout = CONFIG['scraping'].get('wait_timeout', 10)
    
    try:
        # Set up Chrome options for headless mode
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run in background
        chrome_options.add_argument("--no-sandbox")  # Required for GitHub Actions
        chrome_options.add_argument("--disable-dev-shm-usage")  # Overcome limited resource problems
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")  # Hide automation
        
        # Create driver
        driver = webdriver.Chrome(options=chrome_options)
        
        print(f"DEBUG: Fetching {url} with Selenium...")
        driver.get(url)
        
        # Wait for the configured element to load
        print(f"DEBUG: Waiting for element ({wait_element['type']}: {wait_element['value']})...")
        
        # Map config type to Selenium By type
        by_type_map = {
            'class_name': By.CLASS_NAME,
            'id': By.ID,
            'css': By.CSS_SELECTOR,
            'xpath': By.XPATH,
            'tag_name': By.TAG_NAME
        }
        
        by_type = by_type_map.get(wait_element['type'], By.CLASS_NAME)
        
        WebDriverWait(driver, wait_timeout).until(
            EC.presence_of_all_elements_located((by_type, wait_element['value']))
        )
        print("DEBUG: Elements loaded!")
        
        # Get the rendered HTML
        html = driver.page_source
        print(f"DEBUG: Fetched {len(html)} characters from website")
        
        driver.quit()
        return html
        
    except Exception as e:
        print(f"Error fetching website with Selenium: {e}")
        try:
            driver.quit()
        except:
            pass
        return None


def extract_us_dates(html_content):
    """
    Parse the HTML and extract US tour dates by detecting US postal codes in addresses.
    
    Returns:
        list: A list of tour date dictionaries with keys: 'date', 'city', 'venue', 'address'
    """
    # Use the same extraction logic as extract_all_events, then filter for US dates
    all_events = extract_all_events(html_content)
    us_dates = [e for e in all_events if is_us_location_by_postal_code(e.get('address', ''))]
    return us_dates


def extract_all_events(html_content):
    """
    Parse the HTML and extract all tour events (no country filtering).
    Uses configuration to determine CSS selectors and data extraction logic.

    Returns:
        list: A list of tour event dictionaries with keys: 'date', 'city', 'venue', 'address'
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    events_out = []
    
    selectors = CONFIG['scraping']['selectors']

    # Find all event cards using configured selector
    events = soup.select(selectors['event_cards'])
    print(f"DEBUG: Found {len(events)} elements with CSS selector '{selectors['event_cards']}'")
    
    # Debug: print first event if found
    if events:
        print(f"DEBUG: First event HTML snippet: {str(events[0])[:300]}...")
    else:
        # Try alternate selectors to debug
        print(f"DEBUG: Trying alternate selectors...")
        alt1 = soup.find_all('div', class_='card-date')
        print(f"DEBUG: find_all with class_='card-date': {len(alt1)} elements")
        
        alt2 = soup.select('[class*="card-date"]')
        print(f"DEBUG: CSS selector with class*=card-date: {len(alt2)} elements")
        
        # Check if there are any divs at all
        all_divs = soup.find_all('div')
        print(f"DEBUG: Total divs in page: {len(all_divs)}")
        
        # Sample a few div classes
        sample_classes = []
        for div in all_divs[:10]:
            if div.get('class'):
                sample_classes.append(div.get('class'))
        print(f"DEBUG: Sample of div classes: {sample_classes}")

    for idx, event in enumerate(events):
        try:
            # Find the text container with event details
            text_container = event.select_one(selectors.get('text_container', 'div.text-container'))
            if not text_container:
                print(f"DEBUG: Event {idx} has no text-container")
                continue

            # Get date and venue from top-info
            top_info = text_container.select_one(selectors.get('top_info', 'div.top-info'))
            if not top_info:
                print(f"DEBUG: Event {idx} has no top-info")
                continue
            
            date_elem = top_info.select_one(selectors.get('date_element', 'span.date'))
            venue_elem = top_info.select_one(selectors.get('venue_element', 'span.venue'))
            
            # Get city from middle-info
            middle_info = text_container.select_one(selectors.get('middle_info', 'div.middle-info'))
            city_elem = None
            if middle_info:
                city_elem = middle_info.select_one(selectors.get('city_element', 'div.city'))

            if not date_elem or not city_elem:
                print(f"DEBUG: Event {idx} missing date or city")
                continue

            # Extract date and city
            date_text = date_elem.get_text(strip=True)
            city_text = city_elem.get_text(strip=True)
            venue_text = venue_elem.get_text(strip=True) if venue_elem else 'TBA'

            # Get address and link from the data-infos attribute on the "More info" button
            address_text = ''
            link_text = ''
            bottom_infos = text_container.select_one(selectors.get('bottom_info', 'div.bottom-infos'))
            if bottom_infos:
                # try to find a direct tickets link first
                tickets_a = bottom_infos.select_one(selectors.get('tickets_button', 'a.btn'))
                if tickets_a and tickets_a.has_attr('href'):
                    link_text = tickets_a['href']

                more_info_selector = selectors.get('more_info_button', "button[data-open-modal='date-infos']")
                data_attr = selectors.get('data_attribute', 'data-infos')
                more_info_btn = bottom_infos.select_one(more_info_selector)
                
                if more_info_btn and more_info_btn.has_attr(data_attr):
                    try:
                        # Decode the URL-encoded JSON
                        encoded_data = more_info_btn[data_attr]
                        decoded_data = urllib.parse.unquote(encoded_data)
                        event_info = json.loads(decoded_data)
                        address_text = event_info.get('address', '')
                        # prefer link from embedded JSON if present
                        link_text = event_info.get('link', link_text)
                    except Exception as e:
                        print(f"Error decoding event info for event {idx}: {e}")
                        address_text = ''
                else:
                    # fallback: look for primary ticket anchor
                    a_primary = bottom_infos.select_one('a.btn.primary')
                    if a_primary and a_primary.has_attr('href'):
                        link_text = a_primary['href']

            # Create event dictionary
            events_out.append({
                'date': date_text,
                'city': city_text,
                'venue': venue_text,
                'address': address_text,
                'link': link_text
            })
            print(f"DEBUG: Extracted event {idx}: {city_text} on {date_text}")

        except Exception as e:
            print(f"Error parsing event {idx}: {e}")
            continue

    return events_out


def get_us_states_map():
    """
    Returns a mapping of US state abbreviations and full names for fallback matching.
    
    Returns:
        dict: Map of state abbreviations to full names, and full names to abbreviations
    """
    state_abbr_to_name = {
        'AL': 'Alabama', 'AK': 'Alaska', 'AZ': 'Arizona', 'AR': 'Arkansas',
        'CA': 'California', 'CO': 'Colorado', 'CT': 'Connecticut', 'DE': 'Delaware',
        'FL': 'Florida', 'GA': 'Georgia', 'HI': 'Hawaii', 'ID': 'Idaho',
        'IL': 'Illinois', 'IN': 'Indiana', 'IA': 'Iowa', 'KS': 'Kansas',
        'KY': 'Kentucky', 'LA': 'Louisiana', 'ME': 'Maine', 'MD': 'Maryland',
        'MA': 'Massachusetts', 'MI': 'Michigan', 'MN': 'Minnesota', 'MS': 'Mississippi',
        'MO': 'Missouri', 'MT': 'Montana', 'NE': 'Nebraska', 'NV': 'Nevada',
        'NH': 'New Hampshire', 'NJ': 'New Jersey', 'NM': 'New Mexico', 'NY': 'New York',
        'NC': 'North Carolina', 'ND': 'North Dakota', 'OH': 'Ohio', 'OK': 'Oklahoma',
        'OR': 'Oregon', 'PA': 'Pennsylvania', 'RI': 'Rhode Island', 'SC': 'South Carolina',
        'SD': 'South Dakota', 'TN': 'Tennessee', 'TX': 'Texas', 'UT': 'Utah',
        'VT': 'Vermont', 'VA': 'Virginia', 'WA': 'Washington', 'WV': 'West Virginia',
        'WI': 'Wisconsin', 'WY': 'Wyoming',
        'DC': 'District of Columbia'
    }
    
    # Also create name to abbreviation mapping for fallback checking
    state_name_to_abbr = {v.upper(): k for k, v in state_abbr_to_name.items()}
    
    return {
        'abbr_to_name': state_abbr_to_name,
        'name_to_abbr': state_name_to_abbr,
        'all_abbrs': set(state_abbr_to_name.keys()),
        'all_names': set(state_abbr_to_name.values())
    }


def is_us_location_by_postal_code(address_text):
    """
    Detect if an address is in the US by looking for the US postal code format:
    State abbreviation (2 capital letters) followed by 5-digit ZIP code.
    Falls back to checking for US state names/abbreviations if no postal code found.
    
    Examples:
    - "New York, NY 10001" → matches (state abbr + ZIP)
    - "Los Angeles, CA 90210" → matches
    - "New York, NY" → matches (fallback: state abbreviation alone)
    - "New York City" → matches (fallback: state name alone)
    - "1 Pl. Saint-Nazaire, 11000 Carcassonne" → does NOT match (European address)
    
    This distinguishes US addresses from European ones, which just have postal codes
    without state abbreviations.
    
    Args:
        address_text (str): The full address string
        
    Returns:
        bool: True if the address contains a US state + ZIP code pattern, or fallback matches
    """
    # Primary: Pattern for state abbreviation + ZIP code
    # Examples: "NY 10001", "CA 90210-1234", "Texas TX 12345"
    us_pattern = r'[,\s]([A-Z]{2})\s+\d{5}(?:-\d{4})?'
    
    # Search for the pattern in the address
    match = re.search(us_pattern, address_text)
    
    if match:
        state_abbr = match.group(1)
        print(f"DEBUG: Found US postal pattern with state '{state_abbr}' in address: {address_text}")
        return True
    
    # Fallback: Check for state abbreviations or names directly
    states_map = get_us_states_map()
    address_upper = address_text.upper()
    
    # Check for state abbreviations (like "NY", "CA", "TX")
    for abbr in states_map['all_abbrs']:
        # Use word boundaries to avoid matching partial words
        if re.search(rf'\b{abbr}\b', address_upper):
            print(f"DEBUG: Found US state abbreviation '{abbr}' (fallback) in address: {address_text}")
            return True
    
    # Check for state names (like "New York", "California", "Texas")
    for name in states_map['all_names']:
        if re.search(rf'\b{name.upper()}\b', address_upper):
            print(f"DEBUG: Found US state name '{name}' (fallback) in address: {address_text}")
            return True
    
    return False


def load_seen_dates():
    """
    Load the list of previously seen tour dates from a JSON file.
    This prevents duplicate notifications.
    
    Returns:
        list: List of previously seen date strings
    """
    state_file = CONFIG.get('state_file', 'seen_dates.json')
    
    if os.path.exists(state_file):
        try:
            with open(state_file, 'r') as f:
                data = json.load(f)
                return data.get('dates', [])
        except Exception as e:
            print(f"Error loading seen dates: {e}")
            return []
    
    return []


def save_seen_dates(dates):
    """
    Save the current tour dates to a JSON file.
    This way, next time the script runs, it knows which dates are new.
    
    Args:
        dates (list): List of tour date strings to save
    """
    state_file = CONFIG.get('state_file', 'seen_dates.json')
    
    try:
        with open(state_file, 'w') as f:
            json.dump({'dates': dates, 'last_updated': datetime.now().isoformat()}, f)
    except Exception as e:
        print(f"Error saving seen dates: {e}")


def save_all_events(events):
    """
    Save the full list of scraped events to the same JSON state file under key `all_events`.
    This helps verify scraping while keeping existing `dates` behavior intact.
    """
    state_file = CONFIG.get('state_file', 'seen_dates.json')
    data = {}
    try:
        if os.path.exists(state_file):
            with open(state_file, 'r') as f:
                data = json.load(f)
    except Exception:
        data = {}

    data['all_events'] = events
    data['last_scan'] = datetime.now().isoformat()

    try:
        with open(state_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error saving all events: {e}")


def send_email_notification(new_dates):
    """
    Send an email notification with the new tour dates.
    
    Args:
        new_dates (list): List of new tour date dictionaries
    """
    # Check if email notifications are enabled
    if not CONFIG['notifications']['email'].get('enabled', True):
        print("Email notifications are disabled in config")
        return
    
    # Get credentials from environment variables (more secure than hardcoding)
    sender_email = os.getenv('EMAIL_ADDRESS')
    sender_password = os.getenv('EMAIL_PASSWORD')
    recipient_email = os.getenv('RECIPIENT_EMAIL')
    
    if not all([sender_email, sender_password, recipient_email]):
        print("Error: Email environment variables not set")
        return
    
    try:
        # Create the email message with configured subject
        email_config = CONFIG['notifications']['email']
        subject_prefix = email_config.get('subject_prefix', '🎵 NEW')
        subject_suffix = email_config.get('subject_suffix', 'Tour Dates Found!')
        
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"{subject_prefix} {subject_suffix}"
        msg['From'] = sender_email
        msg['To'] = recipient_email
        
        # Base site URL from config
        base_site = CONFIG['site']['url']

        # Create plain text and HTML versions (include event link if available)
        text = "New US tour dates have been found!\n\n"
        html = "<html><body><h2>🎵 New US Tour Dates!</h2><table border='1'><tr><th>Date</th><th>City</th><th>Venue</th><th>Link</th></tr>"

        for date_info in new_dates:
            link = date_info.get('link') or ''
            if not link:
                link = base_site
            text += f"- {date_info['date']}: {date_info['city']} at {date_info['venue']} {link}\n"
            html += f"<tr><td>{date_info['date']}</td><td>{date_info['city']}</td><td>{date_info['venue']}</td><td><a href=\"{link}\">Link</a></td></tr>"

        html += "</table></body></html>"
        
        # Attach both versions
        part1 = MIMEText(text, 'plain')
        part2 = MIMEText(html, 'html')
        msg.attach(part1)
        msg.attach(part2)
        
        # Send the email
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, recipient_email, msg.as_string())
        
        print(f"✅ Email sent! {len(new_dates)} new US dates found.")
    
    except Exception as e:
        print(f"Error sending email: {e}")


def send_sms_via_email(new_dates):
    """
    Send a short SMS via the carrier's email-to-SMS gateway.
    Requires env var `SMS_RECIPIENT_ADDRESS` (e.g. 5551234567@txt.att.net)
    Uses the same SMTP credentials as email notifications.
    """
    if not CONFIG['notifications']['sms'].get('enabled', True):
        print('DEBUG: SMS notifications are disabled in config')
        return
    
    sms_to = os.getenv('SMS_RECIPIENT_ADDRESS')
    sender_email = os.getenv('EMAIL_ADDRESS')
    sender_password = os.getenv('EMAIL_PASSWORD')

    if not sms_to:
        print('DEBUG: SMS_RECIPIENT_ADDRESS not set; skipping SMS via email')
        return
    if not all([sender_email, sender_password]):
        print('DEBUG: SMTP credentials not set; cannot send SMS via email')
        return

    # Build a short message (carrier limits apply ~160 chars)
    lines = []
    for d in new_dates:
        lines.append(f"{d['date']} {d['city']} {d['venue']}")
    body = "New US tour dates: " + "; ".join(lines)
    # Truncate to 150 chars to be safe
    body = body[:150]

    try:
        msg = MIMEText(body)
        msg['Subject'] = ''
        msg['From'] = sender_email
        msg['To'] = sms_to

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, [sms_to], msg.as_string())

        print(f"✅ SMS via email sent to {sms_to}")
    except Exception as e:
        print(f"Error sending SMS via email: {e}")


def send_telegram_notification(new_dates):
    """
    Send a Telegram message to a chat using a bot.
    Requires `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` env vars.
    """
    if not CONFIG['notifications']['telegram'].get('enabled', True):
        print('DEBUG: Telegram notifications are disabled in config')
        return
    
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')

    if not all([bot_token, chat_id]):
        print('DEBUG: Telegram env vars not set; skipping Telegram notification')
        return

    lines = []
    for d in new_dates:
        link = d.get('link') or CONFIG['site']['url']
        lines.append(f"{d['date']}: {d['city']} at {d['venue']} — {link}")

    text = "🎵 New tour dates!\n" + "\n".join(lines)

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {'chat_id': chat_id, 'text': text}

    try:
        r = requests.post(url, data=payload, timeout=10)
        if r.status_code == 200:
            print('✅ Telegram notification sent')
        else:
            print(f'Error sending Telegram message: HTTP {r.status_code} {r.text}')
    except Exception as e:
        print(f'Error sending Telegram message: {e}')


def main():
    """Main function - orchestrates the entire check process."""
    # Step 0: Load configuration
    load_config()
    
    print(f"[{datetime.now()}] Starting tour date check for {CONFIG['site']['name']}...")
    
    # Step 1: Fetch the website
    html = fetch_website()
    if not html:
        print("Failed to fetch website. Exiting.")
        return
    
    # DEBUG: Save HTML to file for inspection
    debug_file = CONFIG.get('debug_html_file', 'debug_html.txt')
    with open(debug_file, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"DEBUG: Saved HTML to {debug_file} for inspection")
    
    # Check if the HTML contains expected content
    if 'card-date' in html:
        print("DEBUG: Found 'card-date' in HTML")
    else:
        print("DEBUG: 'card-date' NOT found in HTML - page may be JavaScript-rendered!")
    
    if 'dates-list' in html:
        print("DEBUG: Found 'dates-list' in HTML")
    else:
        print("DEBUG: 'dates-list' NOT found in HTML")
    
    # Step 2: Extract all events (for verification) and then filter US dates
    all_events = extract_all_events(html)
    print(f"Found {len(all_events)} total events on website")

    # Save all scraped events so you can verify scraping in seen_dates.json
    save_all_events(all_events)

    # TESTING: if FORCE_SEND_FIRST is set, send the first event found (useful for GitHub Actions tests)
    if os.getenv('FORCE_SEND_FIRST') == '1':
        if all_events:
            print('DEBUG: FORCE_SEND_FIRST enabled — sending first event via all channels')
            try:
                send_email_notification([all_events[0]])
            except Exception as e:
                print(f"Error sending forced test email: {e}")
            try:
                send_sms_via_email([all_events[0]])
            except Exception as e:
                print(f"Error in forced SMS: {e}")
            try:
                send_telegram_notification([all_events[0]])
            except Exception as e:
                print(f"Error in forced Telegram: {e}")
        else:
            print('DEBUG: FORCE_SEND_FIRST enabled but no events found')
        return

    # Filter events based on config
    if CONFIG['filtering']['enabled'] and CONFIG['filtering']['type'] == 'us_only':
        current_dates = [e for e in all_events if is_us_location_by_postal_code(e.get('address', ''))]
        print(f"Found {len(current_dates)} US dates on website")
    else:
        # No filtering, use all events
        current_dates = all_events
        print(f"Using all {len(current_dates)} dates (filtering disabled)")
    
    # Step 3: Load previously seen dates
    seen_dates = load_seen_dates()
    
    # Step 4: Find NEW dates (not in the seen list)
    # We compare by creating a unique string from date, city, venue, address and link
    current_date_strings = [f"{d['date']}_{d['city']}_{d['venue']}_{d.get('address','')}_{d.get('link','')}" for d in current_dates]
    new_date_strings = [d for d in current_date_strings if d not in seen_dates]
    
    if new_date_strings:
        # We found new dates!
        print(f"🎉 Found {len(new_date_strings)} new US dates!")
        
        # Get the actual date details for the new ones
        new_dates = [d for d in current_dates if f"{d['date']}_{d['city']}_{d['venue']}_{d['address']}" in new_date_strings]
        
        # Send notification
        send_email_notification(new_dates)
        # Optional: also send SMS via carrier gateway and Telegram
        try:
            send_sms_via_email(new_dates)
        except Exception as e:
            print(f"Error in SMS notification: {e}")
        try:
            send_telegram_notification(new_dates)
        except Exception as e:
            print(f"Error in Telegram notification: {e}")
    else:
        print("No new US dates found.")
    
    # Step 5: Save the current state
    save_seen_dates(current_date_strings)
    print("State saved for next run.")


if __name__ == "__main__":
    main()