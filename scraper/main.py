import asyncio
import json
import logging
import os
import re
from typing import List, Literal, Optional

import django
import zendriver as zd
from asgiref.sync import sync_to_async
from bs4 import BeautifulSoup
from django.utils import timezone
from pydantic import BaseModel, HttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class PostalAddress(BaseModel):
    streetAddress: Optional[str]
    addressLocality: Optional[str]
    addressRegion: Optional[str]
    postalCode: Optional[str]
    addressCountry: Optional[str]


class OfferDetails(BaseModel):
    type: Optional[str]
    price: Optional[float]
    priceCurrency: Optional[str]
    availability: Optional[HttpUrl]


class Provider(BaseModel):
    name: Optional[str]


class MainEntity(BaseModel):
    address: Optional[PostalAddress]


class RealEstateListingScraped(BaseModel):
    name: Optional[str]
    url: Optional[HttpUrl]
    description: Optional[str]
    datePosted: Optional[str]
    offers: OfferDetails
    provider: Optional[Provider]
    mainEntity: Optional[MainEntity]
    image: Optional[HttpUrl] = None


class RealEstateListingScrapedWithAdditions(BaseModel):
    listings_scraped: RealEstateListingScraped
    square_meters: int | None


class ListItem(BaseModel):
    position: int
    item: RealEstateListingScraped


class ItemList(BaseModel):
    itemListOrder: Optional[str]
    numberOfItems: Optional[int]
    itemListElement: List[ListItem]


class CollectionPage(BaseModel):
    name: Optional[str]
    url: Optional[HttpUrl]
    description: Optional[str]
    publisher: Optional[dict]
    mainEntity: ItemList


City = Literal[
    "Duesseldorf",
    "Koeln",
    "Berlin",
    "Muenchen",
    "Frankfurt-am-Main",
    "Hamburg",
    "Stuttgart",
    "Leipzig",
    "Dortmund",
    "Bremen",
]

city_to_id: dict[City, int] = {
    "Duesseldorf": 30,
    "Koeln": 73,
    "Berlin": 8,
    "Muenchen": 90,
    "Frankfurt-am-Main": 41,
    "Hamburg": 55,
    "Stuttgart": 124,
    "Leipzig": 77,
    "Dortmund": 26,
    "Bremen": 17,
}


class ScraperConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_nested_delimiter="_", env_nested_max_split=1, env_prefix="SCRAPER_"
    )

    cities: Optional[list[City]] = None
    headless: bool = False
    start_at_page: int = 0
    max_concurrent: int = 3
    max_pages_to_scrape: int = 30


def get_wg_gesucht_url(city: City, page: int) -> str:
    URL_TEMPLATE = (
        "https://www.wg-gesucht.de/wg-zimmer-und-1-zimmer-wohnungen-und-wohnungen-und-haeuser"
        "-in-{city}.{city_id}.0+1+2+3.1.{page}.html?offer_filter=1"
        "&city_id={city_id}&sort_order=0&noDeact=1&categories%5B%5D=0"
        "&categories%5B%5D=1&categories%5B%5D=2&categories%5B%5D=3&pagination=4&pu="
    )

    city_id = city_to_id[city]
    return URL_TEMPLATE.format(city=city, city_id=city_id, page=page)


def _extract_listing_id_from_url(url: str) -> int:
    pattern = r"\.(\d+)\.html"

    match = re.search(pattern, url)
    if match:
        try:
            listing_id_str = match.group(1)
            listing_id = int(listing_id_str)
            return listing_id
        except Exception:
            raise RuntimeError(
                f"No listing id could be extracted from url: {url}"
            )
    else:
        raise RuntimeError(f"No listing id could be extracted from url: {url}")


def _get_square_meters(soup: BeautifulSoup, listing_id: int) -> int | None:
    listing_data_id_result = soup.find_all(attrs={"data-id": str(listing_id)})

    soup_listing_data_id = BeautifulSoup(
        str(listing_data_id_result), "html.parser"
    )

    # Find all bold tags (<b>) that contain the square meter info
    bold_tags = soup_listing_data_id.find_all("b")

    # Use regex to extract patterns like '22 m²'
    area_pattern = re.compile(r"\b\d+\s?m²\b")

    for tag in bold_tags:
        text = tag.get_text(strip=True)
        match_area = area_pattern.search(text)
        if match_area:
            match_area_number = re.search(r"\d+", text)
            if match_area_number:
                area_number = int(match_area_number.group())
                return area_number

    return None


def _extract_and_add_square_meters(
    html_soup: BeautifulSoup,
    scraped_real_estate_listings: List[RealEstateListingScraped],
) -> list[RealEstateListingScrapedWithAdditions]:
    listings_scraped_with_additions = []
    for listing in scraped_real_estate_listings:
        square_meters: int | None = None
        if listing.url:
            listing_id = _extract_listing_id_from_url(url=str(listing.url))
            square_meters = _get_square_meters(
                soup=html_soup, listing_id=listing_id
            )
        scraped_with_addition = RealEstateListingScrapedWithAdditions(
            listings_scraped=listing, square_meters=square_meters
        )
        listings_scraped_with_additions.append(scraped_with_addition)

    return listings_scraped_with_additions


@sync_to_async
def bulk_insert_listings(
    scraped_real_estate_listings: List[RealEstateListingScrapedWithAdditions],
    current_page: int,
) -> None:
    from wgwatch.models import RealEstateListing

    django_listings = []

    for scraped_listing_with_additions in scraped_real_estate_listings:
        scraped_listing = scraped_listing_with_additions.listings_scraped
        offer = scraped_listing.offers
        provider = scraped_listing.provider
        main_entity = scraped_listing.mainEntity
        address = main_entity.address if main_entity else None

        listing = RealEstateListing(
            listed_on_page=current_page,
            name=scraped_listing.name,
            url=str(scraped_listing.url) if scraped_listing.url else None,
            description=scraped_listing.description,
            date_posted=scraped_listing.datePosted,
            image=str(scraped_listing.image) if scraped_listing.image else None,
            offer_type=offer.type,
            price=offer.price,
            square_meters=scraped_listing_with_additions.square_meters,
            price_currency=offer.priceCurrency,
            availability=(
                str(offer.availability) if offer.availability else None
            ),
            provider_name=provider.name if provider else None,
            street_address=address.streetAddress if address else None,
            address_locality=address.addressLocality if address else None,
            address_region=address.addressRegion if address else None,
            postal_code=address.postalCode if address else None,
            address_country=address.addressCountry if address else None,
            job_insert_time=timezone.now(),
        )
        django_listings.append(listing)

    RealEstateListing.objects.bulk_create(django_listings, batch_size=100)


def parse_listings_from_listings_str(
    jsonld_str: str,
) -> List[RealEstateListingScraped]:
    data = json.loads(jsonld_str)
    collection_page = next(
        (d for d in data if d.get("type") == "CollectionPage"), None
    )
    if not collection_page:
        return []
    collection = CollectionPage.model_validate(collection_page)
    return [li.item for li in collection.mainEntity.itemListElement]


def extract_listings(html_soup: BeautifulSoup) -> str:
    for script in html_soup.select("head > script"):
        script_content = script.text or ""
        if '@type": "Product",' in script_content:
            content = script_content.strip()[:-1]
            return content.replace("@type", "type")
    raise RuntimeError("No relevant <script> tag found in HTML.")


def get_last_page_number(html_soup: BeautifulSoup) -> int:
    pagination_div = html_soup.find(id="assets_list_pagination")
    if not pagination_div:
        raise ValueError("Pagination element not found.")
    links = pagination_div.find_all("a", class_="page-link")
    nums = []
    for link in links:
        try:
            nums.append(int(link.text.strip()))
        except ValueError:
            continue
    return max(nums) - 1 if nums else 0


async def scrape_city(
    browser: zd.Browser,
    city: City,
    scraped_pages: list[int],
    start_at_page: int = 0,
):
    current_page = start_at_page
    while True:
        url = get_wg_gesucht_url(city, current_page)
        logger.info(f"{city}: Scraping page {current_page} — {url}")
        page = await browser.get(url)
        await asyncio.sleep(5)
        html = await page.get_content()

        if "g-recaptcha" in html.lower():
            logger.warning(f"{city}: CAPTCHA detected — waiting")
            while "g-recaptcha" in html.lower():
                await asyncio.sleep(5)
                html = await page.get_content()
            await asyncio.sleep(4)
            html = await page.get_content()

        html_soup = BeautifulSoup(html, "html.parser")
        listings_str = extract_listings(html_soup)
        listings_parsed = parse_listings_from_listings_str(listings_str)
        listings_parsed_with_additions = _extract_and_add_square_meters(
            html_soup=html_soup, scraped_real_estate_listings=listings_parsed
        )
        last_page = get_last_page_number(html_soup)

        await bulk_insert_listings(
            scraped_real_estate_listings=listings_parsed_with_additions,
            current_page=current_page,
        )
        logger.info(
            f"{city}: Saved {len(listings_parsed)} listings from page {current_page}"
        )

        scraped_pages.append(current_page)
        current_page += 1
        if current_page > last_page:
            logger.info(f"{city}: Reached last page {last_page}")
            break

        if len(scraped_pages) >= ScraperConfig().max_pages_to_scrape:
            logger.info(f"{city}: Reached max page scrape limit")
            break

        await asyncio.sleep(1)

    await browser.stop()
    logger.info(f"✅ Finished scraping {city}")


async def main():
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "wgwatch.settings")
    django.setup()

    config = ScraperConfig()
    cities: List[City] = (
        config.cities if config.cities else list(city_to_id.keys())
    )

    sem = asyncio.Semaphore(config.max_concurrent)

    async def with_limit(city: City):
        scraped_pages: list[int] = []
        # Retry loop in case
        while True:
            try:
                async with sem:
                    max_scraped_page = max(scraped_pages, default=None)
                    start_at_page = max_scraped_page or config.start_at_page
                    logger.info(
                        f"Starting scraping for {city=} at page {start_at_page=}"
                    )

                    browser = await zd.start(
                        config=zd.Config(
                            sandbox=True,
                            headless=config.headless,
                            browser_connection_timeout=2,
                            browser_connection_max_tries=10,
                        )
                    )

                    await scrape_city(
                        city=city,
                        browser=browser,
                        scraped_pages=scraped_pages,
                        start_at_page=max_scraped_page or config.start_at_page,
                    )
                logger.info(f"Finished scraping: {city=}")
                break
            except Exception as e:
                wait_n_seconds = 10
                logger.error(f"Error for: {city=}: {e}")
                logger.info(
                    f"Retrying after {wait_n_seconds} seconds for: {city=}"
                )
                await browser.stop()
                await asyncio.sleep(wait_n_seconds)

    await asyncio.gather(*(with_limit(city) for city in cities))


if __name__ == "__main__":
    asyncio.run(main())
