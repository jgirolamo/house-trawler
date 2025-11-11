# Quick Start Guide

## ✅ Everything is Compiled and Working!

### 🚀 Start the Web Interface

```bash
python app.py
```

Then open: **http://localhost:5000**

### 🔍 Scrape New Properties with Match Scores

```bash
python main.py
```

This will:
- Scrape from OpenRent, OnTheMarket, Spareroom
- Calculate match scores based on your filters
- Sort properties by best matches
- Save to `output/properties.json`

### ⚙️ Configure Your Search

Edit `config.json`:

```json
{
  "search_params": {
    "locations": ["London"],
    "min_price": 1000,
    "max_price": 2000,
    "min_bedrooms": 2,
    "max_bedrooms": 3,
    "has_garden": true,
    "has_balcony": false,
    "exclude_student_accommodation": true,
    "exclude_house_shares": true,
    "exclude_retirement": true
  }
}
```

### ✅ System Status

- ✅ **Property Model**: Includes match_score field
- ✅ **Trawler**: Scrapes, filters, and calculates match scores
- ✅ **Storage**: Saves match scores to JSON/CSV
- ✅ **Web Interface**: Displays match scores with visual indicators
- ✅ **Match Scoring**: 0-100 score based on all criteria
- ✅ **Auto-Sorting**: Best matches appear first

### 🎯 Match Scores

Properties are scored 0-100 based on:
- Price match (30 points)
- Bedrooms match (20 points)
- Bathrooms match (20 points)
- Garden match (10 points)
- Balcony match (10 points)
- Data completeness (10 points)

### 📊 Current Data

- 29 properties available
- 20 from OpenRent
- 7 from Spareroom
- 2 from OnTheMarket

### 🧪 Test the System

```bash
python test_system.py
```

This verifies all components work together.

---

**Everything is ready to use!** 🎉

