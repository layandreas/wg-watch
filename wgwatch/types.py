import datetime
from typing import Literal

from pydantic import BaseModel, HttpUrl

City = Literal[
    "Düsseldorf",
    "Köln",
    "Berlin",
    "München",
    "Frankfurt am Main",
    "Hamburg",
    "Stuttgart",
    "Leipzig",
    "Dortmund",
    "Bremen",
]

OfferType = Literal[
    "Suite",
    "House",
    "Room",
    "Apartment",
]


class SelectedCities(BaseModel):
    payload: list[City]


class SelectedCity(BaseModel):
    payload: City


class SelectedOfferType(BaseModel):
    payload: OfferType


class ScrapeDates(BaseModel):
    data: list[datetime.date]


class SingleRealEstateListingWithLocation(BaseModel):
    street_address: str | None
    address_locality: str | None
    name: str | None
    url: HttpUrl | None
    price: float | None
    square_meters: float | None
    latitude: float | None
    longitude: float | None
    price_rank_normalized: float | None


class RealEstateListingsWithLocation(BaseModel):
    data: list[SingleRealEstateListingWithLocation]


class CityInfo(BaseModel):
    lat: float
    lon: float
    zoom: int


CITY_CENTER_LOCATIONS: dict[City, CityInfo] = {
    "Düsseldorf": CityInfo(lat=51.2277, lon=6.7735, zoom=12),
    "Köln": CityInfo(lat=50.9375, lon=6.9603, zoom=12),
    "Berlin": CityInfo(lat=52.5200, lon=13.4050, zoom=11),
    "München": CityInfo(lat=48.1351, lon=11.5820, zoom=12),
    "Frankfurt am Main": CityInfo(lat=50.1109, lon=8.6821, zoom=12),
    "Hamburg": CityInfo(lat=53.5511, lon=9.9937, zoom=11),
    "Stuttgart": CityInfo(lat=48.7758, lon=9.1829, zoom=12),
    "Leipzig": CityInfo(lat=51.3397, lon=12.3731, zoom=12),
    "Dortmund": CityInfo(lat=51.5136, lon=7.4653, zoom=12),
    "Bremen": CityInfo(lat=53.0793, lon=8.8017, zoom=12),
}
