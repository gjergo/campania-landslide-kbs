import geopandas as gpd

gdf = gpd.read_file("data/geological-map/geology_campania_classified.geojson")
gdf = gdf.to_crs("EPSG:32633")

# Find polygons that touch the suspicious boundary lines
# The tile boundaries are roughly at these UTM northings/eastings
# First let's see the bounding boxes of each polygon to find the tile edges
bounds = gdf.bounds
print("Y extents (northing):")
print(sorted(bounds["maxy"].round(-3).unique())[:20])
print("\nX extents (easting):")  
print(sorted(bounds["maxx"].round(-3).unique())[:20])
