# UK House and Flats Trawler

A web scraper for finding houses and flats across the UK. This tool searches multiple property websites and collects listing information.

## Features

- Scrapes property listings from UK property websites
- Supports both houses and flats
- Configurable search parameters (location, price range, property type)
- Exports data to CSV and JSON formats
- Modern, extensible architecture

## Installation

1. Install Python 3.8 or higher
2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Configure your search parameters in `config.json`
2. Run the trawler:
```bash
python main.py
```

3. Results will be saved in the `output/` directory

## Configuration

Edit `config.json` to customize:
- Search locations
- Price ranges
- Property types (house/flat)
- Number of pages to scrape

## Output

Results are saved as:
- `output/properties.csv` - CSV format for spreadsheet analysis
- `output/properties.json` - JSON format for programmatic use

## Web Interface

Start the web server to view scraped properties in a browser:

```bash
python app.py
```

Then open http://localhost:5000 in your browser.

## Free Deployment Options

The application can be deployed for **FREE** on several platforms:

### 🚀 Quick Deploy (Recommended: Render.com)

1. **Push to GitHub** (if not already done)
2. Go to https://render.com and sign up with GitHub
3. Click "New +" → "Web Service"
4. Connect your repository
5. Render will auto-detect using `render.yaml`
6. Click "Create Web Service"
7. Your app will be live in ~2 minutes!

**Your app URL**: `https://your-app-name.onrender.com`

### Other Free Options:
- **Railway.app** - $5 free credit/month (very fast)
- **Fly.io** - 3 free VMs (good performance)
- **PythonAnywhere** - Free tier available
- **Replit** - Very easy, good for learning

See `DEPLOYMENT.md` for detailed instructions on all platforms.

## Deployment

### Railway
1. Connect your GitHub repository
2. Railway will auto-detect and deploy using `railway.json`

### Render
1. Create a new Web Service
2. Connect your repository
3. Render will use `render.yaml` for configuration

### Heroku
1. Install Heroku CLI
2. Run: `heroku create`
3. Deploy: `git push heroku main`

### Docker
```bash
docker build -t property-trawler .
docker run -p 5000:5000 property-trawler
```

### Environment Variables
- `PORT` - Server port (default: 5000)
- `HOST` - Server host (default: 127.0.0.1)
- `FLASK_DEBUG` - Debug mode (default: True)

## Legal Notice

Please ensure you comply with the terms of service of the websites you're scraping. This tool is for educational purposes. Always respect robots.txt and rate limits.

