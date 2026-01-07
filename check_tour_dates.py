"""
Tour Date Checker - Monitors for new US concert dates
"""
import os
import json
import smtplib
import re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import requests
from bs4 import BeautifulSoup


def fetch_website():
    """
    Fetch the concert website and return the HTML content.
    
    Returns:
        str: The HTML content of the webpage, or None if request fails
    """
    url = "https://apaintedsymphony.expedition33.com/"
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()  # Raise an error if the request failed
        return response.text
    except requests.RequestException as e:
        print(f"Error fetching website: {e}")
        return None


def extract_us_dates(html_content):
    """
    Parse the HTML and extract US tour dates by detecting US postal codes in addresses.
    
    Returns:
        list: A list of tour date dictionaries with keys: 'date', 'city', 'venue', 'address'
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    
    us_dates = []
    
    # Find all event cards - they're in elements with class 'card-date-reveal' or inside 'text-container'
    events = soup.find_all('div', class_='card-date-reveal')
    
    # If card-date-reveal isn't found, try finding text-container elements
    if not events:
        events = soup.find_all('div', class_='text-container')
    
    for event in events:
        try:
            # Extract event information from the visible card
            date_text = event.find('span', class_='date')
            city_text = event.find('span', class_='city')
            venue_text = event.find('span', class_='venue')
            
            # The address is in a hidden dialog, but it's already in the HTML
            # Find the dialog associated with this event
            address_link = event.find_parent().find('a', class_='address')
            
            if not address_link:
                # Try finding the dialog directly on the page
                dialog = soup.find('dialog', {'data-modal': 'date-infos'})
                if dialog:
                    address_link = dialog.find('a', class_='address')
            
            if date_text and city_text:
                address_text = address_link.get_text(strip=True) if address_link else "Address not found"
                
                event_data = {
                    'date': date_text.get_text(strip=True),
                    'city': city_text.get_text(strip=True),
                    'venue': venue_text.get_text(strip=True) if venue_text else 'TBA',
                    'address': address_text
                }
                
                # Check if this event is in the US by detecting US postal code in the address
                if is_us_location_by_postal_code(address_text):
                    us_dates.append(event_data)
        except Exception as e:
            print(f"Error parsing event: {e}")
            continue
    
    return us_dates


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
    
    # Step 2: Extract US dates
    current_dates = extract_us_dates(html)
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
