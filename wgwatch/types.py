from typing import Literal

from pydantic import BaseModel

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


class SelectedCities(BaseModel):
    payload: list[City]
