"""
Download geological map (SGI ISPRA 1:100k) for the Campania bbox.

Strategy:
  1. Fetch all OBJECTID_1 values intersecting Campania in one lightweight call.
  2. Batch-fetch geometry + attributes in chunks of 2000 using
     WHERE OBJECTID_1 IN (...) — avoids offset pagination which the server
     can't handle past ~8000 results.
"""
import json
import time
import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE      = "https://sinacloud.isprambiente.it/arcgisgeo/rest/services/geo/SGI_ISPRA_geologia100K/MapServer"
LAYER_ID  = 14
BBOX      = "13.8,39.9,15.8,41.5"
BATCH     = 2000


def get_all_ids() -> list[int]:
    r = requests.get(f"{BASE}/{LAYER_ID}/query", params={
        "where": "1=1",
        "geometry": BBOX,
        "geometryType": "esriGeometryEnvelope",
        "inSR": "4326",
        "spatialRel": "esriSpatialRelIntersects",
        "returnIdsOnly": "true",
        "f": "json",
    }, verify=False, timeout=30)
    r.raise_for_status()
    data = r.json()
    if "error" in data:
        raise RuntimeError(f"ArcGIS error: {data['error']}")
    return data["objectIds"]


def fetch_batch(ids: list[int], retries: int = 3) -> list | None:
    id_str = ",".join(str(i) for i in ids)
    data = {
        "where": f"OBJECTID_1 IN ({id_str})",
        "outFields": "*",
        "returnGeometry": "true",
        "f": "geojson",
    }
    for attempt in range(retries):
        try:
            r = requests.post(f"{BASE}/{LAYER_ID}/query", data=data,
                              verify=False, timeout=120)
            r.raise_for_status()
            data = r.json()
            if "error" in data:
                raise RuntimeError(f"ArcGIS error: {data['error']}")
            return data.get("features", [])
        except Exception as e:
            wait = 10 * (attempt + 1)
            print(f"  Attempt {attempt + 1}/{retries} failed: {e} — retrying in {wait}s", flush=True)
            if attempt < retries - 1:
                time.sleep(wait)
    print(f"  SKIPPING batch of {len(ids)} IDs after {retries} failures", flush=True)
    return None


def main():
    print("Fetching IDs for Campania bbox …", flush=True)
    all_ids = get_all_ids()
    print(f"  {len(all_ids)} features to download", flush=True)

    batches = [all_ids[i:i + BATCH] for i in range(0, len(all_ids), BATCH)]
    print(f"  {len(batches)} batches of up to {BATCH}", flush=True)

    all_features = []
    failed_batches = 0

    for i, batch in enumerate(batches, 1):
        features = fetch_batch(batch)
        if features is None:
            failed_batches += 1
            print(f"  [{i:02d}/{len(batches)}] FAILED", flush=True)
        else:
            all_features.extend(features)
            print(f"  [{i:02d}/{len(batches)}] got {len(features)} features (total {len(all_features)})", flush=True)

    print(f"\nTotal features: {len(all_features)}")
    if failed_batches:
        print(f"WARNING: {failed_batches} batches failed — output is incomplete")

    out_path = "data/geological-map/geology_campania.geojson"
    with open(out_path, "w") as f:
        json.dump({"type": "FeatureCollection", "features": all_features}, f)
    print(f"Saved → {out_path}")


if __name__ == "__main__":
    main()
