#!/usr/bin/env python3
"""
Build master va_sales_pins.geojson with ALL data from every source.
Deduplicates by coordinates. Preserves all rich properties.
"""

import json
import re
import os

features = []
seen = set()

def coord_key(lng, lat):
    return (round(lng, 5), round(lat, 5))

def add_feature(lng, lat, props):
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

# ===== 1. pins.geojson (Arcadia - richest data) =====
arcadia_count = 0
with open('pins.geojson', 'r') as f:
    data = json.load(f)
for feat in data.get('features', []):
    coords = feat['geometry']['coordinates']
    lng, lat = coords[0], coords[1]
    props = feat.get('properties', {})

    normalized = {
        "address": props.get('address', ''),
        "city": props.get('city', '').title(),
        "state": "VA",
        "zip": props.get('zip', ''),
        "sale_date": props.get('date', ''),
        "type": props.get('type', 'complete'),
        "rep": props.get('rep', '').strip(),
        "status": props.get('status', ''),
        "order_status": props.get('order_status', ''),
        "dwelling": props.get('dwelling', ''),
        "lmi_type": props.get('lmi_type', ''),
        "source": "arcadia"
    }

    if add_feature(lng, lat, normalized):
        arcadia_count += 1

print(f"1. Arcadia pins: {arcadia_count}")

# ===== 2. Current va_sales_pins.geojson (Google Maps + pasted) =====
google_count = 0
with open('va_sales_pins.geojson', 'r') as f:
    data = json.load(f)
for feat in data.get('features', []):
    coords = feat['geometry']['coordinates']
    lng, lat = coords[0], coords[1]
    props = feat.get('properties', {})

    # Skip if already from arcadia (we got richer data above)
    if props.get('source') == 'arcadia':
        continue

    normalized = {
        "address": props.get('address', ''),
        "city": props.get('city', '').title() if props.get('city') else '',
        "state": "VA",
        "zip": props.get('zip', ''),
        "sale_date": props.get('sale_date', ''),
        "type": props.get('type', 'complete'),
        "source": props.get('source', 'google_maps')
    }

    if add_feature(lng, lat, normalized):
        google_count += 1

print(f"2. Google Maps/pasted: {google_count}")

# ===== 3. geocode_cache.json =====
geocode_count = 0
if os.path.exists('geocode_cache.json'):
    with open('geocode_cache.json', 'r') as f:
        cache = json.load(f)

    for addr, coords in cache.items():
        if coords[0] is not None and coords[1] is not None:
            lat, lng = coords[0], coords[1]
            parts = [p.strip() for p in addr.split(',')]
            street = parts[0] if parts else addr
            city = ''
            zip_code = ''
            for part in parts[1:]:
                p = part.strip()
                if p and p.upper() not in ['VA', 'VIRGINIA', ''] and not re.match(r'^\d{5}$', p):
                    if not city:
                        city = p
                z = re.search(r'(\d{5})', part)
                if z:
                    zip_code = z.group(1)

            if add_feature(lng, lat, {
                "address": street,
                "city": city,
                "state": "VA",
                "zip": zip_code,
                "type": "complete",
                "source": "vipr_scraped"
            }):
                geocode_count += 1

print(f"3. VIPR/KML geocoded: {geocode_count}")

# ===== SAVE =====
master = {"type": "FeatureCollection", "features": features}
with open('va_sales_pins.geojson', 'w') as f:
    json.dump(master, f)

total = len(features)
print(f"\n{'='*40}")
print(f"TOTAL UNIQUE PINS: {total}")
print(f"{'='*40}")

# Stats
types = {}
lmi_types = {}
dwellings = {}
sources = {}
for f in features:
    p = f['properties']
    types[p.get('type', '?')] = types.get(p.get('type', '?'), 0) + 1
    sources[p.get('source', '?')] = sources.get(p.get('source', '?'), 0) + 1
    if p.get('lmi_type'):
        lt = p['lmi_type'].split('(')[0].strip()
        lmi_types[lt] = lmi_types.get(lt, 0) + 1
    if p.get('dwelling'):
        dwellings[p['dwelling']] = dwellings.get(p['dwelling'], 0) + 1

print("\nBy type:")
for t, c in sorted(types.items(), key=lambda x: -x[1]):
    print(f"  {t}: {c}")

print("\nBy source:")
for s, c in sorted(sources.items(), key=lambda x: -x[1]):
    print(f"  {s}: {c}")

print("\nBy LMI qualification:")
for t, c in sorted(lmi_types.items(), key=lambda x: -x[1]):
    print(f"  {t}: {c}")

print("\nBy dwelling type:")
for d, c in sorted(dwellings.items(), key=lambda x: -x[1]):
    print(f"  {d}: {c}")
