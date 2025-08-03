from django.shortcuts import render
from django.views.decorators.http import require_http_methods

from .dataloader import load_city_comparison_data, load_scrape_dates
from .models import RealEstateListing
from .types import SelectedCities


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
    return render(
        request,
        "map.html",
        {},
    )


@require_http_methods(["GET"])
def about(request):
    return render(
        request,
        "about.html",
    )
