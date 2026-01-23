from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import urllib.parse
import json

def fetch_website(url, wait_element, wait_timeout=10):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    driver = webdriver.Chrome(options=chrome_options)
    driver.get(url)
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
    html = driver.page_source
    driver.quit()
    return html

def extract_all_events(html_content, selectors):
    soup = BeautifulSoup(html_content, 'html.parser')
    events_out = []
    events = soup.select(selectors['event_cards'])
    for event in events:
        try:
            text_container = event.select_one(selectors.get('text_container', 'div.text-container'))
            top_info = text_container.select_one(selectors.get('top_info', 'div.top-info'))
            date_elem = top_info.select_one(selectors.get('date_element', 'span.date'))
            venue_elem = top_info.select_one(selectors.get('venue_element', 'span.venue'))
            middle_info = text_container.select_one(selectors.get('middle_info', 'div.middle-info'))
            city_elem = None
            if middle_info:
                city_elem = middle_info.select_one(selectors.get('city_element', 'div.city'))
            date_text = date_elem.get_text(strip=True)
            city_text = city_elem.get_text(strip=True)
            venue_text = venue_elem.get_text(strip=True) if venue_elem else 'TBA'
            address_text = ''
            link_text = ''
            bottom_infos = text_container.select_one(selectors.get('bottom_info', 'div.bottom-infos'))
            if bottom_infos:
                tickets_a = bottom_infos.select_one(selectors.get('tickets_button', 'a.btn'))
                if tickets_a and tickets_a.has_attr('href'):
                    link_text = tickets_a['href']
                more_info_selector = selectors.get('more_info_button', "button[data-open-modal='date-infos']")
                data_attr = selectors.get('data_attribute', 'data-infos')
                more_info_btn = bottom_infos.select_one(more_info_selector)
                if more_info_btn and more_info_btn.has_attr(data_attr):
                    encoded_data = more_info_btn[data_attr]
                    decoded_data = urllib.parse.unquote(encoded_data)
                    event_info = json.loads(decoded_data)
                    address_text = event_info.get('address', '')
                    link_text = event_info.get('link', link_text)
                else:
                    a_primary = bottom_infos.select_one('a.btn.primary')
                    if a_primary and a_primary.has_attr('href'):
                        link_text = a_primary['href']
            events_out.append({
                'date': date_text,
                'city': city_text,
                'venue': venue_text,
                'address': address_text,
                'link': link_text
            })
        except Exception:
            continue
    return events_out
