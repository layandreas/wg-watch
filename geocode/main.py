import logging
import multiprocessing
import os

import django
from django.db import connection
from googlemaps import Client as GoogleMapsClient

logger = logging.getLogger(__name__)


def _format_address(address: dict) -> str:
    address_formatted = (
        f"{address['street_address']}, {address['address_locality']}, "
        f"{address['address_region']}, {address['postal_code']}, "
        f"{address['address_country']}"
    )

    return address_formatted


def _load_addresses() -> list[dict]:
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

    addresses = [dict(zip(columns, row)) for row in rows]

    return addresses


def geocode_locations(
    gmaps_client: GoogleMapsClient, addresses: list[dict]
) -> None:
    mp_logger = multiprocessing.get_logger()

    from wgwatch.models import RealEstateLocation

    for address in addresses:
        address_formatted = _format_address(address)
        try:
            geocode_result = gmaps_client.geocode(address_formatted)
            if geocode_result:
                latitude = geocode_result[0]["geometry"]["location"]["lat"]
                longitude = geocode_result[0]["geometry"]["location"]["lng"]

                mp_logger.info(
                    f"Geocoded: {address_formatted} -> ({latitude}, {longitude})"
                )

                mp_logger.info(
                    f"Saving location for address: {address_formatted}"
                )
                location_model = RealEstateLocation(
                    street_address=address["street_address"],
                    address_locality=address["address_locality"],
                    address_region=address["address_region"],
                    postal_code=address["postal_code"],
                    address_country=address["address_country"],
                    latitude=latitude,
                    longitude=longitude,
                )

                location_model.save()

            else:
                mp_logger.error(f"Failed to geocode: {address}")
        except Exception as e:
            mp_logger.error(f"Error for {address}: {e}")


def init_django():
    import os

    os.environ["DJANGO_SETTINGS_MODULE"] = "wgwatch.settings"
    django.setup()


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    multiprocessing.log_to_stderr(logging.INFO)

    gmaps_client = GoogleMapsClient(key=os.getenv("GOOGLE_MAPS_API_KEY"))
    n_processes = 8

    init_django()
    addresses = _load_addresses()
    logger.info(f"{len(addresses)} addresses loaded")

    address_chunks = [addresses[i::n_processes] for i in range(n_processes)]
    args = [(gmaps_client, chunk) for chunk in address_chunks]

    with multiprocessing.Pool(
        processes=n_processes, initializer=init_django
    ) as pool:
        pool.starmap(geocode_locations, args)


if __name__ == "__main__":
    main()
