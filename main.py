import argparse
import json
import os
import sys
from datetime import datetime
from scraper.scraper import NewsScraper
from summarizer.summarizer import NewsSummarizer
from renderer.renderer import NewsRenderer

# Reconfigure stdout/stderr on Windows to support printing arbitrary Unicode text without crashing
if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        # Fallback for old python versions
        pass

def main():
    parser = argparse.ArgumentParser(description="SmartNews Living Canvas Pipeline")
    parser.add_argument("--limit", type=int, default=5, help="Number of articles to scrape per source")
    parser.add_argument("--offline", action="store_true", help="Force rule-based summarization without Gemini API")
    args = parser.parse_args()

    print("==============================================")
    print("      SMARTNEWS LIVING CANVAS PIPELINE        ")
    print("==============================================")
    
    # Set offline mode if requested
    if args.offline:
        os.environ["GEMINI_API_KEY"] = ""
        os.environ["GOOGLE_API_KEY"] = ""
        print("Running in OFFLINE mode (using rule-based summarizer).")

    # Initialize modules
    scraper = NewsScraper()
    summarizer = NewsSummarizer()
    renderer = NewsRenderer()

    # Step 1: Scrape articles
    print("\n--- Phase 1: News Scraping ---")
    raw_articles = scraper.scrape_all(limit_per_source=args.limit)
    
    # Fetch local news despatches based on location
    local_articles = scraper.get_local_news(limit=5)
    
    # Merge local articles into raw article list
    raw_articles.extend(local_articles)
    
    if not raw_articles:
        print("No articles scraped. Exiting pipeline.")
        return

    # Step 1.5: Ensure all topics are represented (completeness check)
    core_topics = {
        "Technology": ["ai", "tech", "software", "chip", "nvidia", "groq", "anthropic", "openai", "bytedance", "cpu", "streamer"],
        "Economy": ["market", "economy", "fed", "inflation", "stock", "funding", "valuation", "sales", "finance"],
        "Politics": ["court", "election", "biden", "trump", "government", "senate", "parliament", "modi", "minister", "ceasefire", "truce", "judiciary", "justice"],
        "World": ["war", "conflict", "summit", "china", "russia", "global", "border", "diplomacy"],
        "Science": ["health", "cancer", "space", "mars", "nasa", "science", "climate", "breakthrough", "tree", "temple", "pharaoh"],
        "Sports": ["sports", "cricket", "football", "match", "cup", "game", "win", "champion", "olympic", "sinner", "french open"]
    }

    represented_categories = set()
    for article in raw_articles:
        text = (article["title"] + " " + article.get("snippet", "")).lower()
        guessed = "General"
        for cat, keywords in core_topics.items():
            if any(w in text for w in keywords):
                guessed = cat
                break
        if "Local Gazette" in article.get("source", ""):
            represented_categories.add("Local")
        else:
            represented_categories.add(guessed)

    print(f"\nTopic representation scan: {represented_categories}")

    # Inject targeted news for any completely unrepresented core categories
    for cat in core_topics.keys():
        if cat not in represented_categories:
            print(f"Core category '{cat}' is not represented. Fetching targeted stories...")
            topic_articles = scraper.get_topic_news(topic=cat.lower(), limit=2)
            raw_articles.extend(topic_articles)

    # Step 2: Summarize and enrich articles
    print("\n--- Phase 2: AI Summarization & Categorization ---")
    enriched_articles = []
    
    for i, article in enumerate(raw_articles, 1):
        print(f"[{i}/{len(raw_articles)}] Processing: '{article['title']}' ({article['source']})")
        
        # Fetch full text content for AI to read
        content = scraper.fetch_article_content(article['url'])
        
        # AI Summarization
        analysis = summarizer.summarize(article['title'], content)
        
        # Force category to 'Local' if the article is from the local gazette
        category = "Local" if "Local Gazette" in article.get("source", "") else analysis["category"]
        
        # Merge analysis back into article dict
        enriched_article = {
            **article,
            "summary": analysis["summary"],
            "category": category,
            "sentiment": analysis["sentiment"]
        }
        enriched_articles.append(enriched_article)

    # Step 3: Render to HTML
    print("\n--- Phase 3: Canvas Rendering ---")
    success = renderer.render(enriched_articles)
    
    if success:
        # Save structured JSON data
        data_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "newsletter_data.json")
        now = datetime.now()
        payload = {
            "last_updated": now.strftime("%Y-%m-%d %H:%M:%S"),
            "articles": enriched_articles
        }
        
        with open(data_file, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
            
        print(f"Successfully saved structured JSON data to {data_file}")
        print("\nPipeline execution completed successfully!")
        print("Ready to update the Jetro Canvas frame.")
    else:
        print("Pipeline execution completed, but rendering encountered errors.")

if __name__ == "__main__":
    main()
