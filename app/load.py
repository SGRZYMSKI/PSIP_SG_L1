import os
import subprocess
from pathlib import Path

POWIAT_FILE = Path("/data/powiat_turecki.shp")
H3_FILE = Path("/data/hexagons.gpkg")

DB_HOST = os.getenv("DB_HOST", "postgis")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("POSTGRES_DB", "psip")
DB_USER = os.getenv("POSTGRES_USER", "psip")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "psip")

connection = (
    f"PG:host={DB_HOST} "
    f"port={DB_PORT} "
    f"dbname={DB_NAME} "
    f"user={DB_USER}"
)

environment = os.environ.copy()
environment["PGPASSWORD"] = DB_PASSWORD

if not POWIAT_FILE.exists():
    raise FileNotFoundError(f"Nie znaleziono pliku: {POWIAT_FILE}")

if not H3_FILE.exists():
    raise FileNotFoundError(f"Nie znaleziono pliku: {H3_FILE}")

create_schema = [
    "ogrinfo",
    connection,
    "-sql",
    "CREATE SCHEMA IF NOT EXISTS grid"
]

subprocess.run(
    create_schema,
    env=environment,
    check=True
)

powiat_command = [
    "ogr2ogr",
    "-f",
    "PostgreSQL",
    connection,
    str(POWIAT_FILE),
    "-nln",
    "powiat",
    "-lco",
    "GEOMETRY_NAME=geom",
    "-overwrite"
]

subprocess.run(
    powiat_command,
    env=environment,
    check=True
)

layers = [
    "h3_grid_7",
    "h3_grid_8",
    "h3_grid_9"
]

for layer in layers:
    command = [
        "ogr2ogr",
        "-f",
        "PostgreSQL",
        connection,
        str(H3_FILE),
        layer,
        "-nln",
        f"grid.{layer}",
        "-lco",
        "GEOMETRY_NAME=geom",
        "-overwrite"
    ]

    subprocess.run(
        command,
        env=environment,
        check=True
    )

    print(f"Załadowano {layer} do schematu grid.")

print("Załadowano powiat oraz wszystkie siatki H3 do bazy.")