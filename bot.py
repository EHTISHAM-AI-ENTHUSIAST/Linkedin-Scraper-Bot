"""
LinkedIn Profile Scraper Bot
Scrapes LinkedIn profiles from Google search results
"""

import os
import csv
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

# Configuration
SEARCH_QUERY = os.getenv("SEARCH_QUERY", "site:linkedin.com/in/ software engineer")
OUTPUT_FILE = "linkedin_profiles.csv"
MAX_RESULTS = 50


def setup_driver(headless=True):
    """Configure and return Chrome WebDriver"""
    chrome_options = Options()
    
    if headless:
        chrome_options.add_argument("--headless=new")
    
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    # Disable automation flags
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    # Execute CDP commands to prevent detection
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            })
        """
    })
    
    return driver


def scrape_google_results(driver, query, max_results=50):
    """Scrape LinkedIn profiles from Google search results"""
    profiles = []
    page = 0
    
    while len(profiles) < max_results:
        # Build Google search URL
        start = page * 10
        url = f"https://www.google.com/search?q={query}&start={start}"
        
        print(f"🔍 Scraping page {page + 1}...")
        driver.get(url)
        
        # Wait for results to load
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "search"))
            )
        except TimeoutException:
            print("⚠️ Timeout waiting for search results")
            break
        
        # Add random delay to avoid detection
        time.sleep(2)
        
        # Find all search result links
        try:
            search_results = driver.find_elements(By.CSS_SELECTOR, "div.g")
            
            if not search_results:
                print("⚠️ No more results found")
                break
            
            for result in search_results:
                try:
                    link_element = result.find_element(By.CSS_SELECTOR, "a")
                    link = link_element.get_attribute("href")
                    
                    # Only get LinkedIn profile links
                    if link and "linkedin.com/in/" in link:
                        try:
                            title_element = result.find_element(By.CSS_SELECTOR, "h3")
                            title = title_element.text
                        except NoSuchElementException:
                            title = "Unknown"
                        
                        profile = {
                            "title": title,
                            "link": link,
                            "scraped_at": datetime.now().isoformat()
                        }
                        
                        # Avoid duplicates
                        if not any(p["link"] == link for p in profiles):
                            profiles.append(profile)
                            print(f"✅ Found: {title[:50]}...")
                        
                        if len(profiles) >= max_results:
                            break
                            
                except NoSuchElementException:
                    continue
                    
        except Exception as e:
            print(f"⚠️ Error parsing results: {e}")
        
        # Check for "next" button or if we've hit the limit
        page += 1
        if page >= 5:  # Limit to 5 pages to avoid rate limiting
            break
        
        time.sleep(3)  # Delay between pages
    
    return profiles


def save_to_csv(profiles, filename):
    """Save scraped profiles to CSV file"""
    if not profiles:
        print("⚠️ No profiles to save")
        return
    
    # Check if file exists to determine if we need headers
    file_exists = os.path.exists(filename)
    
    with open(filename, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["title", "link", "scraped_at"])
        
        if not file_exists:
            writer.writeheader()
        
        writer.writerows(profiles)
    
    print(f"💾 Saved {len(profiles)} profiles to {filename}")


def main():
    """Main function to run the scraper"""
    print("=" * 50)
    print("🤖 LinkedIn Profile Scraper Bot")
    print("=" * 50)
    print(f"📝 Search Query: {SEARCH_QUERY}")
    print(f"📁 Output File: {OUTPUT_FILE}")
    print(f"🎯 Max Results: {MAX_RESULTS}")
    print("=" * 50)
    
    driver = None
    try:
        # Setup driver (headless mode for cloud deployment)
        headless = os.getenv("HEADLESS", "true").lower() == "true"
        print(f"🖥️ Headless mode: {headless}")
        
        driver = setup_driver(headless=headless)
        
        # Scrape profiles
        profiles = scrape_google_results(driver, SEARCH_QUERY, MAX_RESULTS)
        
        print(f"\n📊 Total profiles found: {len(profiles)}")
        
        # Save results
        save_to_csv(profiles, OUTPUT_FILE)
        
        print("\n✅ Scraping completed successfully!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        raise
        
    finally:
        if driver:
            driver.quit()
            print("🔒 Browser closed")


if __name__ == "__main__":
    main()
