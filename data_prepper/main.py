import os

import django
from django.db import connection


def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "wgwatch.settings")
    django.setup()

    with connection.cursor() as cursor:
        print("Creating table latest_realestatelisting_per_day...")
        cursor.execute("""
            DROP TABLE IF EXISTS latest_realestatelisting_per_day;
        """)
        cursor.execute("""
            CREATE TABLE latest_realestatelisting_per_day AS
            SELECT *
            FROM (
                SELECT *,
                    ROW_NUMBER() OVER (
                        PARTITION BY url, DATE(job_insert_time)
                        ORDER BY job_insert_time DESC
                    ) AS rn
                FROM wgwatch_realestatelisting
            ) t
            WHERE t.rn = 1;
        """)

        print("Creating table scrape_dates_by_city...")
        cursor.execute("DROP TABLE IF EXISTS latest_locality_per_day;")
        cursor.execute("""
            CREATE TABLE latest_locality_per_day (
                address_locality TEXT NOT NULL,
                date TEXT NOT NULL,
                PRIMARY KEY (address_locality, date)
            );
        """)
        cursor.execute("""
            INSERT INTO latest_locality_per_day (address_locality, date)
            SELECT
                address_locality,
                DATE(job_insert_time) AS date
            FROM wgwatch_realestatelisting
            GROUP BY address_locality, date;
        """)


if __name__ == "__main__":
    main()
