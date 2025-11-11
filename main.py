"""
Main entry point for the UK Property Trawler.
"""
import json
import os
from trawler import UKPropertyTrawler
from storage import PropertyStorage


def load_config(config_path: str = None) -> dict:
    """Load configuration from JSON file."""
    # Check for temp config from API call
    if config_path is None:
        config_path = os.environ.get('CONFIG_FILE', 'config.json')
    
    if not os.path.exists(config_path):
        print(f"Config file {config_path} not found. Using defaults.")
        return {
            "search_params": {
                "locations": ["London"],
                "property_types": ["house", "flat"],
                "max_pages": 5
            },
            "output_dir": "output",
            "delay_between_requests": 2
        }
    
    with open(config_path, 'r') as f:
        return json.load(f)


def main():
    """Main function to run the property trawler."""
    print("=" * 60)
    print("UK House and Flats Trawler")
    print("=" * 60)
    
    # Load configuration (check for temp config from API)
    config_path = os.environ.get('CONFIG_FILE', 'config.json')
    config = load_config(config_path)
    search_params = config.get("search_params", {})
    output_dir = config.get("output_dir", "output")
    delay = config.get("delay_between_requests", 2)
    
    # Initialize trawler and storage
    trawler = UKPropertyTrawler(delay=delay)
    storage = PropertyStorage(output_dir=output_dir)
    
    # Get search parameters
    locations = search_params.get("locations", ["London"])
    property_types = search_params.get("property_types", ["house", "flat"])
    max_pages = search_params.get("max_pages", 5)
    
    # Get filter parameters
    filters = {
        'min_bedrooms': search_params.get("min_bedrooms"),
        'max_bedrooms': search_params.get("max_bedrooms"),
        'min_bathrooms': search_params.get("min_bathrooms"),
        'max_bathrooms': search_params.get("max_bathrooms"),
        'has_garden': search_params.get("has_garden"),
        'has_balcony': search_params.get("has_balcony"),
        'min_price': search_params.get("min_price"),
        'max_price': search_params.get("max_price"),
        'exclude_student_accommodation': search_params.get("exclude_student_accommodation", False),
        'exclude_house_shares': search_params.get("exclude_house_shares", False),
        'exclude_retirement': search_params.get("exclude_retirement", False),
        'keywords': search_params.get("keywords")
    }
    
    # Remove None values from filters dict (keeps True/False for exclude_ keys, and non-None for others)
    filters = {k: v for k, v in filters.items() if v is not None}
    
    print(f"\nConfiguration:")
    print(f"  Locations: {', '.join(locations)}")
    print(f"  Property Types: {', '.join(property_types)}")
    print(f"  Max Pages: {max_pages}")
    if filters:
        print(f"  Filters: {filters}")
    print(f"  Output Directory: {output_dir}\n")
    
    # Scrape properties
    print("Starting scrape...")
    print("Using real scrapers: Spareroom, OpenRent, Gumtree, OnTheMarket, PrimeLocation\n")
    properties = trawler.scrape_all(
        locations=locations,
        property_types=property_types,
        max_pages=max_pages,
        use_real_scrapers=True,
        filters=filters if filters else None
    )
    
    print(f"\nFound {len(properties)} properties")
    
    # Save results
    if properties:
        storage.save_to_json(properties)
        storage.save_to_csv(properties)
        print("\n[OK] Scraping complete!")
    else:
        print("\n[WARNING] No properties found.")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()

