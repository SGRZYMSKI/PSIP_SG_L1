import os
import psycopg2
import geopandas as gpd
import matplotlib.pyplot as plt

DB_HOST = os.getenv("DB_HOST", "postgis")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("POSTGRES_DB", "psip")
DB_USER = os.getenv("POSTGRES_USER", "psip")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "psip")

RESOLUTIONS = [7, 8, 9]

conn_string = (
    f"postgresql://{DB_USER}:{DB_PASSWORD}"
    f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

for resolution in RESOLUTIONS:
    table = f"grid.h3_grid_{resolution}_bdot"

    print(f"Tworzenie mapy H3 {resolution}")

    sql = f"""
        SELECT
            h3_id,
            iop_norm,
            geom
        FROM {table}
    """

    gdf = gpd.read_postgis(
        sql,
        conn_string,
        geom_col="geom"
    )

    fig, ax = plt.subplots(figsize=(12, 12))

    gdf.plot(
        column="iop_norm",
        ax=ax,
        legend=True,
        vmin=0,
        vmax=1,
        cmap="RdYlGn",
        edgecolor="black",
        linewidth=0.1
    )

    ax.set_title(
        f"Mapa przejezdnosci terenu - H3 {resolution}",
        fontsize=16
    )

    ax.set_axis_off()

    output = f"/data/iop_h3_{resolution}.png"

    plt.savefig(
        output,
        dpi=300,
        bbox_inches="tight"
    )

    plt.close()

    print(f"Zapisano: {output}")

print("Wizualizacja zakonczona.")