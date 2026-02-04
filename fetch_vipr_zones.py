#!/usr/bin/env python3
"""
VIPR Zone Fetcher - Downloads LMI census tracts from TIGERweb API
Matches the VA Low Income Housing zones shown in VIPR portal.

Usage:
    python fetch_vipr_zones.py [--region REGION] [--output FILE]

Regions: hampton_roads, richmond, petersburg, lynchburg, nova, all
"""

import argparse
import geopandas as gpd
import pandas as pd
import requests
import json
import os
from pathlib import Path

# County FIPS codes by region (Dominion Energy Virginia territory)
REGIONS = {
    "hampton_roads": {
        "550": "Chesapeake", "710": "Norfolk", "810": "Virginia Beach",
        "740": "Portsmouth", "650": "Hampton", "700": "Newport News",
        "800": "Suffolk", "093": "Isle of Wight", "175": "Southampton",
        "095": "James City", "199": "York", "073": "Gloucester", "115": "Mathews"
    },
    "richmond": {
        "760": "Richmond City", "087": "Henrico", "041": "Chesterfield",
        "085": "Hanover", "036": "Charles City", "127": "New Kent",
        "075": "Goochland", "145": "Powhatan", "570": "Colonial Heights", "670": "Hopewell"
    },
    "petersburg": {
        "730": "Petersburg", "149": "Prince George", "053": "Dinwiddie",
        "025": "Brunswick", "081": "Greensville", "595": "Emporia",
        "183": "Sussex", "181": "Surry", "117": "Mecklenburg",
        "111": "Lunenburg", "135": "Nottoway", "007": "Amelia",
        "147": "Prince Edward", "037": "Charlotte", "083": "Halifax",
        "143": "Pittsylvania", "590": "Danville"
    },
    "lynchburg": {
        "680": "Lynchburg", "031": "Campbell", "009": "Amherst",
        "011": "Appomattox", "019": "Bedford County", "515": "Bedford City",
        "029": "Buckingham", "049": "Cumberland", "065": "Fluvanna",
        "109": "Louisa", "137": "Orange", "003": "Albemarle",
        "540": "Charlottesville", "079": "Greene", "113": "Madison",
        "157": "Rappahannock", "047": "Culpeper", "061": "Fauquier"
    },
    "nova": {
        "059": "Fairfax", "600": "Fairfax City", "610": "Falls Church",
        "013": "Arlington", "510": "Alexandria", "153": "Prince William",
        "683": "Manassas", "685": "Manassas Park", "107": "Loudoun",
        "177": "Spotsylvania", "630": "Fredericksburg", "179": "Stafford"
    },
    "northern_neck": {
        "103": "Lancaster", "133": "Northumberland", "159": "Richmond County",
        "193": "Westmoreland", "057": "Essex", "097": "King and Queen",
        "099": "King George", "101": "King William", "119": "Middlesex", "033": "Caroline"
    }
}


def fetch_tracts_for_county(county_fips: str, county_name: str) -> gpd.GeoDataFrame:
    """Fetch all census tracts for a county from TIGERweb API."""
    url = (
        f"https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/"
        f"tigerWMS_Current/MapServer/8/query"
        f"?where=STATE%3D%2751%27%20AND%20COUNTY%3D%27{county_fips}%27"
        f"&outFields=GEOID,NAME,STATE,COUNTY,CENTLAT,CENTLON,AREALAND"
        f"&f=geojson"
    )

    try:
        resp = requests.get(url, timeout=30)
        if resp.status_code == 200:
            data = resp.json()
            if data.get('features'):
                gdf = gpd.GeoDataFrame.from_features(data['features'], crs="EPSG:4326")
                gdf['COUNTY_NAME'] = county_name
                return gdf
    except Exception as e:
        print(f"    Error fetching {county_name}: {e}")

    return None


def simplify_geometry(gdf: gpd.GeoDataFrame, tolerance: float = 0.001) -> gpd.GeoDataFrame:
    """Simplify polygon geometry to reduce file size."""
    gdf = gdf.copy()
    gdf['geometry'] = gdf['geometry'].simplify(tolerance, preserve_topology=True)
    return gdf


def fetch_region(region_name: str, simplify: bool = True) -> gpd.GeoDataFrame:
    """Fetch all tracts for a region."""
    if region_name == 'all':
        counties = {}
        for r in REGIONS.values():
            counties.update(r)
    else:
        counties = REGIONS.get(region_name, {})

    if not counties:
        print(f"Unknown region: {region_name}")
        print(f"Available: {', '.join(REGIONS.keys())}, all")
        return None

    print(f"Fetching {len(counties)} counties for {region_name}...")
    all_tracts = []

    for fips, name in sorted(counties.items()):
        print(f"  {name} ({fips})...", end=" ", flush=True)
        tracts = fetch_tracts_for_county(fips, name)
        if tracts is not None and len(tracts) > 0:
            all_tracts.append(tracts)
            print(f"{len(tracts)} tracts")
        else:
            print("failed")

    if not all_tracts:
        return None

    combined = pd.concat(all_tracts, ignore_index=True)
    combined = gpd.GeoDataFrame(combined, geometry='geometry', crs="EPSG:4326")

    if simplify:
        print("Simplifying geometry...")
        combined = simplify_geometry(combined, tolerance=0.002)

    return combined


def main():
    parser = argparse.ArgumentParser(description='Fetch VIPR LMI zones')
    parser.add_argument('--region', default='all', help='Region to fetch')
    parser.add_argument('--output', default='blue_zones.geojson', help='Output file')
    parser.add_argument('--no-simplify', action='store_true', help='Skip geometry simplification')
    args = parser.parse_args()

    zones = fetch_region(args.region, simplify=not args.no_simplify)

    if zones is not None:
        print(f"\nTotal zones: {len(zones)}")
        zones.to_file(args.output, driver='GeoJSON')

        size_mb = os.path.getsize(args.output) / 1024 / 1024
        print(f"Saved: {args.output} ({size_mb:.1f} MB)")

        # Summary by county
        print("\nZones by county:")
        for county in sorted(zones['COUNTY_NAME'].unique()):
            count = len(zones[zones['COUNTY_NAME'] == county])
            print(f"  {county}: {count}")


if __name__ == "__main__":
    main()
