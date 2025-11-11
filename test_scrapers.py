
"""Test script to analyze website structures."""
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote

def test_spareroom():
    """Test Spareroom access."""
    print("\n" + "="*60)
    print("Testing Spareroom")
    print("="*60)
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
    })
    
    location = "London"
    test_urls = [
        f"https://www.spareroom.co.uk/flatshare/?search={quote(location)}",
        f"https://www.spareroom.co.uk/flatshare/",
        f"https://www.spareroom.co.uk/",
    ]
    
    for url in test_urls:
        try:
            print(f"\nTrying: {url}")
            response = session.get(url, timeout=10, allow_redirects=True)
            print(f"Status: {response.status_code}")
            print(f"Content length: {len(response.content)}")
            print(f"Final URL: {response.url}")
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                # Look for common listing patterns
                listings = (
                    soup.find_all('article') or
                    soup.find_all('div', class_=lambda x: x and ('listing' in x.lower() or 'property' in x.lower())) or
                    soup.find_all('a', href=lambda x: x and '/room' in x.lower())
                )
                print(f"Found {len(listings)} potential listings")
                if listings:
                    print(f"Sample listing HTML: {str(listings[0])[:200]}")
        except Exception as e:
            print(f"Error: {e}")

def test_gumtree():
    """Test Gumtree access."""
    print("\n" + "="*60)
    print("Testing Gumtree")
    print("="*60)
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8',
        'Referer': 'https://www.google.com/',
    })
    
    location = "London"
    test_urls = [
        f"https://www.gumtree.com/search?q={quote('property rent ' + location)}",
        f"https://www.gumtree.com/search?q={quote('rent ' + location)}&category=property-for-rent",
        f"https://www.gumtree.com/search?category=property-for-rent&q={quote(location)}",
        f"https://www.gumtree.com/search?q={quote(location + ' property')}",
        f"https://www.gumtree.com/",
    ]
    
    for url in test_urls:
        try:
            print(f"\nTrying: {url}")
            response = session.get(url, timeout=10, allow_redirects=True)
            print(f"Status: {response.status_code}")
            print(f"Content length: {len(response.content)}")
            print(f"Final URL: {response.url}")
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                # Try different selectors
                listings = (
                    soup.find_all('article', class_=lambda x: x and 'listing' in str(x).lower()) or
                    soup.find_all('div', class_=lambda x: x and 'listing' in str(x).lower()) or
                    soup.find_all('article') or
                    soup.find_all('a', href=lambda x: x and ('property' in x.lower() or '/p/' in x.lower()))
                )
                print(f"Found {len(listings)} potential listings")
                if listings:
                    print(f"Sample listing HTML: {str(listings[0])[:300]}")
                    # Check for price patterns
                    text = listings[0].get_text()
                    if '£' in text:
                        print(f"Contains price info: Yes")
        except Exception as e:
            print(f"Error: {e}")

def test_primelocation():
    """Test PrimeLocation access with different methods."""
    print("\n" + "="*60)
    print("Testing PrimeLocation")
    print("="*60)
    
    # Try method 1: Standard headers
    session1 = requests.Session()
    session1.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8',
        'Referer': 'https://www.google.com/',
    })
    
    # Try method 2: More complete headers
    session2 = requests.Session()
    session2.headers.update({
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
        'Cache-Control': 'max-age=0',
        'Referer': 'https://www.google.com/',
    })
    
    location = "London"
    test_urls = [
        f"https://www.primelocation.com/to-rent/",
        f"https://www.primelocation.com/",
        f"https://www.primelocation.com/rent/",
    ]
    
    for session, name in [(session1, "Method 1"), (session2, "Method 2")]:
        print(f"\n{name}:")
        for url in test_urls:
            try:
                print(f"  Trying: {url}")
                # First visit homepage to get cookies
                try:
                    session.get("https://www.primelocation.com/", timeout=5)
                except:
                    pass
                
                response = session.get(url, timeout=10, allow_redirects=True)
                print(f"  Status: {response.status_code}")
                print(f"  Content length: {len(response.content)}")
                print(f"  Final URL: {response.url}")
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    listings = (
                        soup.find_all('article') or
                        soup.find_all('div', class_=lambda x: x and ('property' in x.lower() or 'listing' in x.lower()))
                    )
                    print(f"  Found {len(listings)} potential listings")
                    if listings:
                        print(f"  Sample listing HTML: {str(listings[0])[:200]}")
                        break
            except Exception as e:
                print(f"  Error: {e}")

if __name__ == "__main__":
    test_spareroom()
    test_gumtree()
    test_primelocation()

