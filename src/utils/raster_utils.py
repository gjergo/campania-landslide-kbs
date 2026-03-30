"""Shared raster utilities."""
from pathlib import Path

import numpy as np
import geopandas as gpd
from rasterio.features import rasterize

CAMPANIA_PATH = Path("data/campania.geojson")


def campania_mask(profile: dict) -> np.ndarray:
    """Boolean mask where True = outside Campania boundary.

    Rasterizes data/campania.geojson onto the given raster profile.
    Use to stamp nodata onto all out-of-region pixels.
    """
    gdf = gpd.read_file(CAMPANIA_PATH).to_crs("EPSG:32633")
    shapes = (
        (geom, 1)
        for geom in gdf.geometry
        if geom is not None and not geom.is_empty
    )
    inside = rasterize(
        shapes=shapes,
        out_shape=(profile["height"], profile["width"]),
        transform=profile["transform"],
        fill=0,
        dtype="uint8",
    )
    return inside == 0  # True where outside Campania
