import os

import django
import googlemaps
from django.db import connection


def format_address(address: dict) -> str:
    address_formatted = (
        f"{address['street_address']}, {address['address_locality']}, "
        f"{address['address_region']}, {address['postal_code']}, "
        f"{address['address_country']}"
    )

    return address_formatted


def geocode_locations():
    query_select_addresses = """
-- SQLite
select distinct

    listings.street_address,
    listings.address_locality,
    listings.postal_code,
    listings.address_region,
    listings.address_country

from wgwatch_realestatelisting
    as listings

left join wgwatch_realestatelocation
    as locations

on listings.street_address = locations.street_address
and listings.address_locality = locations.address_locality
and listings.postal_code = locations.postal_code
and listings.address_region = locations.address_region
and listings.address_country = locations.address_country

where locations.street_address is null
"""

    with connection.cursor() as cursor:
        cursor.execute(query_select_addresses)
        columns = [col[0] for col in cursor.description]
        rows = cursor.fetchall()

    addresses = [dict(zip(columns, row)) for row in rows][:10]

    gmaps = googlemaps.Client(key=os.environ.get("GOOGLE_MAPS_API_KEY"))

    for address in addresses:
        address = format_address(address)
        try:
            geocode_result = gmaps.geocode(address)
            if geocode_result:
                latitude = geocode_result[0]["geometry"]["location"]["lat"]
                longitude = geocode_result[0]["geometry"]["location"]["lng"]

                print(f"Geocoded: {address} -> ({latitude}, {longitude})")
            else:
                print(f"Failed to geocode: {address}")
        except Exception as e:
            print(f"Error for {address}: {e}")


def main() -> None:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "wgwatch.settings")
    django.setup()

    geocode_locations()


if __name__ == "__main__":
    main()
