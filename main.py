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
    
    # Fetch India metro news despatches (covering major metro cities)
    metro_articles = scraper.get_india_metro_news()
    
    # Merge metro articles into raw article list
    raw_articles.extend(metro_articles)
    
    if not raw_articles:
        print("No articles scraped. Exiting pipeline.")
        return

    # Step 1.5: Ensure all topics are represented (completeness check)
    import re
    
    core_topics = {
        "Technology": [r"\bai\b", r"\btech\b", r"\btechnology\b", r"\bsoftware\b", r"\bapple\b", r"\bgoogle\b", r"\bmicrosoft\b", r"\bcyber\b", r"\bchip\b", r"\bnvidia\b", r"\bquantum\b", r"\bgroq\b", r"\bopenai\b", r"\banthropic\b", r"\bbytedance\b", r"\bcpu\b"],
        "Economy": [r"\bmarket\b", r"\beconomy\b", r"\bfed\b", r"\binflation\b", r"\bstock\b", r"\bdollar\b", r"\btrade\b", r"\bfinance\b", r"\brate\b", r"\bbloomberg\b", r"\bfunding\b", r"\bvaluation\b", r"\bsales\b", r"\bfiscal\b", r"\bbusiness\b"],
        "Politics": [r"\bcourt\b", r"\belection\b", r"\bbiden\b", r"\btrump\b", r"\bgovernment\b", r"\bsenate\b", r"\bparliament\b", r"\bmodi\b", r"\bminister\b", r"\bceasefire\b", r"\bjudiciary\b", r"\bjustice\b", r"\bpolicy\b", r"\blegislative\b"],
        "World": [r"\bwar\b", r"\bconflict\b", r"\bsummit\b", r"\bchina\b", r"\brussia\b", r"\bglobal\b", r"\bun\b", r"\bborder\b", r"\breuters\b", r"\btruce\b", r"\bdiplomacy\b", r"\bgeopolitical\b"],
        "Science": [r"\bhealth\b", r"\bcancer\b", r"\bspace\b", r"\bmars\b", r"\bnasa\b", r"\bscience\b", r"\bclimate\b", r"\bcarbon\b", r"\bbreakthrough\b", r"\btree\b", r"\btemple\b", r"\bpharaoh\b"],
        "Sports": [r"\bcricket\b", r"\bfootball\b", r"\bolympic\b", r"\bmatch\b", r"\bcup\b", r"\bgame\b", r"\bleague\b", r"\bwin\b", r"\bsinner\b", r"\bfrench open\b", r"\byadav\b", r"\buganda\b", r"\bpandya\b", r"\bindians\b", r"\bipl\b", r"\bt20\b", r"\bsquad\b", r"\bbatsman\b", r"\bbowler\b", r"\bwicket\b", r"\bruns\b", r"\bathletes\b", r"\btournament\b", r"\bchampionship\b", r"\bchampions\b", r"\bbcci\b", r"\bfifa\b", r"\bwimbledon\b", r"\batp\b", r"\bpayne\b"]
    }

    represented_categories = set()
    for article in raw_articles:
        text = (article["title"] + " " + article.get("snippet", "")).lower()
        guessed = "General"
        for cat, patterns in core_topics.items():
            if any(re.search(pat, text) for pat in patterns):
                guessed = cat
                break
        if "Metro Gazette" in article.get("source", ""):
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
        analysis = summarizer.summarize(article['title'], content, article.get('source'))

        
        # Force category to 'Local' if the article is from the metro gazette
        category = "Local" if "Metro Gazette" in article.get("source", "") else analysis["category"]
        
        # Merge analysis back into article dict
        enriched_article = {
            **article,
            "summary": analysis["summary"],
            "category": category,
            "sentiment": analysis["sentiment"]
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
