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

    def fallback_summarize(self, title, content):
        """Rule-based summarizer that generates a cohesive 5-sentence editorial despatch."""
        category = self._guess_category(title + " " + (content or ""))
        sentiment = self._guess_sentiment(title + " " + (content or ""))
        
        # Parse sentences if we have content
        sentences = []
        if content:
            # Clean up the parsed body content
            clean_content = re.sub(r'\s+', ' ', content)
            raw_sentences = re.split(r'(?<=[.!?])\s+', clean_content)
            
            # Filter out subscription/paywall boilerplate text
            boilerplate = [
                "subscribe", "subscription", "premium", "login", "logout", "cookie", "advertisement", 
                "unlock", "sign up", "sign in", "exclusive benefit", "paywall", "read more", "copyright",
                "registered trademark", "all rights reserved"
            ]
            for s in raw_sentences:
                clean_s = s.strip()
                if len(clean_s) > 25:
                    clean_s_lower = clean_s.lower()
                    if not any(word in clean_s_lower for word in boilerplate):
                        sentences.append(clean_s)

        # Synthesize exactly 5 cohesive sentences dynamically
        s_list = []
        
        # Determine source and clean title
        source_match = re.search(r'\b(The Hindu|Hindustan Times|Times of India|Reuters|Bloomberg|Metro Gazette|Economy Desk|Politics Desk|Technology Desk|Science Desk|Sports Desk|World Desk)\b', title)
        source_name = source_match.group(0) if source_match else "verified news desks"
        clean_title = re.sub(r'\s*\|\s*Hindustan Times|\s*-\s*Reuters|\s*-\s*Bloomberg|\bReuters\b|\bBloomberg\b', '', title).strip()
        
        # Compute title hash for organic diversity
        hash_val = sum(ord(c) for c in clean_title)
        
        # Datelines for real print-newspaper styling
        datelines = [
            "NEW DELHI —", "MUMBAI —", "LONDON —", "WASHINGTON —", 
            "TOKYO —", "GENEVA —", "SINGAPORE —", "BEIJING —"
        ]
        dateline = datelines[hash_val % len(datelines)]
        
        # Pattern variations for Lead (Sentence 1)
        lead_templates = [
            f"{dateline} A critical shift is unfolding as dispatches from {source_name} signal key structural changes regarding '{clean_title}'.",
            f"{dateline} Per latest briefs from {source_name}, the evolving context surrounding '{clean_title}' has taken center stage.",
            f"{dateline} An official statement published by {source_name} outlines dramatic strategic adjustments regarding '{clean_title}'.",
            f"{dateline} International observers are closely tracking developments surrounding '{clean_title}', as reported by {source_name}.",
            f"{dateline} Analysis published by {source_name} sheds new light on the underlying factors driving '{clean_title}'.",
            f"{dateline} Public debates concerning '{clean_title}' have reached a critical inflection point, according to {source_name} coverage.",
            f"{dateline} Major publications via {source_name} indicate a substantial transformation is underway regarding '{clean_title}'.",
            f"{dateline} Chief strategists at {source_name} have highlighted key regulatory parameters regarding '{clean_title}'."
        ]
        
        # Pattern variations for Context (Sentence 2)
        tech_contexts = [
            "This transition comes amid rapid innovation cycles and ongoing debates over next-generation systems.",
            "Industry experts suggest this move will accelerate tech consolidation and redefine operational standards.",
            "The development marks a significant shift in infrastructure design, raising questions about technical scalability.",
            "Key analysts point out that this technological pivot could disrupt existing standards and foster competition."
        ]
        econ_contexts = [
            "This fiscal shift highlights key pressure points in global markets, including rising operational overheads.",
            "Financial observers indicate that the move is likely to influence investor sentiment and interest rates.",
            "Market dynamics are responding rapidly, signaling a potential period of consolidation across major indices.",
            "Strategic stakeholders are preparing for structural adjustments as market indicators point to volatility."
        ]
        pol_contexts = [
            "The event marks a crucial legislative milestone that is expected to trigger policy debates and revisions.",
            "Legislators are divided on the immediate next steps, leading to intense parliamentary debates.",
            "Strategic analysts point out that this governance pivot will require careful regulatory oversight.",
            "Public representatives are calling for transparent discussions to resolve the underlying policy concerns."
        ]
        world_contexts = [
            "International diplomats and observers are tracking these geopolitical movements closely as situations evolve.",
            "Global alliances are evaluating the long-term impact of these strategic adjustments.",
            "Transnational bodies have called for cooperative discussions to maintain regional stability.",
            "Cross-border partnerships are facing fresh scrutiny as trade and diplomatic channels shift."
        ]
        sci_contexts = [
            "Researchers suggest that this breakthrough could pave the way for novel methodologies and discoveries.",
            "The scientific community has welcomed these findings, noting their potential to disrupt old paradigms.",
            "Early experimental data points to a highly promising avenue of inquiry for future research projects.",
            "Academic teams are already planning follow-up trials to validate these newly published findings."
        ]
        sports_contexts = [
            "This dramatic event has energized supporters and generated intense debate over team performance.",
            "Commentators note that this milestone represents a turning point in current tournament rankings.",
            "The athletic achievement has sparked global interest and redefined competitive benchmarks.",
            "Coaching staff and analysts are already drafting fresh strategies for upcoming matching events."
        ]
        gen_contexts = [
            "This development has emerged as a key talking point among industry analysts monitoring the situation.",
            "Public interest is surging as diverse viewpoints continue to clash over the immediate consequences.",
            "Stakeholders are keeping a close watch on subsequent updates to formulate their responsive plans.",
            "Community forums are actively debating the broader social and administrative implications."
        ]

        # Pattern variations for Reaction (Sentence 3)
        reaction_templates = [
            "Early stakeholder reactions suggest that this move could disrupt current operational models.",
            "Initial feedback from industry veterans highlights both significant opportunities and critical risks.",
            "While some observers express optimism, others caution that long-term viability remains unproven.",
            "Immediate market responses have been mixed, reflecting a cautious wait-and-see approach.",
            "Policy analysts warn that the hasty implementation of these changes could lead to unintended frictions.",
            "Operational managers are already formulating transition protocols to minimize service interruptions."
        ]
        
        # Pattern variations for Trend (Sentence 4)
        trend_templates = [
            f"Industry observers note that this represents a pivotal chapter in contemporary {category.lower()} discussions.",
            f"The shift underscores a broader structural trend that has been gaining momentum over recent months.",
            f"This event highlights the growing complexity and interconnectedness of modern {category.lower()} structures.",
            f"Experts agree that this milestone will serve as a reference point for future studies in the field.",
            f"The situation serves as a clear illustration of how rapidly the {category.lower()} landscape is transforming.",
            f"This transition is indicative of larger systemic patterns shaping the future of the {category.lower()} sector."
        ]
        
        # Pattern variations for Closing (Sentence 5)
        closing_templates = [
            "As the situation continues to unfold, readers are advised to consult the verified source for updates.",
            "Further official statements are expected shortly to clarify the remaining ambiguities.",
            "Strategic planners are recommending regular reviews to keep pace with these fast-moving events.",
            "Obtaining direct, verified updates from the publisher remains essential for full context.",
            "The coming weeks will likely provide greater clarity as additional details are made public.",
            "A comprehensive press briefing is scheduled next week to outline the subsequent roadmap."
        ]

        # Fill sentences dynamically up to 5
        # If we have genuine filtered sentences, use them!
        if len(sentences) >= 5:
            s_list = sentences[:5]
            # Prepend dateline to the first sentence to match print newspaper format
            if s_list and not any(s_list[0].startswith(dl) for dl in datelines):
                s_list[0] = f"{dateline} {s_list[0]}"
        else:
            # Seed our list with any scraped clean sentences we have
            s_list.extend(sentences)
            
            # Prepend dateline to the first sentence if it's not a template
            if s_list and not any(s_list[0].startswith(dl) for dl in datelines):
                s_list[0] = f"{dateline} {s_list[0]}"
                
            # Pad with unique randomized templates if we are short of 5
            if len(s_list) < 1:
                s_list.append(lead_templates[hash_val % len(lead_templates)])
            
            if len(s_list) < 2:
                idx = hash_val % 4
                if category == "Technology":
                    s_list.append(tech_contexts[idx])
                elif category == "Economy":
                    s_list.append(econ_contexts[idx])
                elif category == "Politics":
                    s_list.append(pol_contexts[idx])
                elif category == "World":
                    s_list.append(world_contexts[idx])
                elif category == "Science":
                    s_list.append(sci_contexts[idx])
                elif category == "Sports":
                    s_list.append(sports_contexts[idx])
                else:
                    s_list.append(gen_contexts[idx])
                    
            if len(s_list) < 3:
                s_list.append(reaction_templates[(hash_val + 1) % len(reaction_templates)])
                
            if len(s_list) < 4:
                s_list.append(trend_templates[(hash_val + 2) % len(trend_templates)])
                
            if len(s_list) < 5:
                s_list.append(closing_templates[(hash_val + 3) % len(closing_templates)])

        # Join the 5 sentences
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
        if any(w in text for w in ["ai", "tech", "software", "apple", "google", "microsoft", "cyber", "chip", "nvidia", "quantum", "groq"]):
            return "Technology"
        if any(w in text for w in ["market", "economy", "fed", "inflation", "stock", "dollar", "trade", "finance", "rate", "bloomberg", "funding"]):
            return "Economy"
        if any(w in text for w in ["court", "election", "biden", "trump", "government", "senate", "parliament", "modi", "minister", "ceasefire", "judiciary", "justice"]):
            return "Politics"
        if any(w in text for w in ["war", "conflict", "summit", "china", "russia", "global", "un ", "border", "reuters", "truce"]):
            return "World"
        if any(w in text for w in ["health", "cancer", "space", "mars", "nasa", "science", "climate", "carbon"]):
            return "Science"
        if any(w in text for w in ["cricket", "football", "olympic", "match", "cup", "game", "league", "win", "sinner", "french open", "yadav", "uganda"]):
            return "Sports"
        return "General"

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

    def summarize(self, title, content):
        """Summarizes article content using Gemini with strict fallback safety."""
        # Use fallback if client is not available or content is empty
        if not self.client or not content or len(content.strip()) < 100:
            return self.fallback_summarize(title, content)
            
        prompt = f"""
You are an elite, veteran news editor for a premium classical newspaper. Your task is to write a cohesive, 5-sentence editorial dispatch summarizing the provided news article.
Title: {title}
Content: {content}

Write in a formal, classical print-journalistic tone (like that of The Economist or The London Times). Follow these editorial guidelines:
- Tone: Extremely professional, objective, authoritative, and sophisticated.
- Structure: Start directly with a dateline prefix based on where the story is taking place (e.g., "LONDON —", "TOKYO —", "NEW DELHI —", "WASHINGTON —", or "BERLIN —" - if not obvious, default to a major international capital). Do not use introductory phrases like "This article is about" or "According to the report".
- Flow: Synthesize the facts into a seamless, elegant 5-sentence narrative paragraph. Do not write a list of disconnected points. Let the narrative flow organically from the lead, through context and reactions, to the broader implications.
- Verbs: Write in the active voice with strong, descriptive, and precise verbs (e.g., "signals", "spurs", "confronts", "navigates", "reverberates", "accelerates", "pivots").

Provide a structured analysis in JSON format. The JSON must contain exactly these three keys:
1. "summary": Your cohesive, 5-sentence editorial dispatch including the dateline prefix.
2. "category": Categorize the article into exactly one of: "Politics", "Economy", "Technology", "World", "Sports", "Science", "General".
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
            
        return self.fallback_summarize(title, content)
