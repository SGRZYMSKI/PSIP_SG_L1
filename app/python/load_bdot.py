import os
import re
import subprocess
from pathlib import Path

BDOT_DIR = Path("/data/bdot/3027_GML")

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

if not BDOT_DIR.exists():
    raise FileNotFoundError(f"Nie znaleziono katalogu: {BDOT_DIR}")

create_schema = [
    "ogrinfo",
    connection,
    "-sql",
    "CREATE SCHEMA IF NOT EXISTS bdot"
]

subprocess.run(
    create_schema,
    env=environment,
    check=True
)

xml_files = [
    path
    for path in BDOT_DIR.rglob("*.xml")
    if path.parent.name == "BDOT10k"
]

if not xml_files:
    raise FileNotFoundError("Nie znaleziono plikow BDOT10k XML.")

print(f"Znaleziono {len(xml_files)} warstw BDOT10k.")

loaded = 0
errors = 0

for xml_file in sorted(xml_files):

    match = re.search(
        r"__OT_([A-Z0-9]+)_([ALP])\.xml$",
        xml_file.name
    )

    if not match:
        print(f"Pominieto: {xml_file.name}")
        continue

    layer_code = match.group(1).lower()
    geometry_type = match.group(2).lower()

    table_name = f"ot_{layer_code}_{geometry_type}"

    command = [
        "ogr2ogr",
        "-f",
        "PostgreSQL",
        connection,
        str(xml_file),
        "-nln",
        f"bdot.{table_name}",
        "-lco",
        "GEOMETRY_NAME=geom",
        "-nlt",
        "PROMOTE_TO_MULTI",
        "-overwrite"
    ]

    try:
        subprocess.run(
            command,
            env=environment,
            check=True
        )

        print(
            f"OK: {xml_file.name} -> "
            f"bdot.{table_name}"
        )

        loaded += 1

    except subprocess.CalledProcessError:
        print(f"BLAD: {xml_file.name}")
        errors += 1

print()
print(f"Zaladowano warstw: {loaded}")
print(f"Bledy: {errors}")