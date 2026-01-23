import pytest
from us_tour_checker.scraper import extract_all_events

SAMPLE_HTML = '''
<div class="event-card">
  <div class="text-container">
    <div class="top-info">
      <span class="date">2026-03-15</span>
      <span class="venue">Madison Square Garden</span>
    </div>
    <div class="middle-info">
      <div class="city">New York</div>
    </div>
    <div class="bottom-infos">
      <a class="btn" href="https://tickets.com/event1">Tickets</a>
      <button data-infos="%7B%22address%22%3A%20%22New%20York%2C%20NY%2010001%22%7D"></button>
    </div>
  </div>
</div>
'''

SELECTORS = {
    'event_cards': '.event-card',
    'text_container': 'div.text-container',
    'top_info': 'div.top-info',
    'date_element': 'span.date',
    'venue_element': 'span.venue',
    'middle_info': 'div.middle-info',
    'city_element': 'div.city',
    'bottom_info': 'div.bottom-infos',
    'tickets_button': 'a.btn',
    'more_info_button': "button[data-infos]",
    'data_attribute': 'data-infos'
}

def test_extract_all_events():
    events = extract_all_events(SAMPLE_HTML, SELECTORS)
    assert len(events) == 1
    event = events[0]
    assert event['date'] == '2026-03-15'
    assert event['city'] == 'New York'
    assert event['venue'] == 'Madison Square Garden'
    assert event['address'] == 'New York, NY 10001'
    assert event['link'] == 'https://tickets.com/event1'
