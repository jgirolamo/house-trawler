"""
Main trawler class for scraping UK property websites.
"""
import time
import re
import requests
from bs4 import BeautifulSoup
from typing import List, Optional
from urllib.parse import quote, urljoin
from property_model import Property


class UKPropertyTrawler:
    """Scrapes property listings from UK property websites."""
    
    def __init__(self, delay: float = 2.0):
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def _extract_price(self, text: str) -> Optional[float]:
        """Extract price from text string."""
        if not text:
            return None
        
        # Look for price patterns like £1,234 or £1234
        # Match the first reasonable price (not concatenated numbers)
        price_patterns = [
            r'£\s*([\d,]+)\s*(?:pcm|per month|pm)',  # Monthly rent
            r'£\s*([\d,]+)\s*(?:pw|per week)',  # Weekly rent (convert to monthly: * 52 / 12)
            r'£\s*([\d,]+)',  # Any price
        ]
        
        for pattern in price_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    price_str = match.group(1).replace(',', '')
                    price = float(price_str)
                    # If it's weekly, convert to monthly (approximate)
                    if 'pw' in text.lower() or 'per week' in text.lower():
                        price = price * 52 / 12
                    # Sanity check: prices should be reasonable (between 100 and 10,000,000)
                    if 100 <= price <= 10000000:
                        return price
                except (ValueError, IndexError):
                    continue
        
        return None
    
    def _extract_bedrooms(self, text: str) -> Optional[int]:
        """Extract number of bedrooms from text."""
        if not text:
            return None
        
        # Look for patterns like "2 bed", "3 bedrooms", etc.
        match = re.search(r'(\d+)\s*(?:bed|bedroom)', text.lower())
        if match:
            try:
                return int(match.group(1))
            except ValueError:
                return None
        return None
    
    def _extract_bathrooms(self, text: str) -> Optional[int]:
        """Extract number of bathrooms from text."""
        if not text:
            return None
        
        match = re.search(r'(\d+)\s*(?:bath|bathroom)', text.lower())
        if match:
            try:
                return int(match.group(1))
            except ValueError:
                return None
        return None
    
    def _extract_garden(self, text: str) -> Optional[bool]:
        """Extract whether property has a garden."""
        if not text:
            return None
        
        text_lower = text.lower()
        # Positive indicators
        garden_indicators = [
            r'\bgarden\b',
            r'\bprivate garden\b',
            r'\bshared garden\b',
            r'\boutdoor space\b',
            r'\bpatio\b',
            r'\bterrace\b',
            r'\byard\b',
            r'\bcourtyard\b'
        ]
        
        for pattern in garden_indicators:
            if re.search(pattern, text_lower):
                return True
        
        # Negative indicators (explicitly states no garden)
        no_garden_indicators = [
            r'no garden',
            r'without garden',
            r'no outdoor space'
        ]
        
        for pattern in no_garden_indicators:
            if re.search(pattern, text_lower):
                return False
        
        return None
    
    def _extract_balcony(self, text: str) -> Optional[bool]:
        """Extract whether property has a balcony."""
        if not text:
            return None
        
        text_lower = text.lower()
        # Positive indicators
        balcony_indicators = [
            r'\bbalcony\b',
            r'\bbalconies\b',
            r'\bprivate balcony\b',
            r'\bshared balcony\b',
            r'\bterrace\b'
        ]
        
        for pattern in balcony_indicators:
            if re.search(pattern, text_lower):
                return True
        
        # Negative indicators
        no_balcony_indicators = [
            r'no balcony',
            r'without balcony'
        ]
        
        for pattern in no_balcony_indicators:
            if re.search(pattern, text_lower):
                return False
        
        return None
    
    def _is_student_accommodation(self, text: str) -> bool:
        """Detect if property is student accommodation."""
        if not text:
            return False
        
        text_lower = text.lower()
        student_indicators = [
            r'\bstudent\b',
            r'\bstudent accommodation\b',
            r'\bstudent housing\b',
            r'\bstudent flat\b',
            r'\bstudent room\b',
            r'\buniversity accommodation\b',
            r'\bhall of residence\b',
            r'\bstudent halls\b',
            r'\bstudent let\b',
            r'\bstudent property\b',
            r'\bfor students\b',
            r'\bstudent only\b'
        ]
        
        for pattern in student_indicators:
            if re.search(pattern, text_lower):
                return True
        
        return False
    
    def _is_house_share(self, text: str) -> bool:
        """Detect if property is a house share."""
        if not text:
            return False
        
        text_lower = text.lower()
        house_share_indicators = [
            r'\bhouse share\b',
            r'\bhouse sharing\b',
            r'\bshared house\b',
            r'\bshare house\b',
            r'\broom in shared house\b',
            r'\bshared accommodation\b',
            r'\broom to rent\b',
            r'\bsingle room\b',
            r'\bdouble room\b',
            r'\broom available\b',
            r'\broom for rent\b',
            r'\bshare of\b',
            r'\bsharing with\b'
        ]
        
        for pattern in house_share_indicators:
            if re.search(pattern, text_lower):
                return True
        
        return False
    
    def _is_retirement_property(self, text: str) -> bool:
        """Detect if property is retirement accommodation."""
        if not text:
            return False
        
        text_lower = text.lower()
        retirement_indicators = [
            r'\bretirement\b',
            r'\bretirement property\b',
            r'\bretirement flat\b',
            r'\bretirement home\b',
            r'\bretirement housing\b',
            r'\bover 55\b',
            r'\bover 60\b',
            r'\bover 65\b',
            r'\bage restricted\b',
            r'\bsenior living\b',
            r'\bsheltered accommodation\b',
            r'\bretirement village\b',
            r'\bretirement community\b'
        ]
        
        for pattern in retirement_indicators:
            if re.search(pattern, text_lower):
                return True
        
        return False
    
    def _extract_postcode(self, text: str) -> Optional[str]:
        """Extract UK postcode from text."""
        if not text:
            return None
        
        # UK postcode pattern
        postcode_pattern = r'([A-Z]{1,2}\d{1,2}[A-Z]?\s?\d[A-Z]{2})'
        match = re.search(postcode_pattern, text.upper())
        if match:
            return match.group(1)
        return None
    
    def _extract_image_url(self, listing, base_url: str) -> Optional[str]:
        """Extract first image URL from a listing element."""
        if not listing:
            return None
        
        # Try multiple common image selectors
        img_elem = (
            listing.find('img', src=True) or
            listing.find('img', {'data-src': True}) or
            listing.find('img', {'data-lazy': True}) or
            listing.find('div', class_=re.compile(r'image|photo|picture|thumbnail', re.I)) or
            None
        )
        
        if img_elem:
            # Try different src attributes
            img_url = (
                img_elem.get('src') or
                img_elem.get('data-src') or
                img_elem.get('data-lazy') or
                img_elem.get('data-original')
            )
            
            if img_url:
                # Handle relative URLs
                if img_url.startswith('http'):
                    return img_url
                elif img_url.startswith('//'):
                    return 'https:' + img_url
                elif img_url.startswith('/'):
                    return urljoin(base_url, img_url)
                else:
                    return urljoin(base_url, '/' + img_url)
        
        # Try to find image in background style
        style_elem = listing.find(['div', 'span'], style=re.compile(r'background.*url', re.I))
        if style_elem:
            style = style_elem.get('style', '')
            url_match = re.search(r'url\(["\']?([^"\']+)["\']?\)', style)
            if url_match:
                img_url = url_match.group(1)
                if img_url.startswith('http'):
                    return img_url
                else:
                    return urljoin(base_url, img_url)
        
        return None
    
    def scrape_rightmove(self, location: str, property_type: str, max_pages: int = 5) -> List[Property]:
        """
        Scrape Rightmove (example implementation - note: Rightmove has strict anti-scraping).
        This is a template that would need to be adapted based on actual site structure.
        """
        properties = []
        print(f"Note: Rightmove scraping requires careful implementation due to anti-scraping measures.")
        print(f"Consider using their API or official data feeds if available.")
        return properties
    
    def scrape_zoopla(self, location: str, property_type: str, max_pages: int = 5) -> List[Property]:
        """
        Scrape Zoopla (example implementation).
        Note: Real implementation would need to handle their actual HTML structure.
        """
        properties = []
        print(f"Note: Zoopla scraping requires careful implementation due to anti-scraping measures.")
        return properties
    
    def scrape_spareroom(self, location: str, property_type: str = "whole property", max_pages: int = 5) -> List[Property]:
        """
        Scrape Spareroom for whole properties.
        Searches for whole properties suitable for sharing.
        """
        properties = []
        print(f"Scraping Spareroom for whole properties in {location}...")
        
        try:
            # Spareroom search URL for whole properties
            base_url = "https://www.spareroom.co.uk"
            # Try different URL formats
            search_urls = [
                f"{base_url}/flatshare/?search_id=&flatshare_type=whole_property&search={quote(location)}",
                f"{base_url}/flatshare/flatshare.pl?search_id=&action=search&flatshare_type=whole_property&search={quote(location)}",
                f"{base_url}/flatshare/?search={quote(location)}&flatshare_type=whole_property"
            ]
            
            response = None
            for search_url in search_urls:
                try:
                    response = self.session.get(search_url, timeout=15, allow_redirects=True)
                    if response.status_code == 200:
                        break
                except:
                    continue
            
            if not response or response.status_code != 200:
                print(f"  Could not access Spareroom (tried {len(search_urls)} URL formats)")
                return properties
            
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Try multiple possible selectors for property listings
            listings = (
                soup.find_all('article', class_='listing-result') or
                soup.find_all('li', class_='listing-result') or
                soup.find_all('div', class_='listing-result') or
                soup.find_all('div', {'data-listing-id': True}) or
                soup.find_all('article') or
                []
            )
            
            if not listings:
                # Try finding any elements with property-like content
                listings = soup.find_all(['div', 'article', 'li'], class_=re.compile(r'listing|property|result', re.I))
            
            print(f"  Found {len(listings)} potential listings on Spareroom")
            
            for listing in listings[:20]:  # Limit to first 20 to avoid too many
                try:
                    # Try to find title/link
                    title_elem = (
                        listing.find('a', class_=re.compile(r'title|heading|name', re.I)) or
                        listing.find('h2') or
                        listing.find('h3') or
                        listing.find('a', href=True)
                    )
                    
                    if not title_elem:
                        continue
                    
                    title = title_elem.get_text(strip=True)
                    if not title or len(title) < 5:
                        continue
                    
                    # Get URL
                    link_elem = listing.find('a', href=True)
                    url = urljoin(base_url, link_elem['href']) if link_elem else ""
                    
                    # Try to find price
                    price_elem = (
                        listing.find('span', class_=re.compile(r'price|rent', re.I)) or
                        listing.find('div', class_=re.compile(r'price|rent', re.I)) or
                        listing.find(string=re.compile(r'£'))
                    )
                    
                    price_text = ""
                    if price_elem:
                        if isinstance(price_elem, str):
                            price_text = price_elem
                        else:
                            price_text = price_elem.get_text(strip=True)
                    
                    # Try to find address/location
                    address_elem = (
                        listing.find('span', class_=re.compile(r'location|address|area', re.I)) or
                        listing.find('div', class_=re.compile(r'location|address|area', re.I)) or
                        listing.find('p', class_=re.compile(r'location|address', re.I))
                    )
                    
                    address = location
                    if address_elem:
                        address = address_elem.get_text(strip=True)
                    
                    # Extract description
                    desc_elem = listing.find('p', class_=re.compile(r'description|summary', re.I))
                    description = title
                    if desc_elem:
                        description = desc_elem.get_text(strip=True)
                    
                    # Extract all text for bedroom/bathroom info
                    all_text = listing.get_text()
                    
                    price = self._extract_price(price_text or all_text)
                    bedrooms = self._extract_bedrooms(all_text or title)
                    bathrooms = self._extract_bathrooms(all_text or title)
                    has_garden = self._extract_garden(all_text or description or title)
                    has_balcony = self._extract_balcony(all_text or description or title)
                    
                    # Determine property type
                    prop_type = "flat" if any(word in title.lower() for word in ["flat", "apartment"]) else "house"
                    
                    property_obj = Property(
                        title=title,
                        price=price,
                        address=address,
                        property_type=prop_type,
                        bedrooms=bedrooms,
                        bathrooms=bathrooms,
                        area_sqft=None,
                        description=description[:500] if description else title,
                        url=url,
                        source="Spareroom",
                        listed_date=None,
                        location=location,
                        postcode=self._extract_postcode(address),
                        has_garden=has_garden,
                        has_balcony=has_balcony,
                        image_url=self._extract_image_url(listing, base_url)
                    )
                
                properties.append(property_obj)
                
                except Exception as e:
                    print(f"    Error parsing Spareroom listing: {e}")
                    continue
            
            time.sleep(self.delay)
            
        except Exception as e:
            print(f"  Error scraping Spareroom: {e}")
        
        return properties
    
    def scrape_openrent(self, location: str, property_type: str = "house", max_pages: int = 5) -> List[Property]:
        """
        Scrape OpenRent for rental properties.
        """
        properties = []
        print(f"Scraping OpenRent for {property_type}s in {location}...")
        
        try:
            # OpenRent search URL
            base_url = "https://www.openrent.co.uk"
            # OpenRent uses a search endpoint
            search_url = f"{base_url}/properties-to-rent?term={quote(location)}"
            
            response = self.session.get(search_url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Try multiple possible selectors for OpenRent listings
            listings = (
                soup.find_all('div', class_=re.compile(r'property|listing|result', re.I)) or
                soup.find_all('article') or
                soup.find_all('div', {'data-property-id': True}) or
                soup.find_all('a', href=re.compile(r'/properties/', re.I)) or
                []
            )
            
            if not listings:
                # Try finding property cards
                listings = soup.find_all(['div', 'article'], class_=re.compile(r'card|item|box', re.I))
            
            print(f"  Found {len(listings)} potential listings on OpenRent")
            
            extracted_count = 0
            for listing in listings[:30]:  # Increase limit to 30
                try:
                    # Extract all text first for better parsing
                    all_text = listing.get_text(separator=' ', strip=True)
                    
                    # Skip if too short
                    if len(all_text) < 5:
                        continue
                    
                    # Try to find title - be more flexible
                    title_elem = None
                    title = None
                    
                    # First try headings
                    for selector in ['h2', 'h3', 'h4', 'h1']:
                        elem = listing.find(selector)
                        if elem:
                            text = elem.get_text(strip=True)
                            if text and len(text) >= 5:
                                title_elem = elem
                                title = text
                                break
                    
                    # If no heading, try links
                    if not title_elem:
                        links = listing.find_all('a', href=re.compile(r'/properties?/', re.I))
                        for link in links:
                            text = link.get_text(strip=True)
                            if text and len(text) >= 5:
                                title_elem = link
                                title = text
                                break
                    
                    # If still no title, try any link or use first meaningful text
                    if not title_elem:
                        link = listing.find('a', href=True)
                        if link:
                            text = link.get_text(strip=True)
                            if text and len(text) >= 5:
                                title_elem = link
                                title = text
                    
                    # Last resort: use first non-empty text element
                    if not title_elem:
                        # Get first meaningful text from the listing
                        for tag in ['div', 'span', 'p']:
                            elem = listing.find(tag)
                            if elem:
                                text = elem.get_text(strip=True)
                                if text and len(text) >= 10:
                                    title = text[:100]  # Limit length
                                    break
                    
                    if not title or len(title) < 5:
                        continue
                    
                    # Clean up title - remove excessive price info but keep it if it's the main content
                    if title_elem:
                        title = title_elem.get_text(strip=True)
                    
                    # Skip if title is just a price (common pattern: "£1,234per month")
                    if re.match(r'^£[\d,]+\s*(?:pcm|per month|pw|per week)', title, re.I):
                        # This is just a price, try to find a better title
                        # Look for address or location in the listing
                        addr_elem = listing.find(['span', 'div', 'p'], class_=re.compile(r'location|address|area', re.I))
                        if addr_elem:
                            title = addr_elem.get_text(strip=True)
                        else:
                            # Try to extract meaningful text that's not just price
                            text_parts = all_text.split()
                            for i, part in enumerate(text_parts):
                                if not re.match(r'^£[\d,]+', part) and len(part) > 3:
                                    # Found a non-price word, use it and surrounding words
                                    start = max(0, i-2)
                                    end = min(len(text_parts), i+5)
                                    title = ' '.join(text_parts[start:end])
                                    break
                    
                    # Only remove price suffix if title is long enough
                    if len(title) > 20:
                        title = re.sub(r'£[\d,]+\s*(?:pcm|per month|pw|per week)', '', title, flags=re.I).strip()
                    
                    # Final validation - skip if still just a price or too short
                    if not title or len(title) < 5 or re.match(r'^£[\d,]+', title.strip()):
                        continue
                    
                    # Get URL
                    link_elem = listing.find('a', href=re.compile(r'/properties?/', re.I))
                    if not link_elem and title_elem.name == 'a':
                        link_elem = title_elem
                    
                    url = ""
                    if link_elem and link_elem.get('href'):
                        url = urljoin(base_url, link_elem['href'])
                    
                    # Extract price from all text (better extraction)
                    price = self._extract_price(all_text)
                    
                    # Try to find address - look for location patterns
                    address = location
                    # Look for postcodes or area names in the text
                    postcode_match = self._extract_postcode(all_text)
                    if postcode_match:
                        address = postcode_match
                    else:
                        # Try to find address elements
                        address_elem = (
                            listing.find('span', class_=re.compile(r'location|address|area', re.I)) or
                            listing.find('div', class_=re.compile(r'location|address', re.I)) or
                            listing.find('p', class_=re.compile(r'location|address', re.I))
                        )
                        if address_elem:
                            addr_text = address_elem.get_text(strip=True)
                            if addr_text and len(addr_text) > 3:
                                address = addr_text
                    
                    # Extract description - get first paragraph or summary
                    desc_elem = listing.find('p', class_=re.compile(r'description|summary', re.I))
                    description = title
                    if desc_elem:
                        desc_text = desc_elem.get_text(strip=True)
                        if desc_text and len(desc_text) > len(title):
                            description = desc_text
                    
                    bedrooms = self._extract_bedrooms(all_text or title)
                    bathrooms = self._extract_bathrooms(all_text or title)
                    has_garden = self._extract_garden(all_text or description or title)
                    has_balcony = self._extract_balcony(all_text or description or title)
                    image_url = self._extract_image_url(listing, base_url)
                    
                    # Determine property type from title and description
                    combined_text = (title + " " + description).lower()
                    prop_type = "flat" if any(word in combined_text for word in ["flat", "apartment", "apartment"]) else "house"
                    
                    property_obj = Property(
                        title=title,
                        price=price,
                        address=address,
                        property_type=prop_type,
                        bedrooms=bedrooms,
                        bathrooms=bathrooms,
                        area_sqft=None,
                        description=description[:500] if description else title,
                        url=url,
                        source="OpenRent",
                        listed_date=None,
                        location=location,
                        postcode=self._extract_postcode(address),
                        has_garden=has_garden,
                        has_balcony=has_balcony,
                        image_url=image_url
                    )
                    
                    properties.append(property_obj)
                    
                except Exception as e:
                    print(f"    Error parsing OpenRent listing: {e}")
                    continue
            
            time.sleep(self.delay)
            
        except Exception as e:
            print(f"  Error scraping OpenRent: {e}")
        
        return properties
    
    def scrape_gumtree(self, location: str, property_type: str = "house", max_pages: int = 5) -> List[Property]:
        """
        Scrape Gumtree for property listings.
        """
        properties = []
        print(f"Scraping Gumtree for {property_type}s in {location}...")
        
        try:
            base_url = "https://www.gumtree.com"
            # Gumtree property search URL
            search_url = f"{base_url}/property-for-rent/uk/{quote(location)}"
            
            response = self.session.get(search_url, timeout=15, allow_redirects=True)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Try multiple selectors for Gumtree listings
            listings = (
                soup.find_all('article', class_=re.compile(r'listing|result|item', re.I)) or
                soup.find_all('div', class_=re.compile(r'listing|result|item', re.I)) or
                soup.find_all('a', href=re.compile(r'/property-for-rent/', re.I)) or
                soup.find_all('li', class_=re.compile(r'listing|result', re.I)) or
                []
            )
            
            if not listings:
                listings = soup.find_all(['div', 'article', 'li'], class_=re.compile(r'card|box|tile', re.I))
            
            print(f"  Found {len(listings)} potential listings on Gumtree")
            
            for listing in listings[:25]:
                try:
                    all_text = listing.get_text(separator=' ', strip=True)
                    if len(all_text) < 5:
                        continue
                    
                    # Find title
                    title_elem = (
                        listing.find('h2') or
                        listing.find('h3') or
                        listing.find('a', class_=re.compile(r'title|name|heading', re.I)) or
                        listing.find('a', href=True)
                    )
                    
                    if not title_elem:
                        continue
                    
                    title = title_elem.get_text(strip=True)
                    if not title or len(title) < 5:
                        continue
                    
                    # Get URL
                    link_elem = listing.find('a', href=True)
                    url = ""
                    if link_elem:
                        href = link_elem.get('href', '')
                        if href.startswith('http'):
                            url = href
                        else:
                            url = urljoin(base_url, href)
                    
                    # Extract price
                    price = self._extract_price(all_text or title)
                    
                    # Extract address
                    address_elem = listing.find(['span', 'div', 'p'], class_=re.compile(r'location|address|area', re.I))
                    address = location
                    if address_elem:
                        address = address_elem.get_text(strip=True)
                    
                    # Extract description
                    desc_elem = listing.find('p', class_=re.compile(r'description|summary', re.I))
                    description = title
                    if desc_elem:
                        description = desc_elem.get_text(strip=True)
                    
                    bedrooms = self._extract_bedrooms(all_text or title)
                    bathrooms = self._extract_bathrooms(all_text or title)
                    has_garden = self._extract_garden(all_text or description or title)
                    has_balcony = self._extract_balcony(all_text or description or title)
                    
                    prop_type = "flat" if any(word in title.lower() for word in ["flat", "apartment"]) else "house"
                    
                    property_obj = Property(
                        title=title,
                        price=price,
                        address=address,
                        property_type=prop_type,
                        bedrooms=bedrooms,
                        bathrooms=bathrooms,
                        area_sqft=None,
                        description=description[:500] if description else title,
                        url=url,
                        source="Gumtree",
                        listed_date=None,
                        location=location,
                        postcode=self._extract_postcode(address),
                        has_garden=has_garden,
                        has_balcony=has_balcony,
                        image_url=self._extract_image_url(listing, base_url)
                    )
                    
                    properties.append(property_obj)
                    
                except Exception as e:
                    print(f"    Error parsing Gumtree listing: {e}")
                    continue
            
            time.sleep(self.delay)
            
        except Exception as e:
            print(f"  Error scraping Gumtree: {e}")
        
        return properties
    
    def scrape_onthemarket(self, location: str, property_type: str = "house", max_pages: int = 5) -> List[Property]:
        """
        Scrape OnTheMarket for property listings.
        """
        properties = []
        print(f"Scraping OnTheMarket for {property_type}s in {location}...")
        
        try:
            base_url = "https://www.onthemarket.com"
            # OnTheMarket search URL
            search_url = f"{base_url}/to-rent/property/{quote(location.lower())}/"
            
            response = self.session.get(search_url, timeout=15, allow_redirects=True)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Try multiple selectors
            listings = (
                soup.find_all('article', class_=re.compile(r'property|listing|result', re.I)) or
                soup.find_all('div', class_=re.compile(r'property|listing|result', re.I)) or
                soup.find_all('li', class_=re.compile(r'property|listing', re.I)) or
                soup.find_all('a', href=re.compile(r'/property/', re.I)) or
                []
            )
            
            if not listings:
                listings = soup.find_all(['div', 'article'], class_=re.compile(r'card|tile|box', re.I))
            
            print(f"  Found {len(listings)} potential listings on OnTheMarket")
            
            for listing in listings[:25]:
                try:
                    all_text = listing.get_text(separator=' ', strip=True)
                    if len(all_text) < 5:
                        continue
                    
                    # Find title
                    title_elem = (
                        listing.find('h2') or
                        listing.find('h3') or
                        listing.find('a', class_=re.compile(r'title|name', re.I)) or
                        listing.find('div', class_=re.compile(r'title|heading', re.I))
                    )
                    
                    if not title_elem:
                        continue
                    
                    title = title_elem.get_text(strip=True)
                    if not title or len(title) < 5:
                        continue
                    
                    # Get URL
                    link_elem = listing.find('a', href=re.compile(r'/property/', re.I))
                    if not link_elem:
                        link_elem = listing.find('a', href=True)
                    
                    url = ""
                    if link_elem:
                        href = link_elem.get('href', '')
                        if href.startswith('http'):
                            url = href
                        else:
                            url = urljoin(base_url, href)
                    
                    # Extract price
                    price = self._extract_price(all_text or title)
                    
                    # Extract address
                    address_elem = listing.find(['span', 'div', 'p'], class_=re.compile(r'location|address|area', re.I))
                    address = location
                    if address_elem:
                        address = address_elem.get_text(strip=True)
                    
                    # Extract description
                    desc_elem = listing.find('p', class_=re.compile(r'description|summary', re.I))
                    description = title
                    if desc_elem:
                        description = desc_elem.get_text(strip=True)
                    
                    bedrooms = self._extract_bedrooms(all_text or title)
                    bathrooms = self._extract_bathrooms(all_text or title)
                    has_garden = self._extract_garden(all_text or description or title)
                    has_balcony = self._extract_balcony(all_text or description or title)
                    
                    prop_type = "flat" if any(word in title.lower() for word in ["flat", "apartment"]) else "house"
                    
                    property_obj = Property(
                        title=title,
                        price=price,
                        address=address,
                        property_type=prop_type,
                        bedrooms=bedrooms,
                        bathrooms=bathrooms,
                        area_sqft=None,
                        description=description[:500] if description else title,
                        url=url,
                        source="OnTheMarket",
                        listed_date=None,
                        location=location,
                        postcode=self._extract_postcode(address),
                        has_garden=has_garden,
                        has_balcony=has_balcony,
                        image_url=self._extract_image_url(listing, base_url)
                    )
                    
                    properties.append(property_obj)
                    
                except Exception as e:
                    print(f"    Error parsing OnTheMarket listing: {e}")
                    continue
            
            time.sleep(self.delay)
            
        except Exception as e:
            print(f"  Error scraping OnTheMarket: {e}")
        
        return properties
    
    def scrape_primelocation(self, location: str, property_type: str = "house", max_pages: int = 5) -> List[Property]:
        """
        Scrape PrimeLocation for property listings.
        """
        properties = []
        print(f"Scraping PrimeLocation for {property_type}s in {location}...")
        
        try:
            base_url = "https://www.primelocation.com"
            # PrimeLocation search URL
            search_url = f"{base_url}/to-rent/property/{quote(location.lower())}/"
            
            response = self.session.get(search_url, timeout=15, allow_redirects=True)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Try multiple selectors
            listings = (
                soup.find_all('article', class_=re.compile(r'property|listing|result', re.I)) or
                soup.find_all('div', class_=re.compile(r'property|listing|result', re.I)) or
                soup.find_all('li', class_=re.compile(r'property|listing', re.I)) or
                soup.find_all('a', href=re.compile(r'/property/', re.I)) or
                []
            )
            
            if not listings:
                listings = soup.find_all(['div', 'article'], class_=re.compile(r'card|tile|box', re.I))
            
            print(f"  Found {len(listings)} potential listings on PrimeLocation")
            
            for listing in listings[:25]:
                try:
                    all_text = listing.get_text(separator=' ', strip=True)
                    if len(all_text) < 5:
                        continue
                    
                    # Find title
                    title_elem = (
                        listing.find('h2') or
                        listing.find('h3') or
                        listing.find('a', class_=re.compile(r'title|name', re.I)) or
                        listing.find('div', class_=re.compile(r'title|heading', re.I))
                    )
                    
                    if not title_elem:
                        continue
                    
                    title = title_elem.get_text(strip=True)
                    if not title or len(title) < 5:
                        continue
                    
                    # Get URL
                    link_elem = listing.find('a', href=re.compile(r'/property/', re.I))
                    if not link_elem:
                        link_elem = listing.find('a', href=True)
                    
                    url = ""
                    if link_elem:
                        href = link_elem.get('href', '')
                        if href.startswith('http'):
                            url = href
                        else:
                            url = urljoin(base_url, href)
                    
                    # Extract price
                    price = self._extract_price(all_text or title)
                    
                    # Extract address
                    address_elem = listing.find(['span', 'div', 'p'], class_=re.compile(r'location|address|area', re.I))
                    address = location
                    if address_elem:
                        address = address_elem.get_text(strip=True)
                    
                    # Extract description
                    desc_elem = listing.find('p', class_=re.compile(r'description|summary', re.I))
                    description = title
                    if desc_elem:
                        description = desc_elem.get_text(strip=True)
                    
                    bedrooms = self._extract_bedrooms(all_text or title)
                    bathrooms = self._extract_bathrooms(all_text or title)
                    has_garden = self._extract_garden(all_text or description or title)
                    has_balcony = self._extract_balcony(all_text or description or title)
                    
                    prop_type = "flat" if any(word in title.lower() for word in ["flat", "apartment"]) else "house"
                    
                    property_obj = Property(
                        title=title,
                        price=price,
                        address=address,
                        property_type=prop_type,
                        bedrooms=bedrooms,
                        bathrooms=bathrooms,
                        area_sqft=None,
                        description=description[:500] if description else title,
                        url=url,
                        source="PrimeLocation",
                        listed_date=None,
                        location=location,
                        postcode=self._extract_postcode(address),
                        has_garden=has_garden,
                        has_balcony=has_balcony,
                        image_url=self._extract_image_url(listing, base_url)
                    )
                    
                    properties.append(property_obj)
                    
                except Exception as e:
                    print(f"    Error parsing PrimeLocation listing: {e}")
                    continue
            
            time.sleep(self.delay)
            
        except Exception as e:
            print(f"  Error scraping PrimeLocation: {e}")
        
        return properties
    
    def scrape_generic_site(self, base_url: str, location: str, property_type: str) -> List[Property]:
        """
        Generic scraper template for property websites.
        This can be adapted for specific sites.
        """
        properties = []
        
        try:
            # Construct search URL (this is a template - actual URLs vary by site)
            search_url = f"{base_url}?location={quote(location)}&type={property_type}"
            
            response = self.session.get(search_url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # This is a template - actual selectors would need to be determined
            # by inspecting the target website's HTML structure
            listings = soup.find_all('div', class_='property-listing')  # Example selector
            
            for listing in listings:
                try:
                    # Extract property data (these selectors are examples)
                    title_elem = listing.find('h2', class_='title')
                    price_elem = listing.find('span', class_='price')
                    address_elem = listing.find('div', class_='address')
                    
                    if not title_elem:
                        continue
                    
                    title = title_elem.get_text(strip=True)
                    price_text = price_elem.get_text(strip=True) if price_elem else ""
                    address = address_elem.get_text(strip=True) if address_elem else location
                    
                    price = self._extract_price(price_text)
                    
                    # Extract link
                    link_elem = listing.find('a', href=True)
                    url = urljoin(base_url, link_elem['href']) if link_elem else ""
                    
                    # Determine property type from title/description
                    prop_type = "flat" if any(word in title.lower() for word in ["flat", "apartment", "flat"]) else "house"
                    all_text = listing.get_text()
                    
                    property_obj = Property(
                        title=title,
                        price=price,
                        address=address,
                        property_type=prop_type,
                        bedrooms=self._extract_bedrooms(title),
                        bathrooms=self._extract_bathrooms(title),
                        area_sqft=None,
                        description=title,
                        url=url,
                        source="Generic Site",
                        listed_date=None,
                        location=location,
                        postcode=self._extract_postcode(address),
                        has_garden=self._extract_garden(all_text or title),
                        has_balcony=self._extract_balcony(all_text or title)
                    )
                    
                    properties.append(property_obj)
                    
                except Exception as e:
                    print(f"Error parsing listing: {e}")
                    continue
            
            time.sleep(self.delay)
            
        except Exception as e:
            print(f"Error scraping {base_url}: {e}")
        
        return properties
    
    def filter_properties(self, properties: List[Property], filters: dict) -> List[Property]:
        """
        Filter properties based on search criteria.
        """
        filtered = []
        
        for prop in properties:
            # Combine title and description for exclusion checks
            combined_text = (prop.title + " " + prop.description).lower()
            
            # Exclude student accommodation
            if filters.get('exclude_student_accommodation', False):
                if self._is_student_accommodation(combined_text):
                    continue
            
            # Exclude house shares
            if filters.get('exclude_house_shares', False):
                if self._is_house_share(combined_text):
                    continue
            
            # Exclude retirement properties
            if filters.get('exclude_retirement', False):
                if self._is_retirement_property(combined_text):
                    continue
            
            # Bedroom filter
            if filters.get('min_bedrooms') is not None:
                if prop.bedrooms is None or prop.bedrooms < filters['min_bedrooms']:
                    continue
            if filters.get('max_bedrooms') is not None:
                if prop.bedrooms is not None and prop.bedrooms > filters['max_bedrooms']:
                    continue
            
            # Bathroom filter
            if filters.get('min_bathrooms') is not None:
                if prop.bathrooms is None or prop.bathrooms < filters['min_bathrooms']:
                    continue
            if filters.get('max_bathrooms') is not None:
                if prop.bathrooms is not None and prop.bathrooms > filters['max_bathrooms']:
                    continue
            
            # Garden filter
            if filters.get('has_garden') is not None:
                if prop.has_garden != filters['has_garden']:
                    continue
            
            # Balcony filter
            if filters.get('has_balcony') is not None:
                if prop.has_balcony != filters['has_balcony']:
                    continue
            
            # Price filter
            if filters.get('min_price') is not None:
                if prop.price is None or prop.price < filters['min_price']:
                    continue
            if filters.get('max_price') is not None:
                if prop.price is not None and prop.price > filters['max_price']:
                    continue
            
            filtered.append(prop)
        
        return filtered
    
    def scrape_all(self, locations: List[str], property_types: List[str], max_pages: int = 5, 
                   use_real_scrapers: bool = True, filters: Optional[dict] = None) -> List[Property]:
        """
        Scrape all configured locations and property types.
        Returns combined list of all properties found (optionally filtered).
        """
        all_properties = []
        
        for location in locations:
            print(f"\nScraping properties in {location}...")
            
            for prop_type in property_types:
                print(f"  Searching for {prop_type}s...")
                
                if use_real_scrapers:
                    # Scrape from real websites
                    # Spareroom for whole properties
                    spareroom_props = self.scrape_spareroom(location, prop_type, max_pages)
                    all_properties.extend(spareroom_props)
                    
                    # OpenRent
                    openrent_props = self.scrape_openrent(location, prop_type, max_pages)
                    all_properties.extend(openrent_props)
                    
                    # Gumtree
                    gumtree_props = self.scrape_gumtree(location, prop_type, max_pages)
                    all_properties.extend(gumtree_props)
                    
                    # OnTheMarket
                    onthemarket_props = self.scrape_onthemarket(location, prop_type, max_pages)
                    all_properties.extend(onthemarket_props)
                    
                    # PrimeLocation
                    primelocation_props = self.scrape_primelocation(location, prop_type, max_pages)
                    all_properties.extend(primelocation_props)
                else:
                    # Use mock data for testing
                    mock_properties = self._generate_mock_properties(location, prop_type)
                    all_properties.extend(mock_properties)
                
                time.sleep(self.delay)
        
        # Apply filters if provided
        if filters:
            print(f"\nFiltering properties based on criteria...")
            before_count = len(all_properties)
            all_properties = self.filter_properties(all_properties, filters)
            after_count = len(all_properties)
            print(f"  Filtered from {before_count} to {after_count} properties")
        
        return all_properties
    
    def _generate_mock_properties(self, location: str, property_type: str, count: int = 3) -> List[Property]:
        """
        Generate mock property data for demonstration.
        Replace this with actual scraping logic for real websites.
        """
        import random
        
        mock_properties = []
        prices = [150000, 200000, 250000, 300000, 400000, 500000, 600000]
        bedrooms = [1, 2, 3, 4, 5]
        
        for i in range(count):
            price = random.choice(prices)
            beds = random.choice(bedrooms)
            
            property_obj = Property(
                title=f"{beds} bedroom {property_type} in {location}",
                price=price,
                address=f"{random.randint(1, 100)} High Street, {location}",
                property_type=property_type,
                bedrooms=beds,
                bathrooms=random.choice([1, 2, 3]),
                area_sqft=random.choice([600, 800, 1000, 1200, 1500]),
                description=f"Beautiful {property_type} located in the heart of {location}. Modern amenities and excellent transport links.",
                url=f"https://example-property-site.com/property/{random.randint(1000, 9999)}",
                source="Mock Data",
                listed_date=None,
                location=location,
                postcode=f"{random.choice(['SW', 'NW', 'SE', 'NE', 'E', 'W'])}{random.randint(1, 20)} {random.randint(1, 9)}{random.choice(['AA', 'AB', 'CD', 'EF'])}",
                has_garden=random.choice([True, False, None]),
                has_balcony=random.choice([True, False, None])
            )
            
            mock_properties.append(property_obj)
        
        return mock_properties

