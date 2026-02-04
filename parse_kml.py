#!/usr/bin/env python3
"""
Parse KML file and extract addresses.
Then geocode them using a free service.
"""

import xml.etree.ElementTree as ET
import json
import re
import time
import urllib.request
import urllib.parse

def parse_kml(filename):
    """Extract addresses from KML file."""
    tree = ET.parse(filename)
    root = tree.getroot()

    # KML namespace
    ns = {'kml': 'http://www.opengis.net/kml/2.2'}

    addresses = []
    for placemark in root.findall('.//kml:Placemark', ns):
        addr_elem = placemark.find('kml:address', ns)
        name_elem = placemark.find('kml:name', ns)

        address = addr_elem.text if addr_elem is not None else (name_elem.text if name_elem is not None else None)

        if address:
            addresses.append(address.strip())

    return addresses

def parse_address(full_address):
    """Parse address into components."""
    # Pattern: "123 Street Name, City, VA, 23456"
    parts = [p.strip() for p in full_address.split(',')]

    result = {
        'full': full_address,
        'street': parts[0] if len(parts) > 0 else '',
        'city': parts[-3] if len(parts) >= 3 else (parts[1] if len(parts) > 1 else ''),
        'state': 'VA',
        'zip': ''
    }

    # Extract zip code (5 digits)
    zip_match = re.search(r'\b(\d{5})\b', full_address)
    if zip_match:
        result['zip'] = zip_match.group(1)

    # Clean up city
    if result['city'] and result['city'].upper() in ['VA', 'VIRGINIA']:
        result['city'] = parts[-4] if len(parts) >= 4 else ''

    return result

def geocode_nominatim(address, delay=1.0):
    """Geocode using free Nominatim API (OpenStreetMap)."""
    try:
        encoded = urllib.parse.quote(address)
        url = f"https://nominatim.openstreetmap.org/search?q={encoded}&format=json&limit=1"

        req = urllib.request.Request(url, headers={'User-Agent': 'EMG-Field-Ops/1.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())

            if data and len(data) > 0:
                return float(data[0]['lat']), float(data[0]['lon'])
    except Exception as e:
        print(f"  Geocode error for {address[:40]}...: {e}")

    time.sleep(delay)  # Rate limiting
    return None, None

def main():
    print("Parsing KML file...")
    addresses = parse_kml('doc.kml')
    print(f"Found {len(addresses)} addresses")

    # Parse and deduplicate
    unique_addresses = list(set(addresses))
    print(f"Unique addresses: {len(unique_addresses)}")

    # Save addresses to file for inspection
    with open('va_addresses.txt', 'w') as f:
        for addr in sorted(unique_addresses):
            f.write(addr + '\n')
    print("Saved addresses to va_addresses.txt")

    # Create features (without geocoding for now - too slow)
    features = []
    for addr in unique_addresses:
        parsed = parse_address(addr)

        # For now, skip geocoding - we'll need the coordinates from elsewhere
        # or use batch geocoding service
        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [0, 0]  # Placeholder - needs geocoding
            },
            "properties": {
                "address": parsed['street'],
                "city": parsed['city'],
                "state": parsed['state'],
                "zip": parsed['zip'],
                "full_address": parsed['full'],
                "type": "complete",
                "needs_geocoding": True
            }
        })

    # Save as GeoJSON (without coordinates yet)
    geojson = {
        "type": "FeatureCollection",
        "features": features
    }

    with open('va_sales_addresses.json', 'w') as f:
        json.dump(geojson, f, indent=2)

    print(f"\nSaved {len(features)} addresses to va_sales_addresses.json")
    print("NOTE: Coordinates need to be added via geocoding")

    # Show sample
    print("\nSample addresses:")
    for addr in unique_addresses[:10]:
        parsed = parse_address(addr)
        print(f"  {parsed['street']}, {parsed['city']}, {parsed['state']} {parsed['zip']}")

if __name__ == '__main__':
    main()
