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
    
    if not raw_articles:
        print("No articles scraped. Exiting pipeline.")
        return


    # Step 2: Summarize and enrich articles
    print("\n--- Phase 2: AI Summarization & Categorization ---")
    enriched_articles = []
    
    for i, article in enumerate(raw_articles, 1):
        print(f"[{i}/{len(raw_articles)}] Processing: '{article['title']}' ({article['source']})")
        
        # Fetch full text content for AI to read
        content = scraper.fetch_article_content(article['url'])
        
        # AI Summarization
        analysis = summarizer.summarize(article['title'], content, article.get('source'))

        
        # Use resolved category
        category = analysis["category"]
        
        # Merge analysis back into article dict
        enriched_article = {
            **article,
            "summary": analysis["summary"],
            "category": category,
            "sentiment": analysis["sentiment"],
            "front_page": article.get("front_page", False)
        }
        enriched_articles.append(enriched_article)

        
        # Sleep to satisfy Gemini API 15 RPM free tier rate limits
        if summarizer.client and i < len(raw_articles):
            import time
            time.sleep(4.5)

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

        # Copy preference card to root as preference.html for static hosting (Vercel)
        import shutil
        pref_src = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".jetro", "frames", "preference_card.html")
        pref_dest = os.path.join(os.path.dirname(os.path.abspath(__file__)), "preference.html")
        try:
            shutil.copy(pref_src, pref_dest)
            print(f"Successfully copied preference card to root: {pref_dest}")
        except Exception as e:
            print(f"Error copying preference card to root: {e}")

        print("\nPipeline execution completed successfully!")
        print("Ready to update the Jetro Canvas frame.")
    else:
        print("Pipeline execution completed, but rendering encountered errors.")

if __name__ == "__main__":
    main()
