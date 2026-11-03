import os
import psycopg2

DB_HOST = os.getenv("DB_HOST", "postgis")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("POSTGRES_DB", "psip")
DB_USER = os.getenv("POSTGRES_USER", "psip")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "psip")

RESOLUTIONS = [7, 8, 9]

WEIGHTS = {
    "ot_bubd_a_area_norm": -0.8,
    "ot_skdr_l_length_norm": 0.9,
    "ot_ptlz_a_area_norm": -0.7
}

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
    table = f"grid.h3_grid_{resolution}_bdot"

    print(f"\n=== IOP H3 {resolution} ===")

    cur.execute(f"""
        ALTER TABLE {table}
        ADD COLUMN IF NOT EXISTS iop_raw double precision DEFAULT 0;
    """)

    parts = []

    for column, weight in WEIGHTS.items():
        parts.append(f"COALESCE({column}, 0) * {weight}")

    expression = " + ".join(parts)

    cur.execute(f"""
        UPDATE {table}
        SET iop_raw = {expression};
    """)

    cur.execute(f"""
        ALTER TABLE {table}
        ADD COLUMN IF NOT EXISTS iop_norm double precision DEFAULT 0;
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

    print(f"Gotowe: {table}")

cur.close()
conn.close()

print("\nIOP policzony dla H3 7, 8 i 9.")