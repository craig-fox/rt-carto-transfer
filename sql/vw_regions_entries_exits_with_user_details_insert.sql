INSERT INTO vw_regions_entries_exits_with_user_details (
    cartodb_id,
    the_geom,
    the_geom_webmercator,
    user_id,
    user_home,
    travel_month,
    travel_month_txt,
    activation_country,
    user_region,
    user_suburb,
    user_postcode,
    user_tourism_region,
    longitude,
    latitude,
    user_country,
    visited_region
)
SELECT
  (cartodb_id + {maxid}) AS cartodb_id,
  the_geom,
  the_geom_webmercator,
  user_id,
  user_home,
  travel_month,
  travel_month_txt,
  activation_country,
  user_region,
  user_suburb,
  user_postcode,
  user_tourism_region,
  longitude,
  latitude,
  user_country,
  visited_region
FROM {source}
WHERE 1=1
