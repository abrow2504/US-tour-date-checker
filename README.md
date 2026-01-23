# Tour Date Checker

A highly configurable, reusable tool to monitor websites for new tour dates/events and send notifications via email, SMS, and Telegram. Perfect for tracking concerts, conferences, or any event listings!

## ✨ Features

- **Fully Configurable**: Use JSON config to adapt to any website structure
- **Smart Scraping**: Selenium-based for JavaScript-heavy sites
- **Flexible Filtering**: Built-in US location detection or use all events
- **Multiple Notifications**: Email, SMS (via email gateway), and Telegram
- **State Tracking**: Only notifies on genuinely new dates
- **GitHub Actions**: Set up automated checks every 10 minutes

## 🚀 Quick Start

### 1. Clone & Install

```bash
git clone <your-repo>
cd US-tour-date-checker
pip install -r requirements.txt
```

## 📦 Requirements

- Python 3.10+ with `pip`
- Google Chrome (or Chromium) installed for Selenium to drive
- Matching ChromeDriver/Chrome for local runs (handled automatically in GitHub Actions workflow)
- Project dependencies from `requirements.txt` installed via `pip install -r requirements.txt`

### 2. Configure Your Target Website

Copy the example config and customize it for your website:

```bash
cp config.example.json config.json
```

Edit `config.json` with your website's details:

```json
{
  "site": {
    "name": "My Favorite Band",
    "url": "https://example.com/tour-dates",
    "description": "Tour dates tracker"
  },
  "scraping": {
    "method": "selenium",
    "wait_for_element": {
      "type": "class_name",
      "value": "event-card"
    },
    "selectors": {
      "event_cards": "div.event-card",
      "date_element": "span.date",
      "city_element": "span.city",
      "venue_element": "span.venue"
    }
  }
}
```

### 3. Set Environment Variables

Create a `.env` file or set these in your system:

```bash
# Email notifications (Gmail example)
EMAIL_ADDRESS=your-email@gmail.com
EMAIL_PASSWORD=your-app-password
RECIPIENT_EMAIL=recipient@example.com

# Optional: SMS via carrier gateway
SMS_RECIPIENT_ADDRESS=5551234567@txt.att.net

# Optional: Telegram
TELEGRAM_BOT_TOKEN=your-bot-token
TELEGRAM_CHAT_ID=your-chat-id
```

### 4. Run

```bash
python check_tour_dates.py
```

## 🧪 Testing

- Unit and end-to-end tests live under `tests/` and use `pytest`
- Install dependencies (including pytest) with `pip install -r requirements.txt`
- Run the full suite locally:

```bash
python -m pytest tests
```

Tips:

- Tests mock network/email/Telegram interactions, so no secrets are required
- Use `-k <pattern>` or `-q` flags with pytest to focus on specific modules or quiet the output

## 📋 Configuration Guide

### Site Settings

```json
{
  "site": {
    "name": "Display name for your site",
    "url": "https://example.com/events",
    "description": "What you're tracking"
  }
}
```

### Scraping Settings

The tool uses Selenium to handle JavaScript-rendered pages.

#### Wait Configuration

Tell the scraper what element to wait for before parsing:

```json
{
  "scraping": {
    "wait_for_element": {
      "type": "class_name", // or "id", "css", "xpath", "tag_name"
      "value": "event-item" // the selector value
    },
    "wait_timeout": 10 // seconds to wait
  }
}
```

#### CSS Selectors

Map the HTML structure of your target website:

```json
{
  "scraping": {
    "selectors": {
      "event_cards": "div.event", // Main container for each event
      "text_container": "div.details", // Container with event info
      "date_element": "span.date", // Date element
      "city_element": "span.location", // City/location element
      "venue_element": "span.venue", // Venue name element
      "tickets_button": "a.tickets", // Link to tickets
      "more_info_button": "button.info", // More info button (if any)
      "data_attribute": "data-event-info" // Data attribute name
    }
  }
}
```

**Tips for finding selectors:**

1. Right-click on an event on the website → "Inspect"
2. Look for repeated elements (one per event)
3. Note the class names and structure
4. Use CSS selector syntax: `div.class-name`, `span#id`, etc.

### Filtering

Control which events trigger notifications:

```json
{
  "filtering": {
    "enabled": true, // Set false to get all events
    "type": "us_only", // Currently only "us_only" or disable filtering
    "detection_method": "postal_code"
  }
}
```

- `us_only`: Only notifies for US events using a 3-tier detection system:
  1. **Primary**: State abbreviation + ZIP code (e.g., "NY 10001", "CA 90210")
  2. **Fallback 1**: State abbreviations alone (e.g., "NY", "CA", "TX")
  3. **Fallback 2**: Full state names (e.g., "New York", "California", "Texas")
- Disabled: Get notifications for all events worldwide

### Notifications

Enable/disable each notification channel:

```json
{
  "notifications": {
    "email": {
      "enabled": true,
      "subject_prefix": "🎵 NEW",
      "subject_suffix": "Tour Dates Found!"
    },
    "sms": {
      "enabled": true
    },
    "telegram": {
      "enabled": true
    }
  }
}
```

## 🔧 Finding CSS Selectors for Your Website

### Step-by-Step Guide

1. **Open the target website** in Chrome/Firefox
2. **Right-click** on an event → **Inspect Element**
3. **Find the repeating pattern** - look for a parent element that wraps each event
4. **Note the classes/IDs** used

Example HTML structure:

```html
<div class="event-card">
  <div class="event-details">
    <span class="event-date">Jan 15, 2026</span>
    <span class="event-city">New York, NY</span>
    <span class="event-venue">Madison Square Garden</span>
  </div>
</div>
```

Config for above:

```json
{
  "event_cards": "div.event-card",
  "text_container": "div.event-details",
  "date_element": "span.event-date",
  "city_element": "span.event-city",
  "venue_element": "span.event-venue"
}
```

### Testing Your Config

Run the script once and check `debug_html.txt` and `seen_dates.json`:

```bash
python check_tour_dates.py
```

- `debug_html.txt`: Raw HTML to verify the page loaded
- `seen_dates.json`: Look at `all_events` to see what was extracted

## 🤖 Automated Checking (GitHub Actions)

Set up checks every 10 minutes with GitHub Actions:

> **⚠️ Note on GitHub Actions Run Frequency**
>
> If you use GitHub Actions on a free or public repository, scheduled workflows (like this one) are not guaranteed to run exactly on time. GitHub may delay or skip runs due to server load, repository activity, or maintenance. This means your checks might sometimes run less frequently than scheduled (e.g., every 30–60 minutes instead of every 10). For critical or time-sensitive monitoring, consider running this script on your own server or a dedicated cloud scheduler.

1. **Fork this repo**
2. **Add repository secrets**:
   - Go to Settings → Secrets → Actions
   - Add: `EMAIL_ADDRESS`, `EMAIL_PASSWORD`, `RECIPIENT_EMAIL`, etc.
3. **The workflow runs automatically** (see `.github/workflows/check-dates.yml`)

The GitHub Action:

- Runs every 10 minutes (customizable)
- Installs Chrome and dependencies
- Executes the checker
- Sends notifications when new dates are found

## 📧 Email Setup (Gmail)

1. Enable 2-factor authentication on your Google account
2. Generate an App Password:
   - Google Account → Security → 2-Step Verification → App passwords
3. Use the generated password as `EMAIL_PASSWORD`

## 📱 SMS Setup

Use your carrier's email-to-SMS gateway:

- AT&T: `number@txt.att.net`
- Verizon: `number@vtext.com`
- T-Mobile: `number@tmomail.net`
- Sprint: `number@messaging.sprintpcs.com`

Set `SMS_RECIPIENT_ADDRESS=5551234567@txt.att.net`

## 💬 Telegram Setup

1. Create a bot via [@BotFather](https://t.me/botfather)
2. Get your chat ID via [@userinfobot](https://t.me/userinfobot)
3. Set `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID`

## 🎯 Use Cases

- **Concert Tours**: Track your favorite artists
- **Conference Schedules**: Monitor tech conference announcements
- **Sports Events**: Follow game schedules
- **Theater Shows**: Get notified about new performances
- **Any Event Listing**: If it's on a website, you can track it!

## 🔍 Troubleshooting

### No events found

1. Check `debug_html.txt` - does it have the full page content?
2. Verify your CSS selectors in `config.json`
3. Make sure `wait_for_element` matches what the page loads

### Wrong events detected

- Adjust filtering in config
- Check selector specificity (too broad?)
- Review `seen_dates.json` → `all_events` to see what's being extracted

### Notifications not sending

- Verify environment variables are set
- Check notification `enabled` flags in config
- Look for error messages in console output

## 📝 Example Configs

### Bandsintown Artist Page

```json
{
  "site": {
    "url": "https://www.bandsintown.com/a/artist-name"
  },
  "scraping": {
    "wait_for_element": {
      "type": "css",
      "value": "[data-testid='event-card']"
    },
    "selectors": {
      "event_cards": "[data-testid='event-card']",
      "date_element": "[data-testid='event-date']",
      "city_element": "[data-testid='event-location']",
      "venue_element": "[data-testid='venue-name']"
    }
  }
}
```

### Custom Event Site

```json
{
  "site": {
    "url": "https://yoursite.com/events"
  },
  "scraping": {
    "wait_for_element": {
      "type": "class_name",
      "value": "wp-event"
    },
    "selectors": {
      "event_cards": "li.wp-event",
      "date_element": "time.event-time",
      "city_element": "span.event-location",
      "venue_element": "h3.event-title"
    }
  }
}
```

## 🤝 Contributing

This tool is designed to be reusable! If you adapt it for a popular platform:

1. Test your configuration thoroughly
2. Share your `config.json` as an example
3. Submit a PR with your example config

## 📄 License

MIT License - feel free to use and modify!

## 🙏 Credits

Built to track tour dates and made configurable for the community.
