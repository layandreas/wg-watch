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


class ScrapeDates(BaseModel):
    data: list[datetime.date]


class RealEstateListingWithLocation(BaseModel):
    street_address: str
    address_locality: str
    name: str
    url: HttpUrl
    latitude: float
    longitude: float
