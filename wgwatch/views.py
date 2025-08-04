from typing import get_args

import pandas as pd
from django.shortcuts import render
from django.views.decorators.http import require_http_methods

from .dataloader import (
    load_city_comparison_data,
    load_listings_with_locations,
    load_scrape_dates,
)
from .models import RealEstateListing
from .types import (
    CITY_CENTER_LOCATIONS,
    OfferType,
    SelectedCities,
    SelectedCity,
    SelectedOfferType,
)


@require_http_methods(["GET"])
def home(request):
    cities = (
        RealEstateListing.objects.values_list("address_locality", flat=True)
        .distinct()
        .order_by("address_locality")
    )

    scrape_dates = load_scrape_dates()

    # Get selected cities from query params
    selected_cities_validated = SelectedCities(
        payload=request.GET.getlist("citiesSelection")
    )
    city_comparison_data = None

    if selected_cities_validated.payload:
        city_comparison_data = load_city_comparison_data(
            selected_cities_validated
        )

    return render(
        request,
        "index.html",
        {
            "cities": cities,
            "selected_cities": (
                selected_cities_validated.payload
                if selected_cities_validated
                else None
            ),
            "city_comparison_data": city_comparison_data,
            "scrape_dates": scrape_dates.data,
        },
    )


@require_http_methods(["GET"])
def map(request):
    cities = (
        RealEstateListing.objects.values_list("address_locality", flat=True)
        .distinct()
        .order_by("address_locality")
    )

    offer_types = list(get_args(OfferType))
    selected_city = request.GET.get("citySelection")
    selected_offer_type = request.GET.get("offerSelection")
    selected_city_validated = None
    selected_offer_type_validated = None
    listings_with_locations = None
    city_center_location = None

    if selected_city and selected_offer_type:
        selected_city_validated = SelectedCity(
            payload=request.GET.get("citySelection")
        )

        selected_offer_type_validated = SelectedOfferType(
            payload=request.GET.get("offerSelection")
        )

        listings_with_locations = load_listings_with_locations(
            city=selected_city_validated.payload,
            offer_type=selected_offer_type_validated.payload,
        )

        city_center_location = CITY_CENTER_LOCATIONS[
            selected_city_validated.payload
        ]

        listings_with_locations_df = pd.DataFrame(
            listings_with_locations.model_dump()["data"]
        )

        listing_price_quantiles = (
            listings_with_locations_df["price"]
            .quantile([0.2, 0.4, 0.6, 0.8])
            .to_dict()
        )

    return render(
        request,
        "map.html",
        {
            "cities": cities,
            "offer_types": offer_types,
            "selected_city": (
                selected_city_validated.payload
                if selected_city_validated
                else None
            ),
            "selected_offer_type": (
                selected_offer_type_validated.payload
                if selected_offer_type_validated
                else None
            ),
            "listings_with_locations": (
                listings_with_locations.model_dump(mode="json")
                if listings_with_locations
                else None
            ),
            "city_center_location": (
                city_center_location.model_dump(mode="json")
                if city_center_location
                else None
            ),
            "listing_price_quantiles": listing_price_quantiles,
        },
    )


@require_http_methods(["GET"])
def about(request):
    return render(
        request,
        "about.html",
    )
