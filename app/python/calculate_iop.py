import os
import psycopg2
from iop_weights import WEIGHTS

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

print(f"Liczba wag IVRF: {len(WEIGHTS)}")

for resolution in RESOLUTIONS:
    table_name = f"h3_grid_{resolution}_bdot"
    table = f"grid.{table_name}"

    print(f"\n=== IOP H3 {resolution} ===")

    cur.execute("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = 'grid'
          AND table_name = %s
    """, (table_name,))

    existing_columns = {row[0] for row in cur.fetchall()}

    used_weights = {
        column: weight
        for column, weight in WEIGHTS.items()
        if column in existing_columns
    }

    missing = [
        column
        for column in WEIGHTS
        if column not in existing_columns
    ]

    print(f"Kryteria wykorzystane: {len(used_weights)}")

    if missing:
        print("Brakujace kolumny:")
        for column in missing:
            print(column)

    cur.execute(f"""
        ALTER TABLE {table}
        ADD COLUMN IF NOT EXISTS iop_raw
        double precision DEFAULT 0;
    """)

    expression = " + ".join(
        f"COALESCE({column}, 0) * ({weight})"
        for column, weight in used_weights.items()
    )

    cur.execute(f"""
        UPDATE {table}
        SET iop_raw = {expression};
    """)

    cur.execute(f"""
        ALTER TABLE {table}
        ADD COLUMN IF NOT EXISTS iop_norm
        double precision DEFAULT 0;
    """)

    cur.execute(f"""
        UPDATE {table}
        SET iop_norm =
            CASE
                WHEN (
                    SELECT MAX(iop_raw) - MIN(iop_raw)
                    FROM {table}
                ) = 0
                THEN 0
                ELSE
                    (
                        iop_raw -
                        (
                            SELECT MIN(iop_raw)
                            FROM {table}
                        )
                    )
                    /
                    (
                        (
                            SELECT MAX(iop_raw)
                            FROM {table}
                        )
                        -
                        (
                            SELECT MIN(iop_raw)
                            FROM {table}
                        )
                    )
            END;
    """)

    cur.execute(f"""
        SELECT
            MIN(iop_raw),
            MAX(iop_raw),
            MIN(iop_norm),
            MAX(iop_norm)
        FROM {table};
    """)

    result = cur.fetchone()

    print(f"IOP raw: {result[0]:.4f} - {result[1]:.4f}")
    print(f"IOP norm: {result[2]:.4f} - {result[3]:.4f}")
    print(f"Gotowe: {table}")

cur.close()
conn.close()

print("\nIOP policzony dla wszystkich 61 kryteriow.")