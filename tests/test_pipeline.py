import unittest
from summarizer.summarizer import NewsSummarizer
from scraper.scraper import NewsScraper

class TestSmartNewspaperPipeline(unittest.TestCase):
    def setUp(self):
        self.summarizer = NewsSummarizer()
        self.scraper = NewsScraper()

    def test_regex_category_classification(self):
        # 1. Test Sports Headline (Previously miscategorized as Technology due to "mumbai" containing "ai")
        headline_sports = "Hardik Pandya: India's ‘Clutch God’ who fades for Mumbai Indians"
        category = self.summarizer._guess_category(headline_sports)
        self.assertEqual(category, "Sports")

        # 2. Test Home Affairs / Political Headline (Previously miscategorized as Economy due to "private" containing "rate")
        headline_politics = "Kerala private bus industry ignored in policy address, say operators"
        category = self.summarizer._guess_category(headline_politics)
        self.assertNotEqual(category, "Economy")
        self.assertEqual(category, "Politics")

        # 3. Test Technology Headline
        headline_tech = "Groq raising up to $650 million from existing investors to build next-generation AI chips"
        category = self.summarizer._guess_category(headline_tech)
        self.assertEqual(category, "Technology")

    def test_geopolitical_dateline_extraction(self):
        # 1. Match from source name
        dateline_source = self.summarizer._get_geopolitical_dateline(
            title="Local protest reports",
            content="Heavy traffic was reported due to rallies.",
            source="Local Gazette (Kolkata)"
        )
        self.assertEqual(dateline_source, "KOLKATA —")

        # 2. Match from title
        dateline_title = self.summarizer._get_geopolitical_dateline(
            title="Tokyo braces for record-breaking heatwave",
            content="Temperatures are expected to soar above 40 degrees.",
            source="Reuters"
        )
        self.assertEqual(dateline_title, "TOKYO —")

        # 3. Match from content body
        dateline_content = self.summarizer._get_geopolitical_dateline(
            title="WTO chief urges trade model shifts",
            content="The head of the World Trade Organization speaking in Geneva today urged member states to reform tariff structures.",
            source="Bloomberg"
        )
        self.assertEqual(dateline_content, "GENEVA —")

        # 4. Default by source origin (Indian source)
        dateline_default_india = self.summarizer._get_geopolitical_dateline(
            title="Supreme Court introduces nationwide judicial timelines",
            content="The high court has set a three-month deadline for judgments.",
            source="The Hindu"
        )
        self.assertIn(dateline_default_india, ["NEW DELHI —", "MUMBAI —"])

        # 5. Default by source origin (Global source)
        dateline_default_global = self.summarizer._get_geopolitical_dateline(
            title="Oil Spikes as Renewed Gulf Attacks Threaten Fragile Ceasefire",
            content="Markets reacted sharply with crude futures jumping over three percent.",
            source="Bloomberg"
        )
        self.assertIn(dateline_default_global, ["LONDON —", "WASHINGTON —", "TOKYO —", "GENEVA —", "SINGAPORE —"])

if __name__ == "__main__":
    unittest.main()
