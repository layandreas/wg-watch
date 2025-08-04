import datetime
from datetime import date
from typing import Any, List

from django.db import connection
from jinja2 import Template
from pydantic import BaseModel

from .types import (
    City,
    OfferType,
    RealEstateListingWithLocation,
    ScrapeDates,
    SelectedCities,
)


def load_city_comparison_data(
    selected_cities: SelectedCities,
) -> list[dict[str, Any]]:
    with open("input/sql/city_comparison.sql") as f:
        raw_template = f.read()

    template = Template(raw_template)
    rendered_query = template.render(selected_cities=selected_cities.payload)

    with connection.cursor() as cursor:
        cursor.execute(rendered_query)
        columns = [col[0] for col in cursor.description]
        rows = cursor.fetchall()

    # Combine columns and rows into a list of dictionaries (optional if easier in template)
    city_comparison_data = [dict(zip(columns, row)) for row in rows]

    return city_comparison_data


def load_scrape_dates() -> ScrapeDates:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            select distinct

                date(job_insert_time) as scraped_date

            from latest_realestatelisting_per_day
            order by
                scraped_date desc
            ;
        """
        )

        rows = cursor.fetchall()

    # Combine columns and rows into a list of dictionaries (optional if easier in template)
    scrape_dates = [row[0] for row in rows]
    scrape_dates_validated = ScrapeDates.model_validate({"data": scrape_dates})

    return scrape_dates_validated


def load_listings_with_locations(
    city: City, scrape_date: datetime.date, offer_type: OfferType
) -> RealEstateListingWithLocation:
    scrape_date_str = scrape_date.strftime("%Y-%m-%d")

    with connection.cursor() as cursor:
        cursor.execute(
            """
                select

                    listing.street_address,
                    listing.address_locality,
                    listing.name,
                    listing.url,
                    location.latitude,
                    location.longitude

                from latest_realestatelisting_per_day
                    as listing

                left join wgwatch_realestatelocation
                    as location

                on listing.street_address = location.street_address
                and listing.address_locality = location.address_locality
                and listing.address_region = location.address_region
                and listing.postal_code = location.postal_code
                and listing.address_country = location.address_country

                where listing.address_locality = %s
                and date(listing.job_insert_time) = %s
                and listing.offer_type = %s
                and location.latitude is not null
                and location.longitude is not null
                ;
        """,
            [scrape_date_str, offer_type, city],
        )

        rows = cursor.fetchall()
        columns = [col[0] for col in cursor.description]

    listings_with_locations = [dict(zip(columns, row)) for row in rows]
    listings_with_locations_validated = (
        RealEstateListingWithLocation.model_validate(
            {"data": listings_with_locations}
        )
    )

    return listings_with_locations_validated
