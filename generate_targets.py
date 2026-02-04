#!/usr/bin/env python3
"""
Target Generator - Creates ranked door-knocking targets from LMI zones.

Uses census data + property records to score and rank addresses for canvassing.
Outputs JSON suitable for the web app.

Scoring Algorithm:
- LMI Zone: +30 points (auto-qualify for state benefit)
- High kWh (>1200): +20 points (bigger savings = easier close)
- Homeowner: +15 points (can make decision)
- Older home (<1990): +10 points (less efficient = more savings)
- Large sqft (>2000): +10 points (higher usage)

Output:
- ranked_targets.json: Ordered list of addresses with scores
- clusters.json: Grouped targets by walkable area
"""

import json
import random
from pathlib import Path

# Sample address database (in production, use property records API)
# These are representative addresses in LMI zones

SAMPLE_ADDRESSES = {
    "hampton_roads": [
        {"street": "123 Ocean View Ave", "city": "Norfolk", "lat": 36.8529, "lng": -76.2859},
        {"street": "456 Chesapeake Blvd", "city": "Norfolk", "lat": 36.8489, "lng": -76.2919},
        {"street": "789 Harbor Dr", "city": "Norfolk", "lat": 36.8509, "lng": -76.2839},
        {"street": "321 Maritime Way", "city": "Norfolk", "lat": 36.8549, "lng": -76.2899},
        {"street": "654 Waterfront St", "city": "Norfolk", "lat": 36.8469, "lng": -76.2879},
        {"street": "987 Shore Rd", "city": "Virginia Beach", "lat": 36.8430, "lng": -76.0300},
        {"street": "147 Atlantic Ave", "city": "Virginia Beach", "lat": 36.8450, "lng": -76.0280},
        {"street": "258 Sandbridge Rd", "city": "Virginia Beach", "lat": 36.8410, "lng": -76.0320},
        {"street": "369 Tidewater Dr", "city": "Chesapeake", "lat": 36.7680, "lng": -76.2870},
        {"street": "741 Deep Creek Blvd", "city": "Chesapeake", "lat": 36.7700, "lng": -76.2850},
    ],
    "richmond": [
        {"street": "100 Church Hill Rd", "city": "Richmond", "lat": 37.5407, "lng": -77.4360},
        {"street": "225 Broad St", "city": "Richmond", "lat": 37.5387, "lng": -77.4320},
        {"street": "450 Grace St", "city": "Richmond", "lat": 37.5427, "lng": -77.4380},
        {"street": "333 Monument Ave", "city": "Richmond", "lat": 37.5550, "lng": -77.4700},
        {"street": "567 Cary St", "city": "Richmond", "lat": 37.5350, "lng": -77.4400},
        {"street": "890 Hull St", "city": "Richmond", "lat": 37.5200, "lng": -77.4500},
        {"street": "123 Laburnum Ave", "city": "Henrico", "lat": 37.5700, "lng": -77.4100},
        {"street": "456 Mechanicsville Tpke", "city": "Henrico", "lat": 37.5750, "lng": -77.3900},
    ],
    "petersburg": [
        {"street": "100 Sycamore St", "city": "Petersburg", "lat": 37.2279, "lng": -77.4020},
        {"street": "200 Washington St", "city": "Petersburg", "lat": 37.2300, "lng": -77.4000},
        {"street": "300 Market St", "city": "Petersburg", "lat": 37.2260, "lng": -77.4040},
        {"street": "400 High St", "city": "Petersburg", "lat": 37.2320, "lng": -77.3980},
    ],
    "lynchburg": [
        {"street": "100 Main St", "city": "Lynchburg", "lat": 37.4138, "lng": -79.1422},
        {"street": "200 Church St", "city": "Lynchburg", "lat": 37.4150, "lng": -79.1400},
        {"street": "300 Court St", "city": "Lynchburg", "lat": 37.4120, "lng": -79.1440},
        {"street": "400 Federal St", "city": "Lynchburg", "lat": 37.4160, "lng": -79.1380},
    ],
}


def score_address(addr: dict) -> int:
    """Calculate door priority score."""
    score = 50  # Base score

    # LMI zone bonus (all our addresses are in LMI zones)
    if addr.get('lmi', True):
        score += 30

    # kWh usage
    kwh = addr.get('kwh', 1000)
    if kwh > 1200:
        score += 20
    elif kwh > 900:
        score += 10

    # Homeowner bonus
    if addr.get('owner', True):
        score += 15

    # Older home bonus (less efficient)
    year = addr.get('year', 1990)
    if year < 1990:
        score += 10
    elif year < 2005:
        score += 5

    # Square footage
    sqft = addr.get('sqft', 1500)
    if sqft > 2000:
        score += 10
    elif sqft > 1500:
        score += 5

    return min(99, score)


def generate_targets(region: str = 'all') -> list:
    """Generate scored targets for a region."""
    targets = []

    if region == 'all':
        regions = SAMPLE_ADDRESSES.keys()
    else:
        regions = [region] if region in SAMPLE_ADDRESSES else []

    for reg in regions:
        for addr in SAMPLE_ADDRESSES.get(reg, []):
            # Simulate property data (in production, fetch from API)
            target = {
                'id': f"{reg}_{len(targets)+1}",
                'address': f"{addr['street']}, {addr['city']}, VA",
                'lat': addr['lat'],
                'lng': addr['lng'],
                'lmi': True,  # All in LMI zones
                'kwh': random.randint(800, 1600),
                'owner': random.random() > 0.3,  # 70% owners
                'sqft': random.randint(1200, 2800),
                'year': random.randint(1960, 2010),
            }
            target['score'] = score_address(target)
            targets.append(target)

    # Sort by score descending
    targets.sort(key=lambda x: x['score'], reverse=True)
    return targets


def generate_clusters(targets: list, cluster_radius: float = 0.005) -> list:
    """Group targets into walkable clusters."""
    clusters = []
    used = set()

    for target in targets:
        if target['id'] in used:
            continue

        # Start new cluster
        cluster = {
            'id': f"cluster_{len(clusters)+1}",
            'center_lat': target['lat'],
            'center_lng': target['lng'],
            'targets': [target],
            'total_score': target['score']
        }
        used.add(target['id'])

        # Add nearby targets
        for other in targets:
            if other['id'] in used:
                continue
            dist = ((other['lat'] - target['lat'])**2 + (other['lng'] - target['lng'])**2)**0.5
            if dist < cluster_radius:
                cluster['targets'].append(other)
                cluster['total_score'] += other['score']
                used.add(other['id'])

        # Calculate cluster center
        lats = [t['lat'] for t in cluster['targets']]
        lngs = [t['lng'] for t in cluster['targets']]
        cluster['center_lat'] = sum(lats) / len(lats)
        cluster['center_lng'] = sum(lngs) / len(lngs)
        cluster['avg_score'] = cluster['total_score'] / len(cluster['targets'])

        clusters.append(cluster)

    # Sort clusters by total score
    clusters.sort(key=lambda x: x['total_score'], reverse=True)
    return clusters


def main():
    output_dir = Path('web-app/public/data')
    output_dir.mkdir(parents=True, exist_ok=True)

    print("Generating targets...")
    targets = generate_targets('all')
    print(f"  {len(targets)} targets generated")

    # Save targets
    targets_file = output_dir / 'ranked_targets.json'
    with open(targets_file, 'w') as f:
        json.dump(targets, f, indent=2)
    print(f"  Saved: {targets_file}")

    # Generate and save clusters
    print("\nGenerating clusters...")
    clusters = generate_clusters(targets)
    print(f"  {len(clusters)} clusters generated")

    clusters_file = output_dir / 'ranked_clusters.json'
    with open(clusters_file, 'w') as f:
        json.dump(clusters, f, indent=2)
    print(f"  Saved: {clusters_file}")

    # Summary
    print("\n" + "="*50)
    print("TOP 10 TARGETS:")
    print("="*50)
    for i, t in enumerate(targets[:10], 1):
        print(f"{i:2}. [{t['score']}] {t['address']}")
        print(f"     LMI: {'Yes' if t['lmi'] else 'No'} | kWh: {t['kwh']} | Owner: {'Yes' if t['owner'] else 'No'}")

    print("\n" + "="*50)
    print("TOP 5 CLUSTERS:")
    print("="*50)
    for i, c in enumerate(clusters[:5], 1):
        print(f"{i}. Cluster {c['id']} - {len(c['targets'])} doors, avg score {c['avg_score']:.0f}")


if __name__ == "__main__":
    main()
