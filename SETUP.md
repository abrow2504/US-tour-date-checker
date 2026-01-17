# Tour Date Checker Setup Guide

This script automatically checks for new concert tour dates and sends you notifications via email, SMS, and Telegram.

## How It Works (The Big Picture)

1. **Configuration File** - Define your target website and CSS selectors in `config.json`
2. **Python Script** - Visits the website, extracts events, detects NEW dates
3. **Notifications** - Sends you alerts via Email, SMS, and/or Telegram when new dates are found
4. **GitHub Actions** - Runs your script automatically (every hour by default), completely free
5. **State Tracking** - Remembers which dates you've already been notified about

It's similar to a Power Automate workflow, but running on GitHub's servers instead of Microsoft's.

---

## Setup Steps

### Step 0: Configure Your Target Website

**This is the most important step!** The script needs to know how to parse your specific website.

1. **Copy the example config:**
   ```bash
   cp config.example.json config.json
   ```

2. **Edit `config.json`** with your website details:
   - `site.url` - The website URL to monitor
   - `site.name` - A friendly name for your site
   - `scraping.selectors` - CSS selectors that match your website's HTML structure

3. **Find CSS selectors** (see detailed guide in README.md):
   - Right-click on an event on the website → Inspect
   - Find the class names for: event cards, dates, cities, venues
   - Update the selectors in `config.json`

4. **Test your config locally:**
   ```bash
   python check_tour_dates.py
   ```
   Check `debug_html.txt` and `seen_dates.json` to verify it's working.

For detailed configuration instructions, see the [README.md](README.md).

### Step 1: Set Up Gmail (Your Email Sender)

Since we're sending emails from a Gmail account, you need to set up an "App Password":

1. Go to https://myaccount.google.com/
2. Click **Security** on the left sidebar
3. Enable **2-Step Verification** (if not already done)
4. After 2FA is enabled, go back to Security and find **App Passwords**
5. Select "Mail" and "Windows Computer"
6. Google will generate a 16-character password - **copy this** (you'll need it in Step 4)

### Step 2: Create Initial State File

Create a file called `seen_dates.json` in your repository root with this content:

```json
{
  "dates": [],
  "last_updated": "2026-01-06T00:00:00"
}
```

This file stores which dates you've already been notified about. Push it to GitHub.

### Step 3: Add GitHub Secrets

GitHub "Secrets" are like secure environment variables - they're encrypted and only visible to the Actions workflow.

1. Go to your repository on GitHub
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret** and add these three:

| Name | Value |
|------|-------|
| `EMAIL_ADDRESS` | Your Gmail address (e.g., `yourname@gmail.com`) |
| `EMAIL_PASSWORD` | The 16-character App Password from Step 1 |
| `RECIPIENT_EMAIL` | The email where you want notifications (can be the same as EMAIL_ADDRESS) |

You can optionally add these additional secrets to enable SMS and Telegram notifications:

| Name | Value / Notes |
|------|---------------|
| `TELEGRAM_BOT_TOKEN` | Token from BotFather when you create a Telegram bot |
| `TELEGRAM_CHAT_ID` | Your chat ID (see instructions below) |
| `SMS_RECIPIENT_ADDRESS` | An email-to-SMS gateway address, e.g. `5551234567@txt.att.net` |

### Step 4: Verify the Workflow File

The workflow file (`.github/workflows/check-tour-dates.yml`) is already in the repo. It tells GitHub to:
- Run every 10 minutes
- Install Python and required libraries
- Run your script
- Save the state file back to the repo

### Step 5: Test It!

1. Go to your GitHub repository
2. Click the **Actions** tab
3. On the left, click **Check Tour Dates**
4. Click **Run workflow** → **Run workflow**
5. Wait 30 seconds and refresh - you should see it running (blue dot = in progress, green checkmark = success)
6. You should receive a test email!

If you added `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID`, the workflow will also attempt to send a Telegram message when new dates are found.

If you added `SMS_RECIPIENT_ADDRESS`, the workflow will attempt to send a short SMS via the carrier's email-to-SMS gateway. Carrier gateways differ — a few examples:

- AT&T: `NUMBER@txt.att.net`
- T-Mobile: `NUMBER@tmomail.net`
- Verizon: `NUMBER@vtext.com`

Notes on getting Telegram credentials:

1. In Telegram, start a chat with the user `@BotFather` and follow instructions to create a new bot. BotFather will give you a `BOT_TOKEN`.
2. To get your `CHAT_ID`, you can message your bot and then visit `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates` in a browser (replace `<YOUR_BOT_TOKEN>`). The response will include your chat id. Alternatively, add the bot to a group and use the same method to find the group's chat id.

Notes on SMS and Google Voice:

- The script only supports sending SMS via carrier email-to-SMS gateways (which are free). Google Voice does not provide a supported free HTTP API for sending SMS; automating Google Voice via browser automation is brittle and may violate their terms of service.

Security reminder: keep repository secrets private. Do not commit API tokens or phone numbers into source files.

---

## How the Script Works (Detailed Explanation)

### The Website Scraping Part
```
fetch_website() → downloads the HTML from the concert site
extract_us_dates() → reads through the HTML and finds all events with "US" or state names
```

Think of this like using Power Automate to parse an HTML response - same concept, different syntax.

### The New Date Detection Part
```
Load what we saw last time from seen_dates.json
Compare it to what we see now
If something is new → send an email
Save the current list for next time
```

This prevents duplicate notifications.

### The Email Part
```
Uses Gmail's SMTP server (SMTP = Simple Mail Transfer Protocol, which is just a fancy way to say "send email")
Formats the email with HTML tables so it looks nice
Sends it to your email address
```

---

## Important Notes & Next Steps

### ⚠️ Website Selector Issue
The script currently looks for elements with class names like `event-item`, `date`, `city`. **These probably don't match the actual website.**

To fix this:
1. Visit https://apaintedsymphony.expedition33.com/
2. Right-click an event → **Inspect** (opens Developer Tools)
3. Look at the HTML structure to find the correct class names or CSS selectors
4. Update the `extract_us_dates()` function with the correct selectors

(I can help you do this once you inspect the website!)

### Future Enhancements
- Add iOS webhook notifications (IFTTT)
- Add SMS notifications (Twilio)
- Improve US location detection
- Add logging/history of all found dates
- Check for ticket sale links

### Troubleshooting
- **No emails arriving?** Check GitHub Actions logs for errors
- **Duplicate notifications?** Make sure `seen_dates.json` is being committed to the repo
- **Script fails?** GitHub Actions logs will tell you exactly what went wrong

---

## Key Concepts You're Learning

- **Web Scraping**: Downloading and parsing HTML to extract data
- **State Management**: Remembering what happened last time so you don't repeat it
- **Scheduled Automation**: Running code on a schedule without having your computer on
- **Environment Variables**: Securely storing sensitive data (passwords) separate from code

These are skills used everywhere in software development!
