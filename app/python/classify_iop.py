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
    table = f"grid.h3_grid_{resolution}_bdot"

    print(f"\n=== KLASYFIKACJA H3 {resolution} ===")

    cur.execute(f"""
        ALTER TABLE {table}
        ADD COLUMN IF NOT EXISTS passability_class text;
    """)

    cur.execute(f"""
        UPDATE {table}
        SET passability_class =
            CASE
                WHEN iop_norm < 0.33 THEN 'NO GO'
                WHEN iop_norm < 0.66 THEN 'SLOW GO'
                ELSE 'GO'
            END;
    """)

    print(f"Gotowe: {table}")

cur.close()
conn.close()

print("\nKlasyfikacja zakonczona.")