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

for resolution in RESOLUTIONS:
    table_name = f"h3_grid_{resolution}_bdot"
    table = f"grid.{table_name}"

    print(f"\n=== NORMALIZACJA H3 {resolution} ===")

    cur.execute("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = 'grid'
          AND table_name = %s
        ORDER BY ordinal_position
    """, (table_name,))

    columns = [row[0] for row in cur.fetchall()]

    criteria = [
        c for c in columns
        if (
            c.endswith("_area")
            or c.endswith("_length")
            or c.endswith("_count")
        )
        and not c.endswith("_norm")
    ]

    print(f"Liczba kryteriow: {len(criteria)}")

    for column in criteria:
        norm_column = f"{column}_norm"

        cur.execute(f"""
            ALTER TABLE {table}
            ADD COLUMN IF NOT EXISTS {norm_column}
            double precision DEFAULT 0;
        """)

        cur.execute(f"""
            UPDATE {table}
            SET {norm_column} =
                CASE
                    WHEN (
                        SELECT MAX(COALESCE({column}, 0))
                             - MIN(COALESCE({column}, 0))
                        FROM {table}
                    ) = 0
                    THEN 0

                    ELSE (
                        COALESCE({column}, 0)
                        -
                        (
                            SELECT MIN(COALESCE({column}, 0))
                            FROM {table}
                        )
                    )
                    /
                    (
                        (
                            SELECT MAX(COALESCE({column}, 0))
                            FROM {table}
                        )
                        -
                        (
                            SELECT MIN(COALESCE({column}, 0))
                            FROM {table}
                        )
                    )
                END;
        """)

        print(f"OK: {column}")

cur.close()
conn.close()

print("\nNormalizacja zakonczona.")