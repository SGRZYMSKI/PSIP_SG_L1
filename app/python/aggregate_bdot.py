import os
import psycopg2

DB_HOST = os.getenv("DB_HOST", "postgis")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("POSTGRES_DB", "psip")
DB_USER = os.getenv("POSTGRES_USER", "psip")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "psip")

RESOLUTIONS = [7, 8, 9]

conn = psycopg2.connect(
    host=DB_HOST,
    port=DB_PORT,
    dbname=DB_NAME,
    user=DB_USER,
    password=DB_PASSWORD
)

conn.autocommit = True
cur = conn.cursor()

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

for resolution in RESOLUTIONS:
    source_table = f"grid.h3_grid_{resolution}"
    result_table = f"grid.h3_grid_{resolution}_bdot"

    print()
    print(f"=== H3 RESOLUTION {resolution} ===")

    cur.execute(f"""
        DROP TABLE IF EXISTS {result_table};

        CREATE TABLE {result_table} AS
        SELECT
            h3_id,
            resolution,
            ST_Transform(geom, 2180) AS geom
        FROM {source_table};
    """)

    cur.execute(f"""
        ALTER TABLE {result_table}
        ALTER COLUMN geom
        TYPE geometry(Polygon, 2180)
        USING geom;
    """)

    for table in polygon_tables:
        column = f"{table}_area"

        cur.execute(f"""
            ALTER TABLE {result_table}
            ADD COLUMN IF NOT EXISTS {column}
            double precision DEFAULT 0;
        """)

        cur.execute(f"""
            UPDATE {result_table} g
            SET {column} = x.value
            FROM (
                SELECT
                    g2.h3_id,
                    COALESCE(
                        SUM(
                            ST_Area(
                                ST_Intersection(
                                    g2.geom,
                                    b.geom
                                )
                            )
                        ),
                        0
                    ) AS value
                FROM {result_table} g2
                LEFT JOIN bdot.{table} b
                    ON ST_Intersects(g2.geom, b.geom)
                GROUP BY g2.h3_id
            ) x
            WHERE g.h3_id = x.h3_id;
        """)

        print(f"Area: {table}")

    for table in line_tables:
        column = f"{table}_length"

        cur.execute(f"""
            ALTER TABLE {result_table}
            ADD COLUMN IF NOT EXISTS {column}
            double precision DEFAULT 0;
        """)

        cur.execute(f"""
            UPDATE {result_table} g
            SET {column} = x.value
            FROM (
                SELECT
                    g2.h3_id,
                    COALESCE(
                        SUM(
                            ST_Length(
                                ST_Intersection(
                                    g2.geom,
                                    b.geom
                                )
                            )
                        ),
                        0
                    ) AS value
                FROM {result_table} g2
                LEFT JOIN bdot.{table} b
                    ON ST_Intersects(g2.geom, b.geom)
                GROUP BY g2.h3_id
            ) x
            WHERE g.h3_id = x.h3_id;
        """)

        print(f"Length: {table}")

    for table in point_tables:
        column = f"{table}_count"

        cur.execute(f"""
            ALTER TABLE {result_table}
            ADD COLUMN IF NOT EXISTS {column}
            integer DEFAULT 0;
        """)

        cur.execute(f"""
            UPDATE {result_table} g
            SET {column} = x.value
            FROM (
                SELECT
                    g2.h3_id,
                    COUNT(b.geom)::integer AS value
                FROM {result_table} g2
                LEFT JOIN bdot.{table} b
                    ON ST_Intersects(g2.geom, b.geom)
                GROUP BY g2.h3_id
            ) x
            WHERE g.h3_id = x.h3_id;
        """)

        print(f"Count: {table}")

    print(f"Gotowe: {result_table}")

cur.close()
conn.close()

print()
print("Agregacja dla H3 7, 8 i 9 zakonczona.")