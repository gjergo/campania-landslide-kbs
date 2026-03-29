import requests
import geopandas as gpd
import json
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

base = "https://sinacloud.isprambiente.it/arcgisgeo/rest/services/geo/SGI_ISPRA_geologia100K/MapServer"

def query_layer(layer_id, bbox, offset=0):
    url = f"{base}/{layer_id}/query"
    params = {
        "where": "1=1",
        "geometry": f"{bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]}",
        "geometryType": "esriGeometryEnvelope",
        "inSR": "4326",
        "spatialRel": "esriSpatialRelIntersects",
        "outFields": "*",
        "returnGeometry": "true",
        "f": "geojson",
        "resultOffset": offset,
        "resultRecordCount": 1000,
    }
    r = requests.get(url, params=params, verify=False, timeout=60)
    if not r.text.strip():  # empty response = we're done
        return {"features": []}
    try:
        return r.json()
    except requests.exceptions.JSONDecodeError:
        return {"features": []}

bbox = (13.8, 39.9, 15.8, 41.5)

all_features = []
offset = 0
while True:
    data = query_layer(14, bbox, offset)
    features = data.get("features", [])
    print(f"Offset {offset}: got {len(features)} features")
    if not features:
        break
    all_features.extend(features)
    if len(features) < 1000:
        break
    offset += 1000

print(f"Total features: {len(all_features)}")

geojson = {"type": "FeatureCollection", "features": all_features}
with open("data/geological-map/geology_campania.geojson", "w") as f:
    json.dump(geojson, f)

gdf = gpd.read_file("data/geological-map/geology_campania.geojson")
print(gdf.shape)
print(gdf.columns.tolist())
print(gdf.head(3))
