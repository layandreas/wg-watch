
select

        date(job_insert_time) AS scraped_date,
        offer_type,

        {% for city in selected_cities %}
        AVG(CASE WHEN address_locality = '{{ city }}' THEN price END) AS avg_price_city_{{ loop.index }}{% if not loop.last %},{% endif %}
        {% endfor %},

        {% for city in selected_cities %}
        AVG(CASE WHEN address_locality = '{{ city }}' THEN square_meters END) AS avg_square_meters_city_{{ loop.index }}{% if not loop.last %},{% endif %}
        {% endfor %},

        {% for city in selected_cities %}
        AVG(CASE WHEN address_locality = '{{ city }}' THEN price / NULLIF(square_meters, 0) END) AS avg_price_per_square_meter_city_{{ loop.index }}{% if not loop.last %},{% endif %}
        {% endfor %},

        {% for city in selected_cities %}
        COUNT(CASE WHEN address_locality = '{{ city }}' THEN 1 END) AS number_of_listings_city_{{ loop.index }}{% if not loop.last %},{% endif %}
        {% endfor %}


FROM latest_realestatelisting_per_day

GROUP BY
    date(job_insert_time),
    offer_type

ORDER BY
    scraped_date DESC,
    offer_type;