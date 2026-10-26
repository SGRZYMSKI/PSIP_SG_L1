import os
import psycopg2

DB_HOST = os.getenv("DB_HOST", "postgis")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("POSTGRES_DB", "psip")
DB_USER = os.getenv("POSTGRES_USER", "psip")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "psip")

conn = psycopg2.connect(
    host=DB_HOST,
    port=DB_PORT,
    dbname=DB_NAME,
    user=DB_USER,
    password=DB_PASSWORD
)

conn.autocommit = True
cur = conn.cursor()

grid_table = "grid.h3_grid_8"

cur.execute("""
    SELECT table_name
    FROM information_schema.tables
    WHERE table_schema = 'bdot'
    ORDER BY table_name
""")

tables = [row[0] for row in cur.fetchall()]

polygon_tables = [t for t in tables if t.endswith("_a")]
line_tables = [t for t in tables if t.endswith("_l")]
point_tables = [t for t in tables if t.endswith("_p")]

print(f"Poligony: {len(polygon_tables)}")
print(f"Linie: {len(line_tables)}")
print(f"Punkty: {len(point_tables)}")

cur.execute("""
    DROP TABLE IF EXISTS grid.h3_grid_8_bdot;

    CREATE TABLE grid.h3_grid_8_bdot AS
    SELECT
        h3_id,
        resolution,
        geom
    FROM grid.h3_grid_8;
""")

for table in polygon_tables:
    column = f"{table}_area"

    cur.execute(f"""
        ALTER TABLE grid.h3_grid_8_bdot
        ADD COLUMN IF NOT EXISTS {column}
        double precision DEFAULT 0;
    """)

    cur.execute(f"""
        UPDATE grid.h3_grid_8_bdot g
        SET {column} = x.value
        FROM (
            SELECT
                g2.h3_id,
                COALESCE(
                    SUM(
                        ST_Area(
                            ST_Intersection(
                                ST_Transform(g2.geom, 2180),
                                b.geom
                            )
                        )
                    ),
                    0
                ) AS value
            FROM grid.h3_grid_8_bdot g2
            LEFT JOIN bdot.{table} b
                ON ST_Intersects(
                    ST_Transform(g2.geom, 2180),
                    b.geom
                )
            GROUP BY g2.h3_id
        ) x
        WHERE g.h3_id = x.h3_id;
    """)

    print(f"Powierzchnia: {table}")

for table in line_tables:
    column = f"{table}_length"

    cur.execute(f"""
        ALTER TABLE grid.h3_grid_8_bdot
        ADD COLUMN IF NOT EXISTS {column}
        double precision DEFAULT 0;
    """)

    cur.execute(f"""
        UPDATE grid.h3_grid_8_bdot g
        SET {column} = x.value
        FROM (
            SELECT
                g2.h3_id,
                COALESCE(
                    SUM(
                        ST_Length(
                            ST_Intersection(
                                ST_Transform(g2.geom, 2180),
                                b.geom
                            )
                        )
                    ),
                    0
                ) AS value
            FROM grid.h3_grid_8_bdot g2
            LEFT JOIN bdot.{table} b
                ON ST_Intersects(
                    ST_Transform(g2.geom, 2180),
                    b.geom
                )
            GROUP BY g2.h3_id
        ) x
        WHERE g.h3_id = x.h3_id;
    """)

    print(f"Dlugosc: {table}")

for table in point_tables:
    column = f"{table}_count"

    cur.execute(f"""
        ALTER TABLE grid.h3_grid_8_bdot
        ADD COLUMN IF NOT EXISTS {column}
        integer DEFAULT 0;
    """)

    cur.execute(f"""
        UPDATE grid.h3_grid_8_bdot g
        SET {column} = x.value
        FROM (
            SELECT
                g2.h3_id,
                COUNT(b.geom)::integer AS value
            FROM grid.h3_grid_8_bdot g2
            LEFT JOIN bdot.{table} b
                ON ST_Intersects(
                    ST_Transform(g2.geom, 2180),
                    b.geom
                )
            GROUP BY g2.h3_id
        ) x
        WHERE g.h3_id = x.h3_id;
    """)

    print(f"Liczba punktow: {table}")

cur.close()
conn.close()

print("Agregacja zakonczona.")