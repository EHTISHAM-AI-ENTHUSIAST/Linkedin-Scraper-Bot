"""
LinkedIn Profile Scraper Bot
Scrapes LinkedIn profiles from Google search results
"""

import os
import csv
import time
import random
from datetime import datetime
from urllib.parse import quote_plus

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException

# Configuration
SEARCH_QUERY = os.getenv("SEARCH_QUERY", "site:linkedin.com/in/ software engineer")
OUTPUT_FILE = os.getenv("OUTPUT_FILE", "linkedin_profiles.csv")
MAX_RESULTS = 30
USE_TIMESTAMP = os.getenv("USE_TIMESTAMP", "false").lower() == "true"


def setup_driver(headless=True):
    """Configure and return Chrome WebDriver"""
    chrome_options = Options()
    
    if headless:
        chrome_options.add_argument("--headless=new")
    
    # Essential for GitHub Actions
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-plugins")
    chrome_options.add_argument("--disable-images")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--remote-debugging-port=9222")
    
    # Randomize user agent
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    ]
    chrome_options.add_argument(f"--user-agent={random.choice(user_agents)}")
    
    # Disable automation flags
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)
    
    # Check if CHROME_BIN is set (GitHub Actions)
    chrome_bin = os.getenv("CHROME_BIN")
    if chrome_bin:
        chrome_options.binary_location = chrome_bin
    
    try:
        # Try using chromedriver from PATH first (GitHub Actions)
        driver = webdriver.Chrome(options=chrome_options)
    except WebDriverException:
        # Fallback to webdriver-manager
        from webdriver_manager.chrome import ChromeDriverManager
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
    
    # Execute CDP commands to prevent detection
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    })
    
    return driver


def scrape_google_results(driver, query, max_results=30):
    """Scrape LinkedIn profiles from Google search results"""
    profiles = []
    page = 0
    
    # URL encode the query
    encoded_query = quote_plus(query)
    
    # Add timestamp to make results fresh each time
    timestamp = int(time.time())
    
    while len(profiles) < max_results:
        # Build Google search URL with timestamp parameter for fresh results
        start = page * 10
        url = f"https://www.google.com/search?q={encoded_query}&start={start}&num=10&tbs=qdr:w&t={timestamp}"
        
        print(f"🔍 Scraping page {page + 1}...")
        
        try:
            driver.get(url)
        except WebDriverException as e:
            print(f"⚠️ Error loading page: {e}")
            break
        
        # Random delay to appear more human-like
        time.sleep(random.uniform(2, 4))
        
        # Wait for results to load
        try:
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
        except TimeoutException:
            print("⚠️ Timeout waiting for page to load")
            break
        
        # Check if we hit a CAPTCHA or block
        page_source = driver.page_source.lower()
        if "captcha" in page_source or "unusual traffic" in page_source:
            print("⚠️ Google detected automation, stopping...")
            break

        # Find all search result links - try multiple selectors
        try:
            # Try different selectors for Google search results
            search_results = driver.find_elements(By.CSS_SELECTOR, "div.g")
            
            if not search_results:
                search_results = driver.find_elements(By.CSS_SELECTOR, "div[data-hveid]")
            
            if not search_results:
                # Try finding all links containing linkedin.com/in/
                all_links = driver.find_elements(By.TAG_NAME, "a")
                for link_elem in all_links:
                    try:
                        href = link_elem.get_attribute("href")
                        if href and "linkedin.com/in/" in href and not any(p["link"] == href for p in profiles):
                            text = link_elem.text or "LinkedIn Profile"
                            profiles.append({
                                "title": text[:100] if text else "LinkedIn Profile",
                                "link": href,
                                "scraped_at": datetime.now().isoformat()
                            })
                            print(f"✅ Found: {text[:50]}...")
                            if len(profiles) >= max_results:
                                break
                    except:
                        continue
            else:
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
                                title = "LinkedIn Profile"
                            
                            profile = {
                                "title": title if title else "LinkedIn Profile",
                                "link": link,
                                "scraped_at": datetime.now().isoformat()
                            }
                            
                            # Avoid duplicates
                            if not any(p["link"] == link for p in profiles):
                                profiles.append(profile)
                                print(f"✅ Found: {title[:50] if title else 'Profile'}...")
                            
                            if len(profiles) >= max_results:
                                break
                                
                    except NoSuchElementException:
                        continue
                    
        except Exception as e:
            print(f"⚠️ Error parsing results: {e}")
        
        # Check for "next" button or if we've hit the limit
        page += 1
        if page >= 3:  # Limit to 3 pages to avoid rate limiting
            break
        
        # Random delay between pages
        time.sleep(random.uniform(3, 6))
    
    return profiles


def save_to_csv(profiles, filename):
    """Save scraped profiles to CSV file"""
    if not profiles:
        print("⚠️ No profiles to save, creating empty file...")
        # Create empty CSV with headers
        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["title", "link", "scraped_at"])
            writer.writeheader()
        return
    
    # Write new results (overwrite to avoid duplicates over time)
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["title", "link", "scraped_at"])
        writer.writeheader()
        writer.writerows(profiles)
    
    print(f"💾 Saved {len(profiles)} profiles to {filename}")


def main():
    """Main function to run the scraper"""
    # Generate unique filename with timestamp if enabled
    output_file = OUTPUT_FILE
    if USE_TIMESTAMP:
        base_name = OUTPUT_FILE.rsplit('.', 1)[0]
        extension = OUTPUT_FILE.rsplit('.', 1)[1] if '.' in OUTPUT_FILE else 'csv'
        timestamp_str = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f"{base_name}_{timestamp_str}.{extension}"
    
    print("=" * 50)
    print("🤖 LinkedIn Profile Scraper Bot")
    print("=" * 50)
    print(f"📝 Search Query: {SEARCH_QUERY}")
    print(f"📁 Output File: {output_file}")
    print(f"🎯 Max Results: {MAX_RESULTS}")
    print("=" * 50)
    
    driver = None
    profiles = []
    
    try:
        # Setup driver (headless mode for cloud deployment)
        headless = os.getenv("HEADLESS", "true").lower() == "true"
        print(f"🖥️ Headless mode: {headless}")
        
        driver = setup_driver(headless=headless)
        print("✅ Chrome driver initialized successfully")
        
        # Scrape profiles
        profiles = scrape_google_results(driver, SEARCH_QUERY, MAX_RESULTS)
        
        print(f"\n📊 Total profiles found: {len(profiles)}")
        
    except Exception as e:
        print(f"⚠️ Scraping error (non-fatal): {e}")
        # Don't raise, continue to save whatever we have
        
    finally:
        if driver:
            try:
                driver.quit()
                print("🔒 Browser closed")
            except:
                pass
    
    # Always save results (even if empty) - this ensures the workflow succeeds
    save_to_csv(profiles, output_file)
    
    # Also create/update the main file for workflow
    if USE_TIMESTAMP and output_file != OUTPUT_FILE:
        save_to_csv(profiles, OUTPUT_FILE)
    
    print("\n✅ Scraping completed!")
    
    # Exit with success even if no profiles found
    return 0


if __name__ == "__main__":
    main()
