"""
Quick test to verify the entire system works together.
"""
import os
import json
from trawler import UKPropertyTrawler
from storage import PropertyStorage
from property_model import Property

def test_system():
    """Test the complete system flow."""
    print("=" * 60)
    print("SYSTEM INTEGRATION TEST")
    print("=" * 60)
    
    # Test 1: Create trawler
    print("\n1. Testing trawler initialization...")
    trawler = UKPropertyTrawler(delay=1.0)
    print("   [OK] Trawler initialized")
    
    # Test 2: Test match score calculation
    print("\n2. Testing match score calculation...")
    test_prop = Property(
        title="Test Property",
        price=1500.0,
        address="London",
        property_type="house",
        bedrooms=2,
        bathrooms=1,
        area_sqft=None,
        description="Test description",
        url="http://test.com",
        source="Test",
        listed_date=None,
        location="London",
        postcode="SW1A 1AA",
        has_garden=True,
        has_balcony=False,
        image_url="http://test.com/image.jpg"
    )
    
    filters = {
        'min_price': 1000,
        'max_price': 2000,
        'min_bedrooms': 2,
        'max_bedrooms': 3,
        'has_garden': True
    }
    
    score = trawler.calculate_match_score(test_prop, filters)
    print(f"   [OK] Match score calculated: {score:.1f}/100")
    assert score > 0, "Score should be positive"
    
    # Test 3: Test filtering
    print("\n3. Testing property filtering...")
    test_properties = [test_prop]
    filtered = trawler.filter_properties(test_properties, filters)
    print(f"   [OK] Filtered properties: {len(filtered)}")
    assert len(filtered) > 0, "Should have at least one property"
    assert filtered[0].match_score is not None, "Match score should be set"
    print(f"   [OK] Match score assigned: {filtered[0].match_score:.1f}")
    
    # Test 4: Test storage
    print("\n4. Testing property storage...")
    storage = PropertyStorage(output_dir="test_output")
    storage.save_to_json(filtered, "test_properties.json")
    print("   [OK] Properties saved to JSON")
    
    # Verify JSON contains match_score
    json_path = os.path.join("test_output", "test_properties.json")
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        assert 'match_score' in data[0], "JSON should contain match_score"
        print(f"   [OK] Match score in JSON: {data[0]['match_score']:.1f}")
    
    # Test 5: Verify Property model
    print("\n5. Testing Property model...")
    prop_dict = test_prop.to_dict()
    assert 'match_score' in prop_dict, "to_dict() should include match_score"
    print("   [OK] Property.to_dict() includes match_score")
    
    # Cleanup
    if os.path.exists(json_path):
        os.remove(json_path)
    if os.path.exists("test_output"):
        try:
            os.rmdir("test_output")
        except:
            pass
    
    print("\n" + "=" * 60)
    print("[SUCCESS] ALL TESTS PASSED - System is working correctly!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Run: python main.py (to scrape properties with match scores)")
    print("2. Run: python app.py (to view in web interface)")
    print("3. Open: http://localhost:5000 (in your browser)")

if __name__ == "__main__":
    test_system()

