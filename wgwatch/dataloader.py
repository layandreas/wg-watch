import datetime
from datetime import date
from typing import List

from django.db import connection
from jinja2 import Template
from pydantic import BaseModel

from .types import SelectedCities


class CityComparisonItem(BaseModel):
    scraped_date: date
    offer_type: str | None
    avg_price_city_1: float | None
    avg_price_city_2: float | None
    number_of_listings_city_1: int | None
    number_of_listings_city_2: int | None
    avg_square_meters_city_1: float | None
    avg_square_meters_city_2: float | None
    avg_price_per_square_meter_city_1: float | None
    avg_price_per_square_meter_city_2: float | None


# If you want a model for the whole list:
class CityComparisonData(BaseModel):
    data: List[CityComparisonItem]


class ScrapeDates(BaseModel):
    data: List[datetime.date]


def load_city_comparison_data(
    selected_cities: SelectedCities,
) -> CityComparisonData:
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
    return scrape_dates_validated
    return scrape_dates_validated
