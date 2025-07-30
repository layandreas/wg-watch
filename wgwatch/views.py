from django.shortcuts import render
from django.views.decorators.http import require_http_methods

from .dataloader import load_city_comparison_data, load_scrape_dates
from .models import RealEstateListing


@require_http_methods(["GET"])
def home(request):
    cities = RealEstateListing.objects.values_list(
        "address_locality", flat=True
    ).distinct()

    scrape_dates = load_scrape_dates()

    # Get selected cities from query params
    city1 = request.GET.get("city1")
    city2 = request.GET.get("city2")

    selected_cities = None
    city_comparison_data = None

    if city1 and city2:
        selected_cities = [city1, city2]
        city_comparison_data = load_city_comparison_data(city1, city2)

    city_comparison_data_json = (
        [item.model_dump() for item in city_comparison_data.data]
        if city_comparison_data
        else None
    )

    return render(
        request,
        "index.html",
        {
            "cities": cities,
            "selected_cities": selected_cities,
            "city_comparison_data": city_comparison_data_json,
            "scrape_dates": scrape_dates.data,
        },
    )


@require_http_methods(["GET"])
def about(request):
    return render(
        request,
        "about.html",
    )
