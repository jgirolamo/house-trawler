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
        
        # Session will handle cookies automatically via requests.Session()
        
        # Enhanced headers to mimic a real browser more closely
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0'
        })
        
        # Initialize session by visiting common sites to establish cookies
        self._initialize_session()
    
    def _initialize_session(self):
        """Initialize session by visiting homepage to get cookies."""
        try:
            # Visit Google first to establish a "normal" browsing pattern
            try:
                self.session.get('https://www.google.com/', timeout=5)
                time.sleep(0.5)
            except:
                pass
            
            # Visit each site's homepage to establish session cookies
            sites_to_visit = [
                'https://www.spareroom.co.uk/',
                'https://www.openrent.co.uk/',
                'https://www.gumtree.com/',
                'https://www.onthemarket.com/',
            ]
            
            for site in sites_to_visit:
                try:
                    response = self.session.get(site, timeout=10, allow_redirects=True)
                    # Cookies are automatically stored by requests.Session()
                    time.sleep(0.5)
                except:
                    continue
            
            print("Session initialized with cookies")
        except Exception as e:
            print(f"Warning: Could not fully initialize session: {e}")
    
    def _get_with_session(self, url: str, timeout: int = 15, allow_redirects: bool = True, headers: dict = None):
        """Make a request with proper session and cookie handling."""
        # Merge headers
        request_headers = self.session.headers.copy()
        if headers:
            request_headers.update(headers)
        
        # Make request with session cookies (automatically handled by requests.Session)
        response = self.session.get(url, timeout=timeout, allow_redirects=allow_redirects, headers=request_headers)
        
        # Cookies are automatically stored by requests.Session
        
        return response
    
    def _fuzzy_match_keyword(self, keyword: str, text: str) -> bool:
        """Check if keyword matches text with typo tolerance using Levenshtein distance."""
        from difflib import SequenceMatcher
        
        # Skip very short keywords (1-3 chars) - require exact match
        if len(keyword) <= 3:
            return keyword in text
        
        # Split text into words
        words = re.split(r'\s+', text)
        
        for word in words:
            # Skip very short words
            if len(word) < 3:
                continue
            
            # Check if keyword is contained in word or vice versa
            if keyword in word or word in keyword:
                return True
            
            # Calculate similarity ratio (0.0 to 1.0)
            similarity = SequenceMatcher(None, keyword, word).ratio()
            
            # For words 4-6 chars: allow 1 typo (similarity >= 0.75)
            # For words 7+ chars: allow 2 typos (similarity >= 0.70)
            if len(keyword) <= 6:
                if similarity >= 0.75:
                    return True
            else:
                if similarity >= 0.70:
                    return True
        
        return False
    
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
    
    def scrape_rightmove(self, location: str, property_type: str = "house", max_pages: int = 5) -> List[Property]:
        """
        Scrape Rightmove for property listings.
        Using simplified approach like Gumtree.
        """
        properties = []
        print(f"Scraping Rightmove for {property_type}s in {location}...")
        
        try:
            base_url = "https://www.rightmove.co.uk"
            
            # Simple approach - start with basic URLs (like we did for Gumtree)
            # First visit homepage to establish session
            try:
                self._get_with_session(f"{base_url}/", timeout=10)
                time.sleep(1)
            except:
                pass
            
            # Try the simplest URL patterns first
            search_urls = [
                # Simple search patterns
                f"{base_url}/property-to-rent/find.html?locationIdentifier={quote(location)}",
                f"{base_url}/property-to-rent/find.html?searchLocation={quote(location)}",
                f"{base_url}/property-to-rent.html?locationIdentifier={quote(location)}",
                f"{base_url}/property-to-rent/find.html?q={quote(location)}",
            ]
            
            response = None
            for search_url in search_urls:
                try:
                    response = self._get_with_session(search_url, timeout=15)
                    if response.status_code == 200 and len(response.content) > 5000:
                        break
                    time.sleep(0.5)
                except:
                    continue
            
            if not response or response.status_code != 200:
                print(f"  Could not access Rightmove (tried {len(search_urls)} URL formats)")
                return properties
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Try multiple selectors for Rightmove
            listings = soup.find_all('div', class_=re.compile(r'propertyCard|property-card|l-property', re.I))
            
            # Fallback to other patterns
            if not listings:
                listings = soup.find_all('div', class_=re.compile(r'property|listing|result', re.I))
            
            # Fallback to article patterns
            if not listings:
                listings = soup.find_all('article', class_=re.compile(r'property|listing|result', re.I))
            
            # Last resort: find by property links
            if not listings:
                property_links = soup.find_all('a', href=re.compile(r'/properties/', re.I))
                if property_links:
                    listings = []
                    for link in property_links[:500]:
                        parent = link.find_parent(['div', 'article', 'li'])
                        if parent and parent not in listings:
                            listings.append(parent)
            
            print(f"  Found {len(listings)} potential listings on Rightmove")
            
            for listing in listings[:500]:  # Limit to first 500 properties per search
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
                    link_elem = listing.find('a', href=re.compile(r'/properties/', re.I))
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
                    
                    # Extract address (try to find address element)
                    address_elem = (
                        listing.find('address') or
                        listing.find('div', class_=re.compile(r'address', re.I)) or
                        listing.find('span', class_=re.compile(r'address', re.I))
                    )
                    address = address_elem.get_text(strip=True) if address_elem else location
                    
                    # Extract bedrooms and bathrooms
                    bedrooms = self._extract_bedrooms(all_text or title)
                    bathrooms = self._extract_bathrooms(all_text or title)
                    has_garden = self._extract_garden(all_text or title)
                    has_balcony = self._extract_balcony(all_text or title)
                    
                    # Get description
                    desc_elem = listing.find('div', class_=re.compile(r'description|summary', re.I))
                    description = desc_elem.get_text(strip=True) if desc_elem else title
                    
                    # Determine property type
                    combined_text = (title + " " + description).lower()
                    prop_type = "flat" if any(word in combined_text for word in ["flat", "apartment"]) else "house"
                    
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
                        source="Rightmove",
                        listed_date=None,
                        location=location,
                        postcode=self._extract_postcode(address),
                        has_garden=has_garden,
                        has_balcony=has_balcony,
                        image_url=self._extract_image_url(listing, base_url)
                    )
                    
                    properties.append(property_obj)
                    
                except Exception as e:
                    print(f"    Error parsing Rightmove listing: {e}")
                    continue
            
            time.sleep(self.delay)
            
        except Exception as e:
            print(f"  Error scraping Rightmove: {e}")
        
        return properties
    
    def scrape_zoopla(self, location: str, property_type: str, max_pages: int = 5) -> List[Property]:
        """
        Scrape Zoopla (example implementation).
        Note: Real implementation would need to handle their actual HTML structure.
        """
        properties = []
        print(f"Note: Zoopla scraping requires careful implementation due to anti-scraping measures.")
        return properties
    
    def scrape_spareroom(self, location: str, property_type: str = "whole property", max_pages: int = 5, filters: Optional[dict] = None) -> List[Property]:
        """
        Scrape Spareroom for whole properties.
        Searches for whole properties suitable for sharing.
        Spareroom supports: search (location), flatshare_type, min_rent, max_rent, bedrooms
        """
        properties = []
        print(f"Scraping Spareroom for whole properties in {location}...")
        
        try:
            # Spareroom search URL for whole properties
            base_url = "https://www.spareroom.co.uk"
            
            # Visit main page to establish session and get cookies
            try:
                self._get_with_session(f"{base_url}/", timeout=15)
                time.sleep(1)
            except:
                pass
            
            # Build URL with common parameters
            params = [f"search={quote(location)}", "flatshare_type=whole_property"]
            
            # Add price filters if provided (Spareroom uses min_rent/max_rent)
            if filters:
                if filters.get('min_price'):
                    params.append(f"min_rent={int(filters['min_price'])}")
                if filters.get('max_price'):
                    params.append(f"max_rent={int(filters['max_price'])}")
                # Add bedrooms filter
                if filters.get('min_bedrooms'):
                    params.append(f"bedrooms={int(filters['min_bedrooms'])}")
            
            # Try updated URL patterns with filters
            search_urls = [
                f"{base_url}/flatshare/?{'&'.join(params)}",
                f"{base_url}/flatshare/?search={quote(location)}&flatshare_type=whole_property",
                f"{base_url}/flatshare/?search={quote(location)}",
                f"{base_url}/flatshare/flatshare.pl?search_id=&search={quote(location)}&flatshare_type=whole_property",
            ]
            
            response = None
            for search_url in search_urls:
                try:
                    response = self._get_with_session(search_url, timeout=15)
                    if response.status_code == 200 and len(response.content) > 5000:
                        break
                except:
                    continue
            
            if not response or response.status_code != 200:
                print(f"  Could not access Spareroom (tried {len(search_urls)} URL formats)")
                return properties
            
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Spareroom uses 'listing-card' class - this is the correct selector
            listings = soup.find_all('article', class_=re.compile(r'listing-card', re.I))
            
            if not listings:
                # Fallback to other possible selectors
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
            
            for listing in listings[:500]:  # Limit to first 500 properties per search
                try:
                    # Spareroom structure: listing-card with listing-card__link
                    link_elem = listing.find('a', class_=re.compile(r'listing-card__link', re.I))
                    if not link_elem:
                        link_elem = listing.find('a', href=True)
                    
                    if not link_elem:
                        continue
                    
                    # Get title from link title attribute or text
                    title = link_elem.get('title', '') or link_elem.get_text(strip=True)
                    if not title or len(title) < 5:
                        continue
                    
                    # Get URL
                    url = urljoin(base_url, link_elem['href']) if link_elem.get('href') else ""
                    
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
    
    def scrape_openrent(self, location: str, property_type: str = "house", max_pages: int = 5, filters: Optional[dict] = None) -> List[Property]:
        """
        Scrape OpenRent for rental properties.
        OpenRent supports: term (location), minPrice, maxPrice, bedrooms
        """
        properties = []
        print(f"Scraping OpenRent for {property_type}s in {location}...")
        
        try:
            # OpenRent search URL with common parameters
            base_url = "https://www.openrent.co.uk"
            params = [f"term={quote(location)}"]
            
            # Add price filters if provided
            if filters:
                if filters.get('min_price'):
                    params.append(f"minPrice={int(filters['min_price'])}")
                if filters.get('max_price'):
                    params.append(f"maxPrice={int(filters['max_price'])}")
                # Add bedrooms filter (use min_bedrooms if available)
                if filters.get('min_bedrooms'):
                    params.append(f"bedrooms={int(filters['min_bedrooms'])}")
            
            search_url = f"{base_url}/properties-to-rent?{'&'.join(params)}"
            
            response = self._get_with_session(search_url, timeout=15)
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
            for listing in listings[:500]:  # Limit to first 500 properties per search
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
    
    def scrape_gumtree(self, location: str, property_type: str = "house", max_pages: int = 5, filters: Optional[dict] = None) -> List[Property]:
        """
        Scrape Gumtree for property listings.
        Gumtree supports: q (query), category, min_price, max_price, bedrooms
        """
        properties = []
        print(f"Scraping Gumtree for {property_type}s in {location}...")
        
        try:
            base_url = "https://www.gumtree.com"
            
            # Simple, working approach - start with basic search
            # First visit homepage to establish session
            try:
                self._get_with_session(f"{base_url}/", timeout=10)
                time.sleep(1)
            except:
                pass
            
            # Build search query with common parameters
            search_query = f"property rent {location}"
            if property_type:
                search_query = f"{property_type} rent {location}"
            
            # Build URL with filters
            params = [f"q={quote(search_query)}", "category=property-for-rent"]
            
            # Add price filters if provided
            if filters:
                if filters.get('min_price'):
                    params.append(f"min_price={int(filters['min_price'])}")
                if filters.get('max_price'):
                    params.append(f"max_price={int(filters['max_price'])}")
                # Add bedrooms to search query if specified
                if filters.get('min_bedrooms'):
                    search_query = f"{filters['min_bedrooms']} bedroom {search_query}"
                    params[0] = f"q={quote(search_query)}"
            
            # Try URL patterns with filters
            search_urls = [
                f"{base_url}/search?{'&'.join(params)}",
                f"{base_url}/search?q={quote(search_query)}&category=property-for-rent",
                f"{base_url}/search?q={quote('property rent ' + location)}",
                f"{base_url}/property-for-rent/{quote(location)}",
            ]
            
            response = None
            for search_url in search_urls:
                try:
                    response = self._get_with_session(search_url, timeout=15)
                    if response.status_code == 200 and len(response.content) > 5000:
                        break
                    time.sleep(0.5)
                except:
                    continue
            
            if not response or response.status_code != 200:
                print(f"  Could not access Gumtree (tried {len(search_urls)} URL formats)")
                return properties
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Simple selector - this was working before
            # Gumtree uses article elements with 'listing-tile' class
            listings = soup.find_all('article', class_=re.compile(r'listing-tile', re.I))
            
            # Fallback to other article patterns
            if not listings:
                listings = soup.find_all('article', class_=re.compile(r'listing|result', re.I))
            
            # Fallback to div patterns
            if not listings:
                listings = soup.find_all('div', class_=re.compile(r'listing|result|item', re.I))
            
            # Last resort: find by property links
            if not listings:
                property_links = soup.find_all('a', href=re.compile(r'/property-for-rent/', re.I))
                if property_links:
                    listings = []
                    for link in property_links[:500]:
                        parent = link.find_parent(['article', 'div', 'li'])
                        if parent and parent not in listings:
                            listings.append(parent)
            
            print(f"  Found {len(listings)} potential listings on Gumtree")
            
            for listing in listings[:500]:  # Limit to first 500 properties per search
                try:
                    all_text = listing.get_text(separator=' ', strip=True)
                    if len(all_text) < 5:
                        continue
                    
                    # Gumtree structure: find title and link
                    # Try to find link first (usually contains title)
                    link_elem = listing.find('a', href=True)
                    if not link_elem:
                        # Try finding title in headings
                        title_elem = listing.find('h2') or listing.find('h3')
                        if not title_elem:
                            continue
                        title = title_elem.get_text(strip=True)
                    else:
                        # Get title from link text or aria-label
                        title = (
                            link_elem.get('aria-label', '') or
                            link_elem.get('title', '') or
                            link_elem.get_text(strip=True)
                        )
                    
                    if not title or len(title) < 5:
                        continue
                    
                    # Get URL
                    url = ""
                    if link_elem:
                        href = link_elem.get('href', '')
                        if href.startswith('http'):
                            url = href
                        else:
                            url = urljoin(base_url, href)
                    elif 'href' in str(listing):
                        # Try to extract from data attributes
                        data_link = listing.get('data-href') or listing.get('data-url')
                        if data_link:
                            url = urljoin(base_url, data_link) if not data_link.startswith('http') else data_link
                    
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
    
    def scrape_onthemarket(self, location: str, property_type: str = "house", max_pages: int = 5, filters: Optional[dict] = None) -> List[Property]:
        """
        Scrape OnTheMarket for property listings.
        OnTheMarket supports: locationIdentifier, minPrice, maxPrice, bedrooms
        """
        properties = []
        print(f"Scraping OnTheMarket for {property_type}s in {location}...")
        
        try:
            base_url = "https://www.onthemarket.com"
            
            # Build URL with common parameters
            params = [f"locationIdentifier={quote(location)}"]
            
            # Add price filters if provided
            if filters:
                if filters.get('min_price'):
                    params.append(f"minPrice={int(filters['min_price'])}")
                if filters.get('max_price'):
                    params.append(f"maxPrice={int(filters['max_price'])}")
                # Add bedrooms filter
                if filters.get('min_bedrooms'):
                    params.append(f"bedrooms={int(filters['min_bedrooms'])}")
            
            # OnTheMarket search URLs with filters
            search_urls = [
                f"{base_url}/to-rent/?{'&'.join(params)}",
                f"{base_url}/to-rent/property/{quote(location.lower())}/",
                f"{base_url}/to-rent/property/{quote(location)}/",
                f"{base_url}/to-rent/?locationIdentifier={quote(location)}",
                f"{base_url}/to-rent/?q={quote(location)}",
            ]
            
            # First visit main page to establish session
            try:
                self.session.get(f"{base_url}/", timeout=10, allow_redirects=True)
                time.sleep(1)
                self.session.headers.update({'Referer': f"{base_url}/"})
            except:
                pass
            
            response = None
            for search_url in search_urls:
                try:
                    response = self.session.get(search_url, timeout=15, allow_redirects=True)
                    if response.status_code == 200 and len(response.content) > 5000:
                        break
                except:
                    continue
            
            if not response or response.status_code != 200:
                print(f"  Could not access OnTheMarket (tried {len(search_urls)} URL formats)")
                return properties
            
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
            
            for listing in listings[:500]:  # Limit to first 500 properties per search
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
        Using simplified approach like Gumtree.
        """
        properties = []
        print(f"Scraping PrimeLocation for {property_type}s in {location}...")
        
        try:
            base_url = "https://www.primelocation.com"
            
            # Simple approach - start with basic URLs (like we did for Gumtree)
            # First visit homepage to establish session
            try:
                self._get_with_session(f"{base_url}/", timeout=10)
                time.sleep(1)
            except:
                pass
            
            # Try the simplest URL patterns first
            search_urls = [
                # Simple search patterns
                f"{base_url}/to-rent/?q={quote(location)}",
                f"{base_url}/to-rent/?locationIdentifier={quote(location)}",
                f"{base_url}/to-rent/property/{quote(location.lower())}/",
                f"{base_url}/to-rent/property/{quote(location)}/",
                f"{base_url}/to-rent/{quote(location.lower())}/",
            ]
            
            response = None
            for search_url in search_urls:
                try:
                    response = self._get_with_session(search_url, timeout=15)
                    if response.status_code == 200 and len(response.content) > 5000:
                        break
                    elif response.status_code == 403:
                        # Blocked - try next URL
                        continue
                    time.sleep(0.5)
                except:
                    continue
            
            if not response or response.status_code != 200:
                if response and response.status_code == 403:
                    print(f"  PrimeLocation blocked access (403 Forbidden)")
                else:
                    print(f"  Could not access PrimeLocation (tried {len(search_urls)} URL formats)")
                return properties
            
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
            
            for listing in listings[:500]:  # Limit to first 500 properties per search
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
            
            response = self._get_with_session(search_url, timeout=10)
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
    
    def calculate_match_score(self, prop: Property, filters: dict) -> float:
        """
        Calculate a match score (0-100) for a property based on how well it matches search criteria.
        Higher score = better match.
        """
        score = 0.0
        max_score = 100.0
        
        # Price match (30 points max)
        if prop.price is not None:
            min_price = filters.get('min_price', 0)
            max_price = filters.get('max_price', float('inf'))
            
            if min_price is not None and max_price is not None and max_price != float('inf'):
                # Ideal price is middle of range
                ideal_price = (min_price + max_price) / 2
                price_range = max_price - min_price
                
                if price_range > 0:
                    # Score based on how close to ideal price
                    price_diff = abs(prop.price - ideal_price)
                    price_score = max(0, 30 * (1 - (price_diff / price_range)))
                    score += price_score
                else:
                    # Exact match
                    if min_price <= prop.price <= max_price:
                        score += 30
            elif min_price is not None:
                # Only min price specified - lower is better
                if prop.price >= min_price:
                    score += 30
            elif max_price is not None and max_price != float('inf'):
                # Only max price specified
                if prop.price <= max_price:
                    score += 30
            else:
                # No price filter - give base score
                score += 15
        else:
            # No price data - penalty
            score += 5
        
        # Bedrooms match (20 points max)
        if filters.get('min_bedrooms') is not None or filters.get('max_bedrooms') is not None:
            if prop.bedrooms is not None:
                min_bed = filters.get('min_bedrooms', 0)
                max_bed = filters.get('max_bedrooms', float('inf'))
                
                if min_bed <= prop.bedrooms <= max_bed:
                    # Exact match gets full points, close match gets partial
                    ideal_bed = (min_bed + max_bed) / 2 if max_bed != float('inf') else min_bed
                    if prop.bedrooms == ideal_bed:
                        score += 20
                    else:
                        score += 15  # Within range but not ideal
                else:
                    score += 5  # Outside range but has data
            else:
                score += 2  # No bedroom data
        else:
            # No bedroom filter - bonus if data exists
            if prop.bedrooms is not None:
                score += 10
        
        # Bathrooms match (20 points max)
        if filters.get('min_bathrooms') is not None or filters.get('max_bathrooms') is not None:
            if prop.bathrooms is not None:
                min_bath = filters.get('min_bathrooms', 0)
                max_bath = filters.get('max_bathrooms', float('inf'))
                
                if min_bath <= prop.bathrooms <= max_bath:
                    ideal_bath = (min_bath + max_bath) / 2 if max_bath != float('inf') else min_bath
                    if prop.bathrooms == ideal_bath:
                        score += 20
                    else:
                        score += 15
                else:
                    score += 5
            else:
                score += 2
        else:
            if prop.bathrooms is not None:
                score += 10
        
        # Garden match (10 points)
        if filters.get('has_garden') is True:
            if prop.has_garden is True:
                score += 10
            elif prop.has_garden is False:
                score += 0  # Explicitly doesn't have garden when required
            else:
                score += 3  # Unknown - give small benefit of doubt
        elif filters.get('has_garden') is False:
            # Garden not required, but having it is still a bonus
            if prop.has_garden is True:
                score += 3
        
        # Balcony match (10 points)
        if filters.get('has_balcony') is True:
            if prop.has_balcony is True:
                score += 10
            elif prop.has_balcony is False:
                score += 0
            else:
                score += 3
        elif filters.get('has_balcony') is False:
            if prop.has_balcony is True:
                score += 3
        
        # Data completeness bonus (10 points)
        completeness = 0
        if prop.price is not None:
            completeness += 2
        if prop.bedrooms is not None:
            completeness += 2
        if prop.bathrooms is not None:
            completeness += 2
        if prop.image_url:
            completeness += 2
        if prop.postcode:
            completeness += 2
        score += completeness
        
        # Normalize to 0-100
        return min(100.0, max(0.0, score))
    
    def filter_properties(self, properties: List[Property], filters: dict) -> List[Property]:
        """
        Filter properties based on search criteria and calculate match scores.
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
            
            # Keywords filter (at least some keywords must match, with typo tolerance)
            if filters.get('keywords'):
                keywords_str = filters['keywords'].lower().strip()
                if keywords_str:
                    # Combine all searchable text
                    searchable_text = f"{prop.title} {prop.address} {prop.description}".lower()
                    
                    # Split keywords by comma or space
                    keywords = [k.strip() for k in re.split(r'[,\s]+', keywords_str) if k.strip()]
                    
                    if keywords:
                        # Count how many keywords match (with typo tolerance)
                        matching_keywords = []
                        for kw in keywords:
                            # First try exact match
                            if kw in searchable_text:
                                matching_keywords.append(kw)
                            else:
                                # Try fuzzy match with typo tolerance
                                if self._fuzzy_match_keyword(kw, searchable_text):
                                    matching_keywords.append(kw)
                        
                        match_count = len(matching_keywords)
                        
                        # Require at least 50% of keywords to match, or at least 1 if there's only 1-2 keywords
                        min_required = 1 if len(keywords) <= 2 else int(len(keywords) * 0.5) + (1 if len(keywords) % 2 == 1 else 0)
                        
                        if match_count < min_required:
                            continue
            
            # Calculate match score
            prop.match_score = self.calculate_match_score(prop, filters)
            
            filtered.append(prop)
        
        # Sort by match score (highest first)
        filtered.sort(key=lambda p: p.match_score or 0, reverse=True)
        
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
                    # Scrape from real websites - pass filters to each scraper
                    # Spareroom for whole properties
                    spareroom_props = self.scrape_spareroom(location, prop_type, max_pages, filters)
                    all_properties.extend(spareroom_props)
                    
                    # OpenRent
                    openrent_props = self.scrape_openrent(location, prop_type, max_pages, filters)
                    all_properties.extend(openrent_props)
                    
                    # Gumtree
                    gumtree_props = self.scrape_gumtree(location, prop_type, max_pages, filters)
                    all_properties.extend(gumtree_props)
                    
                    # OnTheMarket
                    onthemarket_props = self.scrape_onthemarket(location, prop_type, max_pages, filters)
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

