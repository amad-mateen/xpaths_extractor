# Web Element ID & XPath Extractor

A Flask web application to extract element IDs, classes, CSS selectors, and XPaths from any public webpage. Supports both static and dynamic (JavaScript-rendered) pages using requests/lxml or Selenium.

## Features
- Extracts element IDs, classes, names, styles, titles, CSS selectors, and XPaths
- Supports static extraction (requests + lxml) and dynamic extraction (Selenium)
- Displays element type (button, input, link, etc.) and value/text
- Option to skip SSL verification
- Filter results to only named IDs
- Web UI and REST API endpoint

## How It Works
- **Static Mode:** Fetches HTML and parses with lxml
- **Dynamic Mode:** Uses Selenium (headless Chrome) to render and extract elements
- Results include detailed attributes and selectors for each element

## Requirements
- Python 3.8+
- Flask
- lxml
- requests
- selenium
- Chrome browser and chromedriver (for dynamic mode)

Install dependencies:
```bash
pip install flask lxml requests selenium
```

## Usage
1. Start the Flask app:
    ```bash
    python app.py
    ```
2. Open your browser at [http://localhost:5000](http://localhost:5000)
3. Enter a webpage URL and choose extraction mode (static/dynamic)
4. View and copy element details (ID, class, CSS selector, XPath, etc.)

## API
POST `/api/extract`
- Request JSON: `{ "url": "https://example.com", "skip_ssl": false }`
- Response: `{ "results": [...] }`

## Notes
- Dynamic mode requires Chrome and chromedriver installed and in PATH
- For best results, use dynamic mode for JavaScript-heavy pages
- SSL errors can be skipped with the checkbox

## License
MIT

## Author
amad-mateen
