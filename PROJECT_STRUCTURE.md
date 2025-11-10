# Project Structure

```
house-trawler/
├── app.py                 # Flask web application
├── main.py               # Main trawler script
├── trawler.py            # Core scraping logic
├── property_model.py     # Property data model
├── storage.py            # Data storage handlers
├── config.json           # Configuration file
├── requirements.txt      # Python dependencies
├── README.md             # Main documentation
├── DEPLOYMENT.md         # Deployment instructions
├── QUICK_DEPLOY.md       # Quick deploy guide
├── WEBSITES_STATUS.md    # Website scraper status
├── templates/
│   └── index.html        # Web interface template
├── output/               # Scraped data (gitignored)
│   ├── .gitkeep
│   ├── properties.json
│   └── properties.csv
├── .gitignore           # Git ignore rules
├── .gitattributes       # Git attributes
├── Procfile             # For Heroku/Railway
├── runtime.txt          # Python version
├── render.yaml          # Render.com config
├── railway.json         # Railway.app config
└── Dockerfile           # Docker configuration
```

## Key Files

- **app.py**: Web server for viewing properties
- **main.py**: Command-line interface for scraping
- **trawler.py**: All scraping logic and website scrapers
- **config.json**: Search parameters and filters
- **templates/index.html**: Web UI with filters and property cards

## Output Files

The `output/` directory contains scraped data:
- `properties.json`: All properties in JSON format
- `properties.csv`: All properties in CSV format

These files are gitignored but the directory structure is preserved.

