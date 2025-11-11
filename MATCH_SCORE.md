# Match Score System

## Overview
The match score system ranks properties from 0-100 based on how well they match your search criteria. Properties are automatically sorted by match score (highest first).

## Scoring Breakdown

### Price Match (30 points max)
- Properties within your price range get points based on how close they are to the ideal price (middle of your range)
- Lower prices get bonus points if only min_price is set
- Properties outside range get fewer points

### Bedrooms Match (20 points max)
- Exact match to your preferred number: 20 points
- Within your range: 15 points
- Outside range but has data: 5 points
- No bedroom data: 2 points

### Bathrooms Match (20 points max)
- Exact match: 20 points
- Within range: 15 points
- Outside range: 5 points
- No data: 2 points

### Garden Match (10 points)
- Required and has garden: 10 points
- Required but unknown: 3 points
- Not required but has garden: 3 bonus points

### Balcony Match (10 points)
- Required and has balcony: 10 points
- Required but unknown: 3 points
- Not required but has balcony: 3 bonus points

### Data Completeness Bonus (10 points)
- Price data: 2 points
- Bedrooms data: 2 points
- Bathrooms data: 2 points
- Image available: 2 points
- Postcode available: 2 points

## Score Ranges
- **70-100**: Excellent match (green indicator)
- **40-69**: Good match (yellow/orange indicator)
- **0-39**: Lower match (red/orange indicator)

## Display
Match scores are shown on each property card with:
- A badge showing the percentage
- A colored progress bar indicating match quality
- Properties are automatically sorted by score (best matches first)

