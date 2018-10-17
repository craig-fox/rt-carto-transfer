INSERT INTO vw_event_by_grid_daily (
    cartodb_id,
    the_geom,
    the_geom_webmercator,
    local_date,
    travel_month,
    grid_id,
    tourism_region_name,
    all_user_count,
    verified_user_count,
    event_count,
    lon,
    lat,
    grid_area,
    source
)
SELECT
  (cartodb_id + {maxid}) AS cartodb_id,
  the_geom,
  the_geom_webmercator,
  local_date,
  travel_month,
  grid_id,
  tourism_region_name,
  all_user_count,
  verified_user_count,
  event_count,
  lon,
  lat,
  grid_area,
  source
FROM {source}
WHERE 1=1
