# SmartNews Living Canvas

An interactive, AI-powered newsletter application that scrapes top news headlines, processes the article content using Google's Gemini models for high-quality summaries, categorizations, and sentiments, and renders a stunning live canvas frame in Jetro.

## Architecture

The project is structured into three cohesive, independent modules:

1. **`scraper/`**: Downloads top stories and parses the HTML of the main page for links and headlines. It also downloads target articles' raw paragraphs.
2. **`summarizer/`**: Integrates with the `google-genai` SDK using `gemini-2.5-flash` to generate structured JSON summaries, categories, and sentiments. If no API key is present, it elegantly falls back to a rule-based statistical summarizer.
3. **`renderer/`**: Merges Jinja2 template definitions with scraped articles into a highly aesthetic, responsive dark-mode HTML dashboard (`.jetro/frames/newsletter_rendered.html`).

```
SmartNewspaper/
├── .gitignore
├── requirements.txt
├── README.md
├── main.py
├── scraper/
│   ├── __init__.py
│   └── scraper.py
├── summarizer/
│   ├── __init__.py
│   └── summarizer.py
├── renderer/
│   ├── __init__.py
│   └── renderer.py
└── .jetro/
    └── frames/
        ├── newsletter.html           # Source Jinja2 template & UI layout
        └── newsletter_rendered.html  # Processed and compiled UI for Jetro
```

## Setup Instructions

1. **Virtual Environment**:
   A virtual environment (`venv`) has been automatically created, and the required dependencies are installed.

2. **API Keys**:
   To enable AI summarization via Gemini, create a `.env` file in the root directory:
   ```env
   GEMINI_API_KEY=your_gemini_api_key_here
   ```
   If no key is configured, the application will safely execute using its high-quality rule-based statistical summarizer.

3. **Running the Pipeline**:
   Activate the virtual environment and execute the pipeline coordinator:
   ```bash
   venv\Scripts\python.exe main.py
   ```
   You can customize the run with optional parameters:
   - `--limit N`: Customize the maximum number of articles to scrape per site (default: 2).
   - `--offline`: Bypass the Gemini API key check and force offline rule-based summarization.

## Canvas Integration

The front-end is integrated with Jetro to offer a premium living canvas experience:
- **Responsive Category Filtering**: Switch between Technology, Economy, Politics, World, Science, and Sports news instantly.
- **Micro-Animations**: Experience smooth transitions, floating card elevations, glowing category indicators, and custom glassmorphism borders.
- **Self-Updating**: Includes a custom event listener for `jet:refresh` to accept and paint live data streams seamlessly.
- **Details Drawer**: Click on any article card to toggle details and reveal the deep summary without leaving the dashboard.
