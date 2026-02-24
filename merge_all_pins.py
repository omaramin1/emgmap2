#!/usr/bin/env python3
"""
Merge ALL VA sales data into one master va_sales_pins.geojson.
Sources:
  1. pins.geojson (4,796 Arcadia sales - geocoded)
  2. va_sales_pins.geojson (1,100 Google Maps + pasted)
  3. geocode_cache.json (partially geocoded KML addresses)
"""

import json
import re
import os

features = []
seen = set()  # deduplicate by rounded coordinates

def coord_key(lng, lat):
    return (round(lng, 5), round(lat, 5))

def add_feature(lng, lat, props, source):
    key = coord_key(lng, lat)
    if key in seen:
        return False
    seen.add(key)
    features.append({
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [lng, lat]},
        "properties": props
    })
    return True

# ======================================
# 1. pins.geojson (Arcadia - 4,796 pins)
# ======================================
arcadia_count = 0
with open('pins.geojson', 'r') as f:
    data = json.load(f)
for feat in data.get('features', []):
    coords = feat['geometry']['coordinates']
    lng, lat = coords[0], coords[1]
    props = feat.get('properties', {})

    # Normalize properties
    normalized = {
        "address": props.get('address', ''),
        "city": props.get('city', ''),
        "state": "VA",
        "zip": props.get('zip', ''),
        "sale_date": props.get('date', ''),
        "type": props.get('type', 'complete'),
        "rep": props.get('rep', ''),
        "status": props.get('status', ''),
        "order_status": props.get('order_status', ''),
        "source": "arcadia"
    }

    if add_feature(lng, lat, normalized, 'arcadia'):
        arcadia_count += 1

print(f"1. Arcadia pins: {arcadia_count} added")

# ======================================
# 2. va_sales_pins.geojson (Google Maps + pasted)
# ======================================
google_count = 0
with open('va_sales_pins.geojson', 'r') as f:
    data = json.load(f)
for feat in data.get('features', []):
    coords = feat['geometry']['coordinates']
    lng, lat = coords[0], coords[1]
    props = feat.get('properties', {})

    normalized = {
        "address": props.get('address', ''),
        "city": props.get('city', ''),
        "state": "VA",
        "zip": props.get('zip', ''),
        "sale_date": props.get('sale_date', ''),
        "type": props.get('type', 'complete'),
        "source": "google_maps"
    }

    if add_feature(lng, lat, normalized, 'google_maps'):
        google_count += 1

print(f"2. Google Maps/pasted pins: {google_count} added")

# ======================================
# 3. geocode_cache.json (geocoded KML addresses)
# ======================================
geocode_count = 0
if os.path.exists('geocode_cache.json'):
    with open('geocode_cache.json', 'r') as f:
        cache = json.load(f)

    for addr, coords in cache.items():
        if coords[0] is not None and coords[1] is not None:
            lat, lng = coords[0], coords[1]

            # Parse address
            parts = [p.strip() for p in addr.split(',')]
            street = parts[0] if parts else addr
            city = ''
            zip_code = ''

            for part in parts[1:]:
                part = part.strip()
                if part.upper() not in ['VA', 'VIRGINIA', ''] and not re.match(r'^\d{5}$', part):
                    if not city:
                        city = part
                z = re.search(r'(\d{5})', part)
                if z:
                    zip_code = z.group(1)

            normalized = {
                "address": street,
                "city": city,
                "state": "VA",
                "zip": zip_code,
                "type": "complete",
                "source": "kml_geocoded"
            }

            if add_feature(lng, lat, normalized, 'kml'):
                geocode_count += 1

print(f"3. Geocoded KML addresses: {geocode_count} added")

# ======================================
# SAVE MASTER FILE
# ======================================
master = {
    "type": "FeatureCollection",
    "features": features
}

with open('va_sales_pins.geojson', 'w') as f:
    json.dump(master, f)

total = len(features)
print(f"\n{'='*40}")
print(f"MASTER FILE: va_sales_pins.geojson")
print(f"Total unique pins: {total}")
print(f"  Arcadia:    {arcadia_count}")
print(f"  Google Maps: {google_count}")
print(f"  KML geocoded: {geocode_count}")
print(f"{'='*40}")

# Stats by type
types = {}
for f in features:
    t = f['properties'].get('type', 'unknown')
    types[t] = types.get(t, 0) + 1
print("\nBy type:")
for t, c in sorted(types.items(), key=lambda x: -x[1]):
    print(f"  {t}: {c}")

# Stats by source
sources = {}
for f in features:
    s = f['properties'].get('source', 'unknown')
    sources[s] = sources.get(s, 0) + 1
print("\nBy source:")
for s, c in sorted(sources.items(), key=lambda x: -x[1]):
    print(f"  {s}: {c}")
