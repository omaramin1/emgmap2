#!/usr/bin/env python3
"""
Geocode VA addresses using Nominatim (OpenStreetMap) API.
"""

import json
import time
import urllib.request
import urllib.parse
import re
import os

def geocode_nominatim(address):
    """Geocode using Nominatim API."""
    try:
        encoded = urllib.parse.quote(address)
        url = f"https://nominatim.openstreetmap.org/search?q={encoded}&format=json&limit=1&countrycodes=us"

        req = urllib.request.Request(url, headers={'User-Agent': 'EMG-Field-Ops/1.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())

            if data and len(data) > 0:
                return float(data[0]['lat']), float(data[0]['lon'])
    except Exception as e:
        pass

    return None, None

def parse_address(full_address):
    """Parse address into components."""
    parts = [p.strip() for p in full_address.split(',')]

    result = {
        'full': full_address,
        'street': parts[0] if len(parts) > 0 else '',
        'city': '',
        'state': 'VA',
        'zip': ''
    }

    # Extract zip code
    zip_match = re.search(r'\b(\d{5})\b', full_address)
    if zip_match:
        result['zip'] = zip_match.group(1)

    # City is usually the second-to-last or third-to-last part
    for part in parts[1:-1]:
        part = part.strip()
        if part and part.upper() not in ['VA', 'VIRGINIA'] and not part.isdigit():
            result['city'] = part
            break

    return result

def main():
    # Load addresses
    with open('va_addresses.txt', 'r') as f:
        addresses = [line.strip() for line in f if line.strip()]

    print(f"Total addresses to geocode: {len(addresses)}")

    # Load existing geocoded data if any
    cache_file = 'geocode_cache.json'
    if os.path.exists(cache_file):
        with open(cache_file, 'r') as f:
            cache = json.load(f)
        print(f"Loaded {len(cache)} cached geocodes")
    else:
        cache = {}

    features = []
    geocoded = 0
    cached = 0
    failed = 0

    for i, addr in enumerate(addresses):
        parsed = parse_address(addr)

        # Check cache first
        if addr in cache:
            lat, lng = cache[addr]
            cached += 1
        else:
            # Geocode
            lat, lng = geocode_nominatim(addr)

            if lat and lng:
                cache[addr] = [lat, lng]
                geocoded += 1
                # Rate limit - 1 request per second for Nominatim
                time.sleep(1.0)
            else:
                cache[addr] = [None, None]
                failed += 1
                time.sleep(0.5)

        # Create feature if we have coordinates
        if lat and lng:
            features.append({
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [lng, lat]
                },
                "properties": {
                    "address": parsed['street'],
                    "city": parsed['city'],
                    "state": "VA",
                    "zip": parsed['zip'],
                    "full_address": addr,
                    "type": "complete"
                }
            })

        # Progress update
        if (i + 1) % 50 == 0:
            print(f"Progress: {i+1}/{len(addresses)} (geocoded: {geocoded}, cached: {cached}, failed: {failed})")
            # Save cache periodically
            with open(cache_file, 'w') as f:
                json.dump(cache, f)

    # Save final cache
    with open(cache_file, 'w') as f:
        json.dump(cache, f)

    # Save GeoJSON
    geojson = {
        "type": "FeatureCollection",
        "features": features
    }

    with open('va_sales_geocoded.geojson', 'w') as f:
        json.dump(geojson, f)

    print(f"\n=== COMPLETE ===")
    print(f"Total addresses: {len(addresses)}")
    print(f"Successfully geocoded: {len(features)}")
    print(f"From cache: {cached}")
    print(f"New geocodes: {geocoded}")
    print(f"Failed: {failed}")
    print(f"Saved to va_sales_geocoded.geojson")

if __name__ == '__main__':
    main()
