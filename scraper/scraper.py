import requests
from bs4 import BeautifulSoup
import urllib.parse
import re
import xml.etree.ElementTree as ET
from googlenewsdecoder import new_decoderv1
import os
from dotenv import load_dotenv


class NewsScraper:
    def __init__(self):
        load_dotenv()
        self.newsapi_key = os.getenv("NEWSAPI_KEY")
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }
        self.sources = {
            "CNBC": "https://www.cnbc.com/",
            "Financial Times": "https://www.ft.com/",
            "Reuters": "https://www.reuters.com/",
            "Bloomberg": "https://www.bloomberg.com/",
            "TechCrunch": "https://techcrunch.com/",
            "Fortune": "https://fortune.com/"
        }
        # Direct high-fidelity RSS endpoints focusing on B-school curriculum categories
        self.rss_endpoints = {
            "Macro & Markets": "https://news.google.com/rss/search?q=(%22monetary+policy%22+OR+%22interest+rates%22+OR+tariffs+OR+inflation+OR+currency+OR+Fed+OR+markets+OR+treasury+OR+bonds)+site:cnbc.com+OR+site:reuters.com+OR+site:finance.yahoo.com+OR+site:bloomberg.com&hl=en-US&gl=US&ceid=US:en",
            "Strategy & M&A": "https://news.google.com/rss/search?q=(mergers+OR+acquisitions+OR+M%26A+OR+antitrust+OR+restructuring+OR+takeover+OR+buyout)+site:ft.com+OR+site:marketwatch.com+OR+site:bloomberg.com+OR+site:reuters.com&hl=en-US&gl=US&ceid=US:en",
            "Venture & Disruption": "https://news.google.com/rss/search?q=(startup+funding+OR+%22venture+capital%22+OR+VC+OR+%22enterprise+AI%22+OR+IPO+OR+disruptive+OR+unicorn)+site:techcrunch.com+OR+site:venturebeat.com+OR+site:bloomberg.com+OR+site:wsj.com&hl=en-US&gl=US&ceid=US:en",
            "Leadership & Governance": "https://news.google.com/rss/search?q=(CEO+OR+boardroom+OR+%22activist+investor%22+OR+governance+OR+succession+OR+%22proxy+battle%22+OR+scandal+OR+lawsuit)+site:fortune.com+OR+site:bloomberg.com+OR+site:reuters.com+OR+site:ft.com&hl=en-US&gl=US&ceid=US:en"
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



    def get_topic_news(self, topic, limit=2):
        """Deprecated: returning empty list as part of B-school curriculum pivot."""
        return []

    def get_india_metro_news(self):
        """Deprecated: returning empty list as part of B-school curriculum pivot."""
        return []

    def scrape_all(self, limit_per_source=3):
        """Scrapes B-school feeds and returns aggregated, filtered, scored, and clustered articles."""
        all_articles = []
        for category, rss_url in self.rss_endpoints.items():
            print(f"Scraping category '{category}' from premium feeds...")
            try:
                response = requests.get(rss_url, headers=self.headers, timeout=10)
                if response.status_code != 200:
                    continue
                
                root = ET.fromstring(response.content)
                items = root.findall('.//item')
                
                count = 0
                for item in items:
                    title_el = item.find('title')
                    link_el = item.find('link')
                    desc_el = item.find('description')
                    
                    title = self.clean_text(title_el.text if title_el is not None else "")
                    link = link_el.text if link_el is not None else ""
                    description = self.clean_text(desc_el.text if desc_el is not None else "")
                    description = re.sub(r'<[^>]*>', '', description)
                    
                    if title and link:
                        # Extract clean source name
                        source_name = "Premium Business Desk"
                        if " - " in title:
                            title, source_name = title.rsplit(" - ", 1)
                        
                        # Discard lifestyle/crime/local news (Step 2: Filtering)
                        title_lower = title.lower()
                        desc_lower = description.lower()
                        negative_terms = ["recipe", "review", "movie", "cricket", "football", "sports", "gaming", "celebrity", "crime", "lifestyle", "horoscope", "travel", "fashion"]
                        if any(w in title_lower or w in desc_lower for w in negative_terms):
                            continue
                            
                        # Keywords to prioritize / score (Step 2: Scoring)
                        positive_terms = ["acquisition", "merger", "ipo", "venture capital", "fed", "interest rates", "antitrust", "default", "proxy battle", "boardroom", "ceo", "succession", "restructuring", "activist investor"]
                        score = 0
                        for term in positive_terms:
                            if term in title_lower:
                                score += 5
                            if term in desc_lower:
                                score += 2
                                
                        all_articles.append({
                            "source": source_name.strip(),
                            "title": title.strip(),
                            "url": link,
                            "snippet": description or f"Latest brief from our {category} desk.",
                            "category": category,
                            "score": score,
                            "front_page": False
                        })
                        count += 1
                        if count >= limit_per_source:
                            break
            except Exception as e:
                print(f"Error scraping '{category}': {e}")
                
        # Scrape NewsAPI fintech news if API key is present
        if self.newsapi_key:
            try:
                fintech_articles = self.scrape_newsapi_fintech(limit=limit_per_source)
                all_articles.extend(fintech_articles)
            except Exception as e:
                print(f"Error fetching fintech news from NewsAPI: {e}")
                
        # Step 3: Cross-Reference Popularity & Impact ("Front Page Despatch")
        for i, art1 in enumerate(all_articles):
            title1_words = set(re.findall(r'\b\w{4,}\b', art1["title"].lower()))
            # Remove some common corporate words
            title1_words -= {"says", "will", "after", "over", "with", "from", "million", "billion", "first", "into"}
            
            for j, art2 in enumerate(all_articles):
                if i != j and art1["source"] != art2["source"]:
                    title2_words = set(re.findall(r'\b\w{4,}\b', art2["title"].lower()))
                    title2_words -= {"says", "will", "after", "over", "with", "from", "million", "billion", "first", "into"}
                    
                    overlap = title1_words.intersection(title2_words)
                    # If they share at least 3 high-value nouns, they are breaking news stories!
                    if len(overlap) >= 3:
                        art1["front_page"] = True
                        art2["front_page"] = True
                        art1["score"] += 10  # Up-weight front page despatches!
                        art2["score"] += 10
                        
        # Sort by score descending to prioritize high-signal stories!
        all_articles.sort(key=lambda x: x["score"], reverse=True)
        return all_articles


    def fetch_article_content(self, url):
        """Fetches the full text content of an article for summarization."""
        # Decode Google News URL if applicable
        target_url = url
        if "news.google.com" in url:
            try:
                decoded = new_decoderv1(url)
                if decoded.get("status"):
                    target_url = decoded["decoded_url"]
                    print(f"Decoded Google News URL to: {target_url}")
            except Exception as e:
                print(f"Error decoding Google News URL {url}: {e}")
                
        try:
            response = requests.get(target_url, headers=self.headers, timeout=10, allow_redirects=True)
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
            
            # Check for pure paywall pages (e.g. Financial Times paywall splash page text)
            paywall_indicators = [
                "complete digital access", "ft weekend newspaper", "subscribe to read", 
                "please subscribe", "unlimited digital access", "sign up for free trial", 
                "already a subscriber", "register to read"
            ]
            content_lower = content.lower()
            if any(indicator in content_lower for indicator in paywall_indicators):
                print(f"Paywall signature detected for {target_url}. Discarding paywalled page body to fallback to title-based generator.")
                return ""
                
            if len(content) > 6000:
                content = content[:6000] + "..."
            return content
        except Exception as e:
            print(f"Error fetching content from {target_url}: {e}")
            return ""

    def scrape_newsapi_fintech(self, limit=5):
        if not self.newsapi_key:
            return []
        
        print("Scraping fintech news from NewsAPI...")
        url = f"https://newsapi.org/v2/everything?q=fintech&sortBy=publishedAt&pageSize={limit}&apiKey={self.newsapi_key}"
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                articles = []
                for item in data.get("articles", []):
                    title = self.clean_text(item.get("title", ""))
                    link = item.get("url", "")
                    description = self.clean_text(item.get("description", "") or item.get("content", ""))
                    description = re.sub(r'<[^>]*>', '', description)
                    source_name = item.get("source", {}).get("name", "NewsAPI Desk")
                    
                    if title and link:
                        articles.append({
                            "source": source_name,
                            "title": title,
                            "url": link,
                            "snippet": description or "Latest fintech bulletin.",
                            "category": "Venture & Disruption",
                            "score": 8,
                            "front_page": False
                        })
                print(f"Successfully scraped {len(articles)} fintech articles from NewsAPI.")
                return articles
            else:
                print(f"NewsAPI error: HTTP {response.status_code}")
        except Exception as e:
            print(f"Error calling NewsAPI: {e}")
        return []

