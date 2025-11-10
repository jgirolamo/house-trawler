"""
Example usage of the UK Property Trawler.
This demonstrates how to use the trawler programmatically.
"""
from trawler import UKPropertyTrawler
from storage import PropertyStorage


def example_basic_usage():
    """Basic example of using the trawler."""
    # Initialize trawler
    trawler = UKPropertyTrawler(delay=2.0)
    
    # Scrape properties
    properties = trawler.scrape_all(
        locations=["London", "Manchester"],
        property_types=["house", "flat"],
        max_pages=3
    )
    
    # Save results
    storage = PropertyStorage(output_dir="output")
    storage.save_to_json(properties, "example_properties.json")
    storage.save_to_csv(properties, "example_properties.csv")
    
    print(f"Found {len(properties)} properties")
    for prop in properties[:3]:  # Show first 3
        print(f"\n{prop.title}")
        print(f"  Price: £{prop.price:,.0f}" if prop.price else "  Price: Not specified")
        print(f"  Address: {prop.address}")
        print(f"  URL: {prop.url}")


def example_custom_scraping():
    """Example of custom scraping for a specific site."""
    trawler = UKPropertyTrawler()
    
    # Example: Scrape from a generic property site
    # Note: You'll need to adapt the selectors based on the actual site structure
    properties = trawler.scrape_generic_site(
        base_url="https://example-property-site.com",
        location="Birmingham",
        property_type="house"
    )
    
    print(f"Scraped {len(properties)} properties from custom site")


if __name__ == "__main__":
    print("Running example usage...")
    example_basic_usage()

