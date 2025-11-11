"""
Flask web application to view scraped properties.
"""
from flask import Flask, render_template, jsonify, request
import json
import os
from storage import PropertyStorage

app = Flask(__name__)

# Configuration for deployment
PORT = int(os.environ.get('PORT', 5000))
HOST = os.environ.get('HOST', '0.0.0.0')  # Use 0.0.0.0 for Render
DEBUG = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'

# Load properties from JSON file
def load_properties():
    """Load properties from the output JSON file."""
    storage = PropertyStorage()
    json_path = os.path.join(storage.output_dir, "properties.json")
    
    if not os.path.exists(json_path):
        return []
    
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)

@app.route('/')
def index():
    """Main page showing all properties."""
    properties = load_properties()
    return render_template('index.html', properties=properties, count=len(properties))

@app.route('/api/properties')
def api_properties():
    """API endpoint to get properties as JSON."""
    properties = load_properties()
    return jsonify(properties)

@app.route('/api/stats')
def api_stats():
    """API endpoint for statistics."""
    properties = load_properties()
    
    stats = {
        'total': len(properties),
        'by_source': {},
        'by_type': {},
        'with_garden': 0,
        'with_balcony': 0,
        'price_range': {
            'min': None,
            'max': None,
            'avg': None
        }
    }
    
    prices = []
    for prop in properties:
        # Count by source
        source = prop.get('source', 'Unknown')
        stats['by_source'][source] = stats['by_source'].get(source, 0) + 1
        
        # Count by type
        prop_type = prop.get('property_type', 'unknown')
        stats['by_type'][prop_type] = stats['by_type'].get(prop_type, 0) + 1
        
        # Count features
        if prop.get('has_garden'):
            stats['with_garden'] += 1
        if prop.get('has_balcony'):
            stats['with_balcony'] += 1
        
        # Collect prices
        if prop.get('price'):
            prices.append(prop['price'])
    
    # Calculate price stats
    if prices:
        stats['price_range']['min'] = min(prices)
        stats['price_range']['max'] = max(prices)
        stats['price_range']['avg'] = sum(prices) / len(prices)
    
    return jsonify(stats)

@app.route('/api/run-trawler', methods=['POST'])
def run_trawler():
    """API endpoint to run the trawler with search parameters."""
    import subprocess
    import threading
    import json as json_lib
    
    # Get search parameters from request
    data = request.get_json() or {}
    search_params = data.get('search_params', {})
    
    def run_trawler_async():
        """Run trawler in background with custom config."""
        try:
            # Create temporary config with search parameters
            temp_config = {
                "search_params": {
                    "locations": search_params.get('locations', ['London']),
                    "min_price": search_params.get('min_price', 0),
                    "max_price": search_params.get('max_price', 1000000),
                    "property_types": search_params.get('property_types', ['house', 'flat']),
                    "max_pages": search_params.get('max_pages', 20),
                    "min_bedrooms": search_params.get('min_bedrooms'),
                    "max_bedrooms": search_params.get('max_bedrooms'),
                    "min_bathrooms": search_params.get('min_bathrooms'),
                    "max_bathrooms": search_params.get('max_bathrooms'),
                    "has_garden": search_params.get('has_garden'),
                    "has_balcony": search_params.get('has_balcony'),
                    "exclude_student_accommodation": search_params.get('exclude_student_accommodation', True),
                    "exclude_house_shares": search_params.get('exclude_house_shares', True),
                    "exclude_retirement": search_params.get('exclude_retirement', True),
                    "keywords": search_params.get('keywords')
                },
                "output_dir": "output",
                "delay_between_requests": 3
            }
            
            # Save temp config
            temp_config_path = os.path.join(os.getcwd(), 'temp_config.json')
            with open(temp_config_path, 'w') as f:
                json_lib.dump(temp_config, f, indent=2)
            
            # Run trawler with temp config
            import sys
            result = subprocess.run([
                sys.executable, 'main.py'
            ], cwd=os.getcwd(), check=True, env={**os.environ, 'CONFIG_FILE': temp_config_path})
            
            # Clean up temp config
            if os.path.exists(temp_config_path):
                os.remove(temp_config_path)
                
        except Exception as e:
            print(f"Error running trawler: {e}")
            import traceback
            traceback.print_exc()
    
    # Run trawler in background thread
    thread = threading.Thread(target=run_trawler_async)
    thread.daemon = True
    thread.start()
    
    return jsonify({
        'status': 'started',
        'message': 'Trawler started with your search criteria. Finding the perfect properties for you!'
    })

if __name__ == '__main__':
    import sys
    print("=" * 60)
    print("Starting Property Trawler Web Server")
    print("=" * 60)
    print(f"\nCurrent directory: {os.getcwd()}")
    print(f"Python executable: {sys.executable}")
    print(f"\nServer will be available at: http://{HOST}:{PORT}")
    print("Press Ctrl+C to stop the server\n")
    
    try:
        app.run(debug=DEBUG, host=HOST, port=PORT, use_reloader=False)
    except OSError as e:
        if "Address already in use" in str(e) or "address is already in use" in str(e).lower():
            alt_port = PORT + 1
            print(f"\n✗ Port {PORT} is already in use. Trying port {alt_port}...")
            app.run(debug=DEBUG, host=HOST, port=alt_port, use_reloader=False)
        else:
            print(f"\n✗ Error: {e}")
            raise
    except Exception as e:
        print(f"\n✗ Error starting server: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

