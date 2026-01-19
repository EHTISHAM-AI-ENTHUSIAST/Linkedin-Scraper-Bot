"""
LinkedIn Profile Scraper Bot
Scrapes LinkedIn profiles from Google search results using Selenium WebDriver.
Author: Vibe Coding
"""

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
import csv
import os
from datetime import datetime
from dataclasses import dataclass


@dataclass
class SearchResult:
    """Data class to store a single search result."""
    title: str
    link: str
    scraped_at: str


class LinkedInScraper:
    """
    A Selenium-based bot to scrape LinkedIn profiles from Google search results.
    
    Attributes:
        driver: Chrome WebDriver instance
        wait: WebDriverWait instance for explicit waits
        results: List of scraped SearchResult objects
    """
    
    def __init__(self, headless: bool = False, timeout: int = 10):
        """
        Initialize the Chrome WebDriver with custom options.
        
        Args:
            headless: Run browser in headless mode (no GUI)
            timeout: Default timeout for explicit waits in seconds
        """
        self.options = self._configure_chrome_options(headless)
        self.driver = self._create_driver()
        self.wait = WebDriverWait(self.driver, timeout)
        self.results: list[SearchResult] = []
        print("🚀 Browser initialized successfully!")
    
    def _configure_chrome_options(self, headless: bool) -> Options:
        """Configure Chrome browser options."""
        options = Options()
        
        if headless:
            options.add_argument("--headless=new")
        
        # Performance and stability options
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--start-maximized")
        
        # Disable automation flags
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)
        
        return options
    
    def _create_driver(self) -> webdriver.Chrome:
        """Create and return a Chrome WebDriver instance."""
        service = Service(ChromeDriverManager().install())
        return webdriver.Chrome(service=service, options=self.options)
    
    def search(self, query: str) -> "LinkedInScraper":
        """
        Perform a Google search with the given query.
        
        Args:
            query: Search query string
            
        Returns:
            Self for method chaining
        """
        print(f"\n🔍 Searching: {query}")
        
        try:
            self.driver.get("https://www.google.com")
            
            # Wait for and interact with search box
            search_box = self.wait.until(
                EC.presence_of_element_located((By.NAME, "q"))
            )
            search_box.clear()
            search_box.send_keys(query)
            search_box.send_keys(Keys.RETURN)
            
            # Wait for results to load
            self.wait.until(
                EC.presence_of_element_located((By.ID, "search"))
            )
            print("✅ Search completed!")
            
        except TimeoutException:
            print("❌ Timeout: Search results didn't load in time")
        
        return self
    
    def scrape(self) -> "LinkedInScraper":
        """
        Scrape titles and links from the current search results page.
        
        Returns:
            Self for method chaining
        """
        print("\n📄 Scraping results...")
        self.results.clear()
        
        try:
            headings = self.driver.find_elements(By.CSS_SELECTOR, "h3")
            
            for heading in headings:
                result = self._extract_result(heading)
                if result:
                    self.results.append(result)
            
            print(f"✅ Scraped {len(self.results)} LinkedIn profiles")
            
        except Exception as e:
            print(f"❌ Error during scraping: {e}")
        
        return self
    
    def _extract_result(self, heading) -> SearchResult | None:
        """Extract title and link from a heading element."""
        try:
            title = heading.text.strip()
            if not title:
                return None
            
            # Navigate to parent anchor tag
            parent = heading.find_element(By.XPATH, "./..")
            link = parent.get_attribute("href")
            
            if link and link.startswith("http"):
                return SearchResult(
                    title=title,
                    link=link,
                    scraped_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                )
        except NoSuchElementException:
            pass
        
        return None
    
    def display(self) -> "LinkedInScraper":
        """
        Display all scraped results in a formatted table.
        
        Returns:
            Self for method chaining
        """
        if not self.results:
            print("\n⚠️ No results to display")
            return self
        
        print("\n" + "=" * 70)
        print("📋 SCRAPED LINKEDIN PROFILES")
        print("=" * 70)
        
        for idx, result in enumerate(self.results, start=1):
            print(f"\n[{idx}] {result.title}")
            print(f"    🔗 {result.link}")
            print(f"    🕐 {result.scraped_at}")
        
        print("\n" + "=" * 70)
        print(f"📊 Total: {len(self.results)} profiles found")
        print("=" * 70)
        
        return self
    
    def save_csv(self, filename: str = "linkedin_profiles.csv") -> "LinkedInScraper":
        """
        Save scraped results to a CSV file.
        
        Args:
            filename: Output CSV filename
            
        Returns:
            Self for method chaining
        """
        if not self.results:
            print("\n⚠️ No results to save")
            return self
        
        filepath = os.path.join(os.path.dirname(__file__) or ".", filename)
        
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Title", "Link", "Scraped At"])
            
            for result in self.results:
                writer.writerow([result.title, result.link, result.scraped_at])
        
        print(f"\n💾 Saved {len(self.results)} results to: {filename}")
        return self
    
    def close(self) -> None:
        """Close the browser and clean up resources."""
        if self.driver:
            self.driver.quit()
            print("\n🔒 Browser closed. Goodbye!")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - ensures browser is closed."""
        self.close()


def main():
    """Main entry point for the LinkedIn scraper bot."""
    
    # Configuration
    SEARCH_QUERY = "site:linkedin.com python developer lahore"
    OUTPUT_FILE = "linkedin_profiles.csv"
    
    print("\n" + "=" * 70)
    print("🤖 LINKEDIN PROFILE SCRAPER BOT")
    print("=" * 70)
    
    # Use context manager for automatic cleanup
    with LinkedInScraper(headless=True) as scraper:
        # Method chaining for clean, readable code
        scraper.search(SEARCH_QUERY).scrape().display().save_csv(OUTPUT_FILE)
    
    print("\n✅ Bot execution completed successfully!")


if __name__ == "__main__":
    main()
