import geopandas as gpd
import h3
from shapely.geometry import Polygon

INPUT_FILE = "/data/powiat.shp"
OUTPUT_FILE = "/data/hexagons.gpkg"

H3_RESOLUTIONS = [7, 8, 9]

gdf = gpd.read_file(INPUT_FILE)
gdf = gdf.to_crs(4326)

geom = gdf.geometry.union_all()

for resolution in H3_RESOLUTIONS:
    hex_ids = h3.geo_to_cells(
        geom,
        res=resolution
    )

    hex_geoms = []

    for h in hex_ids:
        boundary = h3.cell_to_boundary(h)

        poly = Polygon(
            [(lon, lat) for lat, lon in boundary]
        )

        hex_geoms.append({
            "h3_id": h,
            "resolution": resolution,
            "geometry": poly
        })

    hex_gdf = gpd.GeoDataFrame(
        hex_geoms,
        crs="EPSG:4326"
    )

    hex_gdf.to_file(
        OUTPUT_FILE,
        layer=f"h3_grid_{resolution}",
        driver="GPKG"
    )

    print(
        f"Rozdzielczosc {resolution}: "
        f"wygenerowano {len(hex_gdf)} heksagonow"
    )