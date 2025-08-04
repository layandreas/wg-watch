from django.db import models


class RealEstateListing(models.Model):
    # Scraping metadata
    listed_on_page = models.IntegerField(null=True, blank=True)
    # Listing details
    name = models.CharField(max_length=255, null=True, blank=True)
    url = models.URLField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    date_posted = models.DateField(null=True, blank=True)
    image = models.URLField(null=True, blank=True)

    # Offer details
    offer_type = models.CharField(max_length=50, null=True, blank=True)
    price = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    square_meters = models.IntegerField(null=True, blank=True)
    price_currency = models.CharField(max_length=10, null=True, blank=True)
    availability = models.URLField(null=True, blank=True)

    # Provider
    provider_name = models.CharField(max_length=255, null=True, blank=True)

    # Address (mainEntity -> Offer -> PostalAddress)
    street_address = models.CharField(max_length=255, null=True, blank=True)
    address_locality = models.CharField(max_length=100, null=True, blank=True)
    address_region = models.CharField(max_length=100, null=True, blank=True)
    postal_code = models.CharField(max_length=20, null=True, blank=True)
    address_country = models.CharField(max_length=100, null=True, blank=True)

    # Scraper job timestamp
    job_insert_time = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.name or f"Listing #{self.id}"


class RealEstateLocation(models.Model):
    street_address = models.CharField(max_length=255, null=True, blank=True)
    address_locality = models.CharField(max_length=100, null=True, blank=True)
    address_region = models.CharField(max_length=100, null=True, blank=True)
    postal_code = models.CharField(max_length=20, null=True, blank=True)
    address_country = models.CharField(max_length=100, null=True, blank=True)

    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
