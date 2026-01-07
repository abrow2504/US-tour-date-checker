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


def fetch_website():
    """
    Fetch the concert website using Selenium (headless browser) to render JavaScript.
    
    Returns:
        str: The HTML content of the webpage after JavaScript is executed, or None if request fails
    """
    url = "https://apaintedsymphony.expedition33.com/"
    
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
        
        # Wait for the dates list to load (max 10 seconds)
        print("DEBUG: Waiting for dates to load...")
        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, "card-date"))
        )
        print("DEBUG: Dates loaded!")
        
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
    
    The address data is stored in a data-infos attribute as URL-encoded JSON.
    We decode and parse it to get the full event details.

    Returns:
        list: A list of tour event dictionaries with keys: 'date', 'city', 'venue', 'address'
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    events_out = []

    # Find all event cards by the actual class name using CSS selector
    # This is more reliable than find_all() for complex selectors
    events = soup.select('div.card-date')
    print(f"DEBUG: Found {len(events)} elements with CSS selector 'div.card-date'")
    
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
            text_container = event.find('div', class_='text-container')
            if not text_container:
                print(f"DEBUG: Event {idx} has no text-container")
                continue

            # Get date and venue from top-info
            top_info = text_container.find('div', class_='top-info')
            if not top_info:
                print(f"DEBUG: Event {idx} has no top-info")
                continue
            
            date_elem = top_info.find('span', class_='date')
            venue_elem = top_info.find('span', class_='venue')
            
            # Get city from middle-info
            middle_info = text_container.find('div', class_='middle-info')
            city_elem = None
            if middle_info:
                city_elem = middle_info.find('div', class_='city')

            if not date_elem or not city_elem:
                print(f"DEBUG: Event {idx} missing date or city")
                continue

            # Extract date and city
            date_text = date_elem.get_text(strip=True)
            city_text = city_elem.get_text(strip=True)
            venue_text = venue_elem.get_text(strip=True) if venue_elem else 'TBA'

            # Get address from the data-infos attribute on the "More info" button
            address_text = ''
            bottom_infos = text_container.find('div', class_='bottom-infos')
            if bottom_infos:
                more_info_btn = bottom_infos.find('button', {'data-open-modal': 'date-infos'})
                if more_info_btn and more_info_btn.has_attr('data-infos'):
                    try:
                        # Decode the URL-encoded JSON
                        encoded_data = more_info_btn['data-infos']
                        decoded_data = urllib.parse.unquote(encoded_data)
                        event_info = json.loads(decoded_data)
                        address_text = event_info.get('address', '')
                    except Exception as e:
                        print(f"Error decoding event info for event {idx}: {e}")
                        address_text = ''

            # Create event dictionary
            events_out.append({
                'date': date_text,
                'city': city_text,
                'venue': venue_text,
                'address': address_text
            })
            print(f"DEBUG: Extracted event {idx}: {city_text} on {date_text}")

        except Exception as e:
            print(f"Error parsing event {idx}: {e}")
            continue

    return events_out


def is_us_location_by_postal_code(address_text):
    """
    Detect if an address is in the US by looking for US postal code format.
    
    US postal codes are distinctive:
    - 5 digits (e.g., "10001" for New York)
    - 5 digits + 4 (e.g., "10001-1234" for extended format)
    
    This is more reliable than checking city names because:
    - It's based on a standardized format
    - It works even if new European cities are added
    - Postal codes are unique and unambiguous
    
    Args:
        address_text (str): The full address string (e.g., "123 Main St, New York, NY 10001")
        
    Returns:
        bool: True if the address contains a US postal code pattern
    """
    # Regex pattern for US postal codes: 5 digits or 5 digits-4 digits
    # The pattern looks for: digit digit digit digit digit (optional: dash digit digit digit digit)
    us_zip_pattern = r'\b\d{5}(?:-\d{4})?\b'
    
    # Search for the pattern in the address
    if re.search(us_zip_pattern, address_text):
        return True
    
    return False


def load_seen_dates():
    """
    Load the list of previously seen tour dates from a JSON file.
    This prevents duplicate notifications.
    
    Returns:
        list: List of previously seen date strings
    """
    state_file = 'seen_dates.json'
    
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
    state_file = 'seen_dates.json'
    
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
    state_file = 'seen_dates.json'
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
    Send an email notification with the new US tour dates.
    
    Args:
        new_dates (list): List of new tour date dictionaries
    """
    # Get credentials from environment variables (more secure than hardcoding)
    sender_email = os.getenv('EMAIL_ADDRESS')
    sender_password = os.getenv('EMAIL_PASSWORD')
    recipient_email = os.getenv('RECIPIENT_EMAIL')
    
    if not all([sender_email, sender_password, recipient_email]):
        print("Error: Email environment variables not set")
        return
    
    try:
        # Create the email message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = "🎵 NEW US Tour Dates Found!"
        msg['From'] = sender_email
        msg['To'] = recipient_email
        
        # Create plain text and HTML versions
        text = "New US tour dates have been found!\n\n"
        html = "<html><body><h2>🎵 New US Tour Dates!</h2><table border='1'><tr><th>Date</th><th>City</th><th>Venue</th></tr>"
        
        for date_info in new_dates:
            text += f"- {date_info['date']}: {date_info['city']} at {date_info['venue']}\n"
            html += f"<tr><td>{date_info['date']}</td><td>{date_info['city']}</td><td>{date_info['venue']}</td></tr>"
        
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


def main():
    """Main function - orchestrates the entire check process."""
    print(f"[{datetime.now()}] Starting tour date check...")
    
    # Step 1: Fetch the website
    html = fetch_website()
    if not html:
        print("Failed to fetch website. Exiting.")
        return
    
    # DEBUG: Save HTML to file for inspection
    with open('debug_html.txt', 'w', encoding='utf-8') as f:
        f.write(html)
    print("DEBUG: Saved HTML to debug_html.txt for inspection")
    
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

    # Filter US events from the full list
    current_dates = [e for e in all_events if is_us_location_by_postal_code(e.get('address', ''))]
    print(f"Found {len(current_dates)} US dates on website")
    
    # Step 3: Load previously seen dates
    seen_dates = load_seen_dates()
    
    # Step 4: Find NEW dates (not in the seen list)
    # We compare by creating a unique string from date, city, venue, and address
    current_date_strings = [f"{d['date']}_{d['city']}_{d['venue']}_{d['address']}" for d in current_dates]
    new_date_strings = [d for d in current_date_strings if d not in seen_dates]
    
    if new_date_strings:
        # We found new dates!
        print(f"🎉 Found {len(new_date_strings)} new US dates!")
        
        # Get the actual date details for the new ones
        new_dates = [d for d in current_dates if f"{d['date']}_{d['city']}_{d['venue']}_{d['address']}" in new_date_strings]
        
        # Send notification
        send_email_notification(new_dates)
    else:
        print("No new US dates found.")
    
    # Step 5: Save the current state
    save_seen_dates(current_date_strings)
    print("State saved for next run.")


if __name__ == "__main__":
    main()