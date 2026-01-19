# LinkedIn Scraper Bot 🤖

A Selenium-based bot that scrapes LinkedIn profiles from Google search results and runs 24/7 on GitHub Actions.

## 🚀 Features

- Scrapes LinkedIn profiles from Google search results
- Runs automatically every 6 hours via GitHub Actions
- Exports results to CSV
- Supports manual trigger with custom search queries
- Headless browser operation for cloud deployment

## 📁 Project Structure

```
├── bot.py                 # Main scraper bot
├── requirements.txt       # Python dependencies
├── Dockerfile            # Container configuration
├── runtime.txt           # Python version
└── .github/
    └── workflows/
        └── scraper.yml   # GitHub Actions workflow
```

## 🔧 Local Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/EHTISHAM-AI-ENTHUSIAST/linkedin-scraper-bot.git
   cd linkedin-scraper-bot
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the bot:**
   ```bash
   python bot.py
   ```

## ☁️ Cloud Deployment (GitHub Actions)

The bot is configured to run automatically on GitHub Actions:

- **Scheduled runs:** Every 6 hours (0:00, 6:00, 12:00, 18:00 UTC)
- **Manual trigger:** Go to Actions → LinkedIn Scraper Bot → Run workflow
- **Results:** Saved as artifacts and optionally committed to the repo

### Customizing the Schedule

Edit `.github/workflows/scraper.yml` and modify the cron expression:

```yaml
schedule:
  - cron: '0 */6 * * *'  # Every 6 hours
  # - cron: '0 0 * * *'  # Daily at midnight
  # - cron: '0 * * * *'  # Every hour
```

### Manual Trigger with Custom Query

1. Go to **Actions** tab in your repository
2. Select **LinkedIn Scraper Bot** workflow
3. Click **Run workflow**
4. Enter your custom search query
5. Click **Run workflow**

## 📊 Output

Results are saved to `linkedin_profiles.csv` with the following columns:
- Title (Profile name/headline)
- Link (LinkedIn profile URL)
- Scraped At (Timestamp)

## ⚙️ Configuration

Edit `bot.py` to customize:
- `SEARCH_QUERY`: Default search query
- `OUTPUT_FILE`: Output CSV filename
- `headless`: Set to `False` for local debugging with visible browser

## 📝 License

MIT License

## 👤 Author

**EHTISHAM-AI-ENTHUSIAST**
