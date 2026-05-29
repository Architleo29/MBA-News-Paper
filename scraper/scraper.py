import requests
from bs4 import BeautifulSoup
import urllib.parse
import re
import xml.etree.ElementTree as ET

class NewsScraper:
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }
        self.sources = {
            "The Hindu": "https://www.thehindu.com/",
            "Hindustan Times": "https://www.hindustantimes.com/",
            "Times of India": "https://timesofindia.indiatimes.com/us",
            "Reuters": "https://www.reuters.com/",
            "Bloomberg": "https://www.bloomberg.com/"
        }
        # Direct high-fidelity RSS endpoints for local news + Google News RSS bypasses for protected global news
        self.rss_endpoints = {
            "The Hindu": "https://www.thehindu.com/news/national/feeder/default.rss",
            "Hindustan Times": "https://www.hindustantimes.com/feeds/rss/india-news/rssfeed.xml",
            "Times of India": "https://timesofindia.indiatimes.com/rssfeeds/296589292.cms",
            "Reuters": "https://news.google.com/rss/search?q=source:Reuters&hl=en-US&gl=US&ceid=US:en",
            "Bloomberg": "https://news.google.com/rss/search?q=source:Bloomberg&hl=en-US&gl=US&ceid=US:en"
        }

    def clean_text(self, text):
        if not text:
            return ""
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def make_absolute_url(self, base_url, url):
        if not url:
            return ""
        return urllib.parse.urljoin(base_url, url)

    def scrape_site(self, name, url, limit=5):
        articles = []
        try:
            print(f"Scraping {name} via verified RSS...")
            rss_url = self.rss_endpoints.get(name)
            
            response = requests.get(rss_url, headers=self.headers, timeout=10)
            if response.status_code != 200:
                print(f"Failed to fetch {name} RSS: HTTP {response.status_code}. Falling back to HTML.")
                return self.scrape_site_html(name, url, limit)
            
            # Robust XML parsing using ElementTree to avoid HTML empty link tags gotcha
            root = ET.fromstring(response.content)
            items = root.findall('.//item')
            
            for item in items:
                title_el = item.find('title')
                link_el = item.find('link')
                desc_el = item.find('description')
                
                title = self.clean_text(title_el.text if title_el is not None else "")
                link = link_el.text if link_el is not None else ""
                description = self.clean_text(desc_el.text if desc_el is not None else "")
                
                # Strip HTML tags from description if any
                description = re.sub(r'<[^>]*>', '', description)
                
                if title and link:
                    # Clean typical " - Source Name" suffix added by Google News RSS
                    if " - " in title:
                        title = title.rsplit(" - ", 1)[0]
                        
                    articles.append({
                        "source": name,
                        "title": title,
                        "url": link,
                        "snippet": description or "Read full verified story on the publisher website."
                    })
                    if len(articles) >= limit:
                        break
                        
        except Exception as e:
            print(f"Error scraping RSS for {name}: {e}. Trying direct HTML fallback...")
            return self.scrape_site_html(name, url, limit)
            
        print(f"Successfully scraped {len(articles)} genuine articles from {name}")
        return articles

    def scrape_site_html(self, name, url, limit=5):
        """Fallback direct HTML scraping in case RSS feed has issues."""
        articles = []
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            if response.status_code != 200:
                return []
            
            soup = BeautifulSoup(response.text, 'html.parser')
            found_items = []
            
            if name == "The Hindu":
                selectors = ["h1 a", "h2 a", "h3 a", "div.title a", "a.story-card-heading"]
                for selector in selectors:
                    for element in soup.select(selector):
                        title = self.clean_text(element.get_text())
                        href = element.get('href')
                        if title and href and len(title) > 20:
                            found_items.append((title, href))
                            
            elif name == "Hindustan Times":
                selectors = ["h1 a", "h2 a", "h3 a", "div.hdg3 a", "a.story-card-heading"]
                for selector in selectors:
                    for element in soup.select(selector):
                        title = self.clean_text(element.get_text())
                        href = element.get('href')
                        if title and href and len(title) > 20:
                            found_items.append((title, href))
                            
            elif name == "Times of India":
                selectors = ["span.w_tle a", "a.headline", "h2 a", "h3 a"]
                for selector in selectors:
                    for element in soup.select(selector):
                        title = self.clean_text(element.get_text())
                        href = element.get('href')
                        if title and href and len(title) > 20:
                            found_items.append((title, href))
                            
            elif name == "Reuters":
                selectors = ["a[data-testid='Heading']", "a.story-card__headline", "h3 a"]
                for selector in selectors:
                    for element in soup.select(selector):
                        title = self.clean_text(element.get_text())
                        href = element.get('href')
                        if title and href and len(title) > 15:
                            found_items.append((title, href))
                            
            elif name == "Bloomberg":
                selectors = ["a[class*='headline']", "a[class*='story']", "h3 a"]
                for selector in selectors:
                    for element in soup.select(selector):
                        title = self.clean_text(element.get_text())
                        href = element.get('href')
                        if title and href and len(title) > 20:
                            found_items.append((title, href))

            if not found_items:
                for tag in ['h1', 'h2', 'h3', 'h4']:
                    for element in soup.find_all(tag):
                        link = element.find('a') if element.name != 'a' else element
                        if not link and element.parent.name == 'a':
                            link = element.parent
                        if link:
                            title = self.clean_text(link.get_text())
                            href = link.get('href')
                            if title and href and len(title) > 20:
                                found_items.append((title, href))
            
            seen_titles = set()
            seen_urls = set()
            for title, href in found_items:
                abs_url = self.make_absolute_url(url, href)
                if not abs_url.startswith("http"):
                    continue
                if abs_url.strip('/') == url.strip('/'):
                    continue
                
                title_lower = title.lower()
                if title_lower not in seen_titles and abs_url not in seen_urls:
                    seen_titles.add(title_lower)
                    seen_urls.add(abs_url)
                    articles.append({
                        "source": name,
                        "title": title,
                        "url": abs_url,
                        "snippet": "Loading story preview..."
                    })
                    if len(articles) >= limit:
                        break
        except Exception as e:
            print(f"Error scraping HTML fallback for {name}: {e}")
        return articles

    def get_local_location(self):
        """Resolves the user's city and country automatically using their IP address with robust fallbacks."""
        # Fallback 1: ipapi.co
        try:
            print("Resolving location via ipapi.co...")
            response = requests.get("https://ipapi.co/json/", headers=self.headers, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if "city" in data and "country_name" in data:
                    return data["city"], data["country_name"]
        except Exception as e:
            print(f"ipapi.co failed: {e}")

        # Fallback 2: ip-api.com
        try:
            print("Resolving location via ip-api.com...")
            response = requests.get("http://ip-api.com/json/", headers=self.headers, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "success":
                    return data.get("city", "Delhi"), data.get("country", "India")
        except Exception as e:
            print(f"ip-api.com failed: {e}")

        # Fallback 3: ipinfo.io
        try:
            print("Resolving location via ipinfo.io...")
            response = requests.get("https://ipinfo.io/json", headers=self.headers, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if "city" in data:
                    city = data["city"]
                    country = data.get("country", "India")
                    return city, country
        except Exception as e:
            print(f"ipinfo.io failed: {e}")

        print("All geolocation services failed. Falling back to Delhi, India.")
        return "Delhi", "India"

    def get_topic_news(self, topic, limit=2):
        """Queries Google News RSS search to fetch fresh stories specifically for a target topic/category."""
        print(f"Scraping category-specific news for topic: {topic}...")
        query = urllib.parse.quote(topic)
        rss_url = f"https://news.google.com/rss/search?q={query}&hl=en-IN&gl=IN&ceid=IN:en"
        
        articles = []
        try:
            response = requests.get(rss_url, headers=self.headers, timeout=10)
            if response.status_code == 200:
                root = ET.fromstring(response.content)
                items = root.findall('.//item')
                for item in items:
                    title_el = item.find('title')
                    link_el = item.find('link')
                    desc_el = item.find('description')
                    
                    title = self.clean_text(title_el.text if title_el is not None else "")
                    link = link_el.text if link_el is not None else ""
                    description = self.clean_text(desc_el.text if desc_el is not None else "")
                    
                    description = re.sub(r'<[^>]*>', '', description)
                    
                    if title and link:
                        if " - " in title:
                            title = title.rsplit(" - ", 1)[0]
                            
                        articles.append({
                            "source": f"{topic.title()} Desk",
                            "title": title,
                            "url": link,
                            "snippet": description or f"Latest updates from the {topic} news desk."
                        })
                        if len(articles) >= limit:
                            break
        except Exception as e:
            print(f"Error fetching topic news for {topic}: {e}")
            
        print(f"Successfully scraped {len(articles)} articles for topic: {topic}")
        return articles

    def get_local_news(self, limit=5):
        """Fetches regional verified local despatches based on the resolved user city location."""
        city, country = self.get_local_location()
        print(f"Resolved user local region: {city}, {country}")
        
        # Build query for local news
        query = urllib.parse.quote(f"{city} local news")
        rss_url = f"https://news.google.com/rss/search?q={query}&hl=en-IN&gl=IN&ceid=IN:en"
        
        articles = []
        try:
            print(f"Scraping local despatches from {rss_url}...")
            response = requests.get(rss_url, headers=self.headers, timeout=10)
            if response.status_code == 200:
                root = ET.fromstring(response.content)
                items = root.findall('.//item')
                for item in items:
                    title_el = item.find('title')
                    link_el = item.find('link')
                    desc_el = item.find('description')
                    
                    title = self.clean_text(title_el.text if title_el is not None else "")
                    link = link_el.text if link_el is not None else ""
                    description = self.clean_text(desc_el.text if desc_el is not None else "")
                    
                    description = re.sub(r'<[^>]*>', '', description)
                    
                    if title and link:
                        if " - " in title:
                            title = title.rsplit(" - ", 1)[0]
                            
                        articles.append({
                            "source": f"Local Gazette ({city})",
                            "title": title,
                            "url": link,
                            "snippet": description or f"Local reports from the {city} region."
                        })
                        if len(articles) >= limit:
                            break
        except Exception as e:
            print(f"Error fetching local news: {e}")
            
        print(f"Successfully scraped {len(articles)} local despatches")
        return articles

    def scrape_all(self, limit_per_source=3):
        all_articles = []
        for name, url in self.sources.items():
            site_articles = self.scrape_site(name, url, limit_per_source)
            all_articles.extend(site_articles)
        return all_articles

    def fetch_article_content(self, url):
        """Fetches the full text content of an article for summarization."""
        try:
            response = requests.get(url, headers=self.headers, timeout=10, allow_redirects=True)
            if response.status_code != 200:
                return ""
            
            soup = BeautifulSoup(response.text, 'html.parser')
            for element in soup(["script", "style", "nav", "footer", "header", "aside"]):
                element.decompose()
                
            paragraphs = soup.find_all('p')
            text_blocks = []
            for p in paragraphs:
                txt = self.clean_text(p.get_text())
                if len(txt) > 40:
                    text_blocks.append(txt)
            
            content = " ".join(text_blocks)
            if len(content) > 6000:
                content = content[:6000] + "..."
            return content
        except Exception as e:
            print(f"Error fetching content from {url}: {e}")
            return ""
