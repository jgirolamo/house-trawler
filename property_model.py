"""
Property data model for UK property listings.
"""
from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class Property:
    """Represents a UK property listing."""
    title: str
    price: Optional[float]
    address: str
    property_type: str  # "house" or "flat"
    bedrooms: Optional[int]
    bathrooms: Optional[int]
    area_sqft: Optional[float]
    description: str
    url: str
    source: str  # Website name
    listed_date: Optional[str]
    location: str
    postcode: Optional[str]
    has_garden: Optional[bool] = None
    has_balcony: Optional[bool] = None
    image_url: Optional[str] = None
    match_score: Optional[float] = None  # Score from 0-100 indicating how well it matches search criteria
    
    def to_dict(self) -> dict:
        """Convert property to dictionary for JSON/CSV export."""
        return {
            "title": self.title,
            "price": self.price,
            "address": self.address,
            "property_type": self.property_type,
            "bedrooms": self.bedrooms,
            "bathrooms": self.bathrooms,
            "area_sqft": self.area_sqft,
            "description": self.description[:500] if self.description else "",  # Truncate long descriptions
            "url": self.url,
            "source": self.source,
            "listed_date": self.listed_date,
            "location": self.location,
            "postcode": self.postcode,
            "has_garden": self.has_garden,
            "has_balcony": self.has_balcony,
            "image_url": self.image_url,
            "match_score": self.match_score,
            "scraped_at": datetime.now().isoformat()
        }

