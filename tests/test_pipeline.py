import unittest
from summarizer.summarizer import NewsSummarizer
from scraper.scraper import NewsScraper

class TestSmartNewspaperPipeline(unittest.TestCase):
    def setUp(self):
        self.summarizer = NewsSummarizer()
        self.scraper = NewsScraper()

    def test_curriculum_category_classification(self):
        # 1. Macro & Markets
        text_macro = "Federal Reserve signals potential interest rate hikes as inflation measures rise."
        category = self.summarizer._guess_category(text_macro)
        self.assertEqual(category, "Macro & Markets")

        # 2. Strategy & M&A
        text_strategy = "Computing giant completes asset acquisition of tech firm for valuation of 4.2 billion."
        category = self.summarizer._guess_category(text_strategy)
        self.assertEqual(category, "Strategy & M&A")

        # 3. Venture & Disruption
        text_venture = "Enterprise AI startup raising series A funding from prominent venture capital firms."
        category = self.summarizer._guess_category(text_venture)
        self.assertEqual(category, "Venture & Disruption")

        # 4. Leadership & Governance
        text_leadership = "Activist investor wins boardroom seats after board proxy battle ousts current CEO."
        category = self.summarizer._guess_category(text_leadership)
        self.assertEqual(category, "Leadership & Governance")

    def test_two_sentence_brief_summarization(self):
        # Test that offline summaries are exactly two sentences
        content = "Monetary policy shifts are unfolding as the Fed signals interest rates adjustments. Central bank governors indicate this will curb inflation costs. Planners suggest it could affect short-term credit yields across markets."
        analysis = self.summarizer.fallback_summarize(
            title="Fed Interest Rates Update",
            content=content,
            source="CNBC"
        )
        summary = analysis["summary"]
        
        # Strip dateline prefix if any for sentence count check
        clean_summary = summary.split(" — ", 1)[-1]
        sentences = [s.strip() for s in clean_summary.split(".") if s.strip()]
        self.assertEqual(len(sentences), 2)
        
        # Test strategic implication fallback when body is short
        analysis_short = self.summarizer.fallback_summarize(
            title="CEO Boardroom succession",
            content="A boardroom succession is occurring.",
            source="Fortune"
        )
        clean_summary_short = analysis_short["summary"].split(" — ", 1)[-1]
        sentences_short = [s.strip() for s in clean_summary_short.split(".") if s.strip()]
        self.assertEqual(len(sentences_short), 2)

    def test_geopolitical_dateline_extraction(self):
        # 1. Match from source name
        dateline_source = self.summarizer._get_geopolitical_dateline(
            title="Startup trends",
            content="Active funding rounds.",
            source="Metro Gazette (Kolkata)"
        )
        self.assertEqual(dateline_source, "KOLKATA —")

        # 2. Match from title
        dateline_title = self.summarizer._get_geopolitical_dateline(
            title="Tokyo braces for currency fluctuations",
            content="Central bankers meet today.",
            source="Reuters"
        )
        self.assertEqual(dateline_title, "TOKYO —")

if __name__ == "__main__":
    unittest.main()
