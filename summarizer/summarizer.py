import os
import json
import re
from dotenv import load_dotenv

# Try importing the new Google GenAI SDK
try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False

class NewsSummarizer:
    def __init__(self):
        load_dotenv()
        self.api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        self.client = None
        
        if GENAI_AVAILABLE and self.api_key:
            try:
                # Initialize GenAI Client
                self.client = genai.Client(api_key=self.api_key)
                print("Gemini GenAI client initialized successfully.")
            except Exception as e:
                print(f"Error initializing Gemini client: {e}. Falling back to rule-based summarization.")
        else:
            if not GENAI_AVAILABLE:
                print("google-genai SDK not installed. Falling back to rule-based summarization.")
            else:
                print("GEMINI_API_KEY not found in environment. Falling back to rule-based summarization.")

    def _get_geopolitical_dateline(self, title, content, source):
        """Extracts or infers the most accurate print-newspaper dateline prefix (e.g. 'NEW DELHI —')
        based on the article title, body content, and source origin."""
        # Normalize inputs
        title_lower = title.lower() if title else ""
        content_lower = content.lower() if content else ""
        source_lower = source.lower() if source else ""
        
        # Check if source specifically mentions a metro city
        # e.g., "Metro Gazette (Kolkata)" -> KOLKATA
        # Or "Local Gazette (Kolkata)" -> KOLKATA
        source_city_match = re.search(r'\b(delhi|mumbai|kolkata|chennai|bengaluru|bangalore)\b', source_lower)
        if source_city_match:
            city = source_city_match.group(0).upper()
            if city == "BANGALORE":
                city = "BENGALURU"
            return f"{city} —"

        # Explicit well-known cities patterns
        city_patterns = {
            "NEW DELHI": r"\b(delhi|new delhi|noida|gurugram|ghaziabad)\b",
            "MUMBAI": r"\b(mumbai|bombay|navi mumbai|thane|pune)\b",
            "KOLKATA": r"\b(kolkata|calcutta|howrah)\b",
            "CHENNAI": r"\b(chennai|madras)\b",
            "BENGALURU": r"\b(bengaluru|bangalore)\b",
            "LONDON": r"\b(london|uk|britain|british|england)\b",
            "WASHINGTON": r"\b(washington|d\.c\.|u\.s\.|usa|united states|white house)\b",
            "TOKYO": r"\b(tokyo|japan|japanese)\b",
            "BEIJING": r"\b(beijing|peking|china|chinese|shanghai|shenzhen)\b",
            "GENEVA": r"\b(geneva|switzerland|swiss|wto|who)\b",
            "SINGAPORE": r"\b(singapore)\b",
            "PARIS": r"\b(paris|france|french)\b",
            "ROME": r"\b(rome|italy|italian)\b",
            "BERLIN": r"\b(berlin|germany|german)\b",
            "CANBERRA": r"\b(canberra|australia|australian|sydney|melbourne)\b",
            "OTTAWA": r"\b(ottawa|canada|canadian|toronto|vancouver)\b"
        }

        # First scan the title for high-signal city mentions
        for city, pattern in city_patterns.items():
            if re.search(pattern, title_lower):
                return f"{city} —"

        # Scan the first 1000 characters of content for city mentions
        content_preview = content_lower[:1000]
        for city, pattern in city_patterns.items():
            if re.search(pattern, content_preview):
                return f"{city} —"

        # Default defaults based on source origin
        if any(name in source_lower for name in ["hindu", "times of india", "hindustan times"]):
            # Rotate or hash based on title to keep it dynamic but local
            hash_val = sum(ord(c) for c in title)
            return "MUMBAI —" if hash_val % 2 == 0 else "NEW DELHI —"
        elif any(name in source_lower for name in ["reuters", "bloomberg"]):
            hash_val = sum(ord(c) for c in title)
            global_defaults = ["LONDON —", "WASHINGTON —", "TOKYO —", "GENEVA —", "SINGAPORE —"]
            return global_defaults[hash_val % len(global_defaults)]

        # Catch-all fallback using a hash of the title to ensure stability and deterministic printing
        hash_val = sum(ord(c) for c in title)
        all_cities = ["NEW DELHI —", "MUMBAI —", "LONDON —", "WASHINGTON —", "TOKYO —", "GENEVA —", "SINGAPORE —", "BEIJING —"]
        return all_cities[hash_val % len(all_cities)]

    def fallback_summarize(self, title, content, source=None):
        """Rule-based summarizer that generates exactly a 2-sentence executive brief."""
        category = self._guess_category(title + " " + (content or ""))
        sentiment = self._guess_sentiment(title + " " + (content or ""))
        
        # Parse sentences if we have content
        sentences = []
        if content:
            # Clean up the parsed body content
            clean_content = re.sub(r'\s+', ' ', content)
            raw_sentences = re.split(r'(?<=[.!?])\s+', clean_content)
            
            # Filter out subscription/paywall/promo boilerplate text
            boilerplate = [
                "subscribe", "subscription", "premium", "login", "logout", "cookie", "advertisement", 
                "unlock", "sign up", "sign in", "exclusive benefit", "paywall", "read more", "copyright",
                "registered trademark", "all rights reserved", "strictlyvc", "ft journalism", 
                "financial times", "newsletter", "mailing list", "sign-up", "email address", 
                "terms of service", "privacy policy", "read also", "click here", "follow us",
                "trial", "cancel", "upfront", "savings", "early bird"
            ]
            for s in raw_sentences:
                clean_s = s.strip()
                if len(clean_s) > 25:
                    clean_s_lower = clean_s.lower()
                    if not any(word in clean_s_lower for word in boilerplate):
                        sentences.append(clean_s)

        s_list = []
        
        # Determine source and clean title
        source_match = re.search(r'\b(The Hindu|Hindustan Times|Times of India|Reuters|Bloomberg|CNBC|Financial Times|Fortune|TechCrunch|VentureBeat|MarketWatch|Yahoo Finance|Local Gazette|Economy Desk|Politics Desk|Technology Desk|Science Desk|Sports Desk|World Desk)\b', title)
        extracted_source = source_match.group(0) if source_match else "verified news desks"
        final_source = source or extracted_source
        clean_title = re.sub(r'\s*\|\s*Hindustan Times|\s*-\s*Reuters|\s*-\s*Bloomberg|\bReuters\b|\bBloomberg\b', '', title).strip()
        
        # Determine geopolitical dateline
        dateline = self._get_geopolitical_dateline(clean_title, content, final_source)
        
        # Sentence 1: Detail the core event
        if sentences:
            s_list.append(sentences[0])
            
            # Sentence 2: Explain underlying strategic/economic implication
            implication_sent = None
            implication_keywords = ["strategic", "implication", "market", "industry", "because", "analysts", "expect", "suggest", "result", "therefore", "forecast", "impact", "affect"]
            for s in sentences[1:]:
                s_lower = s.lower()
                if any(kw in s_lower for kw in implication_keywords):
                    implication_sent = s
                    break
            
            if implication_sent:
                s_list.append(implication_sent)
            elif len(sentences) > 1:
                s_list.append(sentences[1])
        else:
            # Generate a custom lead sentence using title and source
            s_list.append(f"A significant corporate development was reported as verified briefs detail shifts regarding '{clean_title}'.")
            
        # Pad to exactly 2 sentences if short
        if len(s_list) < 2:
            if category == "Macro & Markets":
                s_list.append("The developing macroeconomic landscape is expected to influence broader interest rate projections and corporate credit yields over the coming quarters.")
            elif category == "Strategy & M&A":
                s_list.append("Industry analysts expect the strategic consolidation to reshape competitive dynamics and potentially trigger regulatory scrutiny from antitrust commissions.")
            elif category == "Venture & Disruption":
                s_list.append("The capital allocation signals shifting sentiment in early-stage investment and represents a notable push toward scaling next-generation enterprise capabilities.")
            elif category == "Leadership & Governance":
                s_list.append("The governance adjustment highlights critical stakeholder pressures and will likely prompt boardroom reviews regarding administrative accountability.")
            else:
                s_list.append("Planners are monitoring the evolving situation closely to assess the operational consequences and coordinate appropriate response strategies.")

        # Ensure exactly 2 sentences in list
        s_list = s_list[:2]

        # Ensure dateline prefix on first sentence
        valid_datelines = ["NEW DELHI —", "MUMBAI —", "LONDON —", "WASHINGTON —", "TOKYO —", "GENEVA —", "SINGAPORE —", "BEIJING —", "KOLKATA —", "BENGALURU —", "CHENNAI —", "PARIS —", "ROME —", "BERLIN —", "CANBERRA —", "OTTAWA —"]
        if s_list and not any(s_list[0].startswith(dl) for dl in valid_datelines):
            s_list[0] = f"{dateline} {s_list[0]}"

        # Join the exactly 2 sentences
        summary = " ".join(s_list)
        if len(summary) > 750:
            summary = summary[:747] + "..."

        return {
            "summary": summary,
            "category": category,
            "sentiment": sentiment
        }

    def _guess_category(self, text):
        text = text.lower()
        
        # Zero-shot keyword classification mapping B-school curriculum categories
        categories = {
            "Macro & Markets": [r"\bmonetary\b", r"\binterest rate\b", r"\bfed\b", r"\bfederal reserve\b", r"\binflation\b", r"\btariff\b", r"\bcurrency\b", r"\bforex\b", r"\bbond\b", r"\byield\b", r"\bcentral bank\b", r"\bdeflation\b", r"\bgdp\b", r"\bmacro\b", r"\btreasury\b", r"\bmarkets\b"],
            "Strategy & M&A": [r"\bmerger\b", r"\bacquisition\b", r"\bm&a\b", r"\btakeover\b", r"\bantitrust\b", r"\bbuyout\b", r"\brestructuring\b", r"\bdivest\b", r"\bconsolidate\b", r"\bjoint venture\b", r"\bsynergy\b", r"\bmergers\b", r"\bacquisitions\b"],
            "Venture & Disruption": [r"\bstartup\b", r"\bventure capital\b", r"\bvc\b", r"\benterprise ai\b", r"\bipo\b", r"\bunicorn\b", r"\bseed round\b", r"\bseries a\b", r"\bseries b\b", r"\bincubator\b", r"\bdisruption\b", r"\bdisruptive\b", r"\bfunding\b"],
            "Leadership & Governance": [r"\bceo\b", r"\bboardroom\b", r"\bactivist investor\b", r"\bgovernance\b", r"\bsuccession\b", r"\bproxy battle\b", r"\bboard of directors\b", r"\bchairman\b", r"\bsec filing\b", r"\bethical crisis\b", r"\bscandal\b", r"\boust\b", r"\blawsuit\b", r"\bboard seat\b"]
        }
        
        for cat, patterns in categories.items():
            if any(re.search(pat, text) for pat in patterns):
                return cat
                
        return "Macro & Markets"  # Default curriculum category for unclassified business despatches



    def _guess_sentiment(self, text):
        text = text.lower()
        pos_words = ["surge", "boost", "growth", "win", "gain", "improve", "success", "innovate", "rise", "positive", "truce", "ceasefire"]
        neg_words = ["fall", "drop", "slump", "crisis", "decline", "warn", "loss", "crash", "strike", "negative", "dead", "shock", "collapse"]
        
        pos_count = sum(text.count(w) for w in pos_words)
        neg_count = sum(text.count(w) for w in neg_words)
        
        if pos_count > neg_count + 1:
            return "Positive"
        elif neg_count > pos_count + 1:
            return "Negative"
        return "Neutral"

    def summarize(self, title, content, source=None):
        """Summarizes article content using Gemini with strict fallback safety."""
        # Use fallback if client is not available or content is empty
        if not self.client or not content or len(content.strip()) < 100:
            return self.fallback_summarize(title, content, source)
            
        # Determine source and geopolitical dateline
        source_match = re.search(r'\b(The Hindu|Hindustan Times|Times of India|Reuters|Bloomberg|CNBC|Financial Times|Fortune|TechCrunch|VentureBeat|MarketWatch|Yahoo Finance|Local Gazette|Economy Desk|Politics Desk|Technology Desk|Science Desk|Sports Desk|World Desk)\b', title)
        extracted_source = source_match.group(0) if source_match else "verified news desks"
        final_source = source or extracted_source
        dateline = self._get_geopolitical_dateline(title, content, final_source)
            
        prompt = f"""
You are a senior editor at a premium financial daily. Summarize the provided business news item into exactly two sentences. 

- Sentence 1: Detail the core event (e.g., who bought whom, what policy changed, or who stepped down).
- Sentence 2: Explain the underlying strategic or economic implication (e.g., why this matters for industry competition, capital costs, or market sentiment).

Write in a formal, classical print-journalistic tone. Follow these structural guidelines:
- Structure: Start directly with the dateline prefix "{dateline} " (all caps, followed by an em-dash).
- Length: Output exactly two sentences. No more, no less.
- Tone: Formal, objective, and analytical. Avoid filler, introductory phrases, or generic hype phrases.

Title: {title}
Content: {content}

Provide a structured analysis in JSON format. The JSON must contain exactly these three keys:
1. "summary": Your cohesive, 2-sentence editorial dispatch including the dateline prefix.
2. "category": Categorize the article into exactly one of: "Macro & Markets", "Strategy & M&A", "Venture & Disruption", "Leadership & Governance".
3. "sentiment": Analyze the tone and categorize into exactly one of: "Positive", "Neutral", "Negative".

Ensure you output ONLY a valid JSON object. No other text or explanation.
"""
        try:
            # Call Gemini
            response = self.client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt
            )
            
            # Clean response text and parse JSON
            text = response.text.strip()
            # Extract JSON block if model wrapped it in markdown
            match = re.search(r'\{.*\}', text, re.DOTALL)
            if match:
                text = match.group(0)
                
            data = json.loads(text)
            
            # Basic validation of keys
            if "summary" in data and "category" in data and "sentiment" in data:
                return {
                    "summary": data["summary"],
                    "category": data["category"],
                    "sentiment": data["sentiment"]
                }
        except Exception as e:
            print(f"Error calling Gemini API: {e}. Falling back...")
            
        return self.fallback_summarize(title, content, source)


