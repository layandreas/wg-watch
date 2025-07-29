import datetime
from datetime import date
from typing import List

from django.db import connection
from pydantic import BaseModel


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


def load_city_comparison_data(city1: str, city2: str) -> CityComparisonData:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            with
                city_1 as (
                    select
                        offer_type,
                        date(job_insert_time) as scraped_date,
                        avg(price) as avg_price,
                        avg(square_meters) as avg_square_meters,
                        avg(
                            price
                            / nullif(square_meters, 0)
                        ) as avg_price_per_square_meter,
                        count(*) as number_of_listings
                    from
                        latest_realestatelisting_per_day
                    where
                        address_locality = %s
                    group by
                        offer_type,
                        date(job_insert_time)
                    order by scraped_date desc, offer_type
                ),
                city_2 as (
                    select
                        offer_type,
                        date(job_insert_time) as scraped_date,
                        avg(price) as avg_price,
                        avg(square_meters) as avg_square_meters,
                        avg(
                            price
                            / nullif(square_meters, 0)
                        ) as avg_price_per_square_meter,
                        count(*) as number_of_listings
                    from
                        latest_realestatelisting_per_day
                    where
                        address_locality = %s
                    group by
                        offer_type,
                        date(job_insert_time)
                    order by scraped_date desc, offer_type
                )
            select
                coalesce(
                    c1.scraped_date,
                    c2.scraped_date
                ) as scraped_date,
                coalesce(c1.offer_type, c2.offer_type) as offer_type,
                c1.avg_price as avg_price_city_1,
                c2.avg_price as avg_price_city_2,
                c1.avg_square_meters as avg_square_meters_city_1,
                c2.avg_square_meters as avg_square_meters_city_2,
                c1.avg_price_per_square_meter as avg_price_per_square_meter_city_1,
                c2.avg_price_per_square_meter as avg_price_per_square_meter_city_2,
                c1.number_of_listings as number_of_listings_city_1,
                c2.number_of_listings as number_of_listings_city_2

            from city_1 as c1
                full join city_2 as c2 on c1.scraped_date = c2.scraped_date
                and c1.offer_type = c2.offer_type
            ;
        """,
            [city1, city2],
        )

        columns = [col[0] for col in cursor.description]
        rows = cursor.fetchall()

    # Combine columns and rows into a list of dictionaries (optional if easier in template)
    city_comparison_data = [dict(zip(columns, row)) for row in rows]
    city_comparison_data_validated = CityComparisonData.model_validate(
        {"data": city_comparison_data}
    )

    return city_comparison_data_validated


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
