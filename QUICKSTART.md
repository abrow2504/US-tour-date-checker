# Quick Start Guide

## For Users Who Want to Monitor a Different Website

### 1. Copy the Example Config
```bash
cp config.example.json config.json
```

### 2. Find Your Website's Selectors

Open your target website in Chrome, right-click on an event, and select "Inspect":

**Look for:**
- The main container div that wraps each event (e.g., `div.event-card`)
- The date element (e.g., `span.date`)
- The city element (e.g., `span.city`)
- The venue element (e.g., `span.venue`)

### 3. Update config.json

```json
{
  "site": {
    "name": "Your Artist Name",
    "url": "https://example.com/tour-dates"
  },
  "scraping": {
    "wait_for_element": {
      "type": "class_name",
      "value": "event-card"  // ← The class name to wait for
    },
    "selectors": {
      "event_cards": "div.event-card",     // ← Main wrapper
      "date_element": "span.date",          // ← Date selector
      "city_element": "span.city",          // ← City selector
      "venue_element": "span.venue"         // ← Venue selector
    }
  },
  "filtering": {
    "enabled": false  // ← Set to false to get ALL events worldwide
  }
}
```

### 4. Test Locally

```bash
python check_tour_dates.py
```

**Check these files:**
- `debug_html.txt` - Verify the page loaded correctly
- `seen_dates.json` - Look at `all_events` to see what was extracted

### 5. Common Selector Types

| Type | Example | Use When |
|------|---------|----------|
| `class_name` | `"event-card"` | Element has a class (most common) |
| `css` | `"div.event-card"` or `"[data-testid='event']"` | Complex selectors |
| `id` | `"event-list"` | Element has an ID |
| `xpath` | `"//div[@class='events']"` | Complex nested structures |

### 6. Enable/Disable Notifications

In `config.json`:

```json
{
  "notifications": {
    "email": {
      "enabled": true  // ← Set to false to disable
    },
    "sms": {
      "enabled": false  // ← Only if you have SMS set up
    },
    "telegram": {
      "enabled": false  // ← Only if you have Telegram set up
    }
  }
}
```

## Troubleshooting

### "No events found"
1. Check `debug_html.txt` - does it have content?
2. Your selectors might be wrong - inspect the HTML again
3. Try `wait_for_element` with a different selector

### "Found 0 events with CSS selector"
- Your `event_cards` selector is incorrect
- Open the website, inspect an event, and find the correct class name

### "Event has no date/city/venue"
- Your individual element selectors are wrong
- Each selector should point to the element containing that specific data

### Getting ALL events (not just US)
Set `"filtering.enabled": false` in config.json

## Example Configs

### Simple Event List
```json
{
  "scraping": {
    "selectors": {
      "event_cards": "li.event",
      "date_element": "time",
      "city_element": "span.location",
      "venue_element": "h3"
    }
  }
}
```

### Events with Data Attributes
```json
{
  "scraping": {
    "selectors": {
      "event_cards": "[data-event-id]",
      "date_element": "[data-date]",
      "city_element": "[data-city]",
      "venue_element": "[data-venue]"
    }
  }
}
```

### WordPress Events Plugin
```json
{
  "scraping": {
    "wait_for_element": {
      "type": "class_name",
      "value": "tribe-events-list-event"
    },
    "selectors": {
      "event_cards": "div.tribe-events-list-event",
      "date_element": "span.tribe-event-date-start",
      "city_element": "span.tribe-venue-location",
      "venue_element": "span.tribe-venue"
    }
  }
}
```

## Need Help?

1. Check the full [README.md](README.md) for detailed documentation
2. Look at [SETUP.md](SETUP.md) for GitHub Actions setup
3. Review `config.example.json` for all available options
