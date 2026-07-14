# OSM tag cheat sheet

You can't query (Overpass) or render meaningfully what you can't name. OSM
features are described by `key=value` tags. This is the working subset; the full
list is https://wiki.openstreetmap.org/wiki/Map_features and you can check how
common any tag actually is at https://taginfo.openstreetmap.org.

## The big keys

| Key        | What it covers                | Frequent values                                                                                                                                                                                                                                             |
| ---------- | ----------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `amenity`  | community/public facilities   | `cafe`, `restaurant`, `bar`, `pub`, `fast_food`, `bench`, `toilets`, `drinking_water`, `parking`, `bicycle_parking`, `bank`, `atm`, `pharmacy`, `hospital`, `school`, `library`, `place_of_worship`, `fuel`, `charging_station`, `fountain`, `waste_basket` |
| `shop`     | retail                        | `supermarket`, `convenience`, `bakery`, `coffee`, `clothes`, `hardware`, `books`, `bicycle`, `electronics`, `mall`                                                                                                                                          |
| `highway`  | roads & paths (ways) + points | `motorway`, `primary`, `secondary`, `residential`, `service`, `footway`, `path`, `cycleway`, `track`, `steps`, `crossing`, `bus_stop`, `traffic_signals`, `trailhead`                                                                                       |
| `leisure`  | recreation                    | `park`, `garden`, `playground`, `pitch`, `sports_centre`, `swimming_pool`, `nature_reserve`, `dog_park`, `fitness_centre`                                                                                                                                   |
| `natural`  | natural features              | `water`, `wood`, `tree`, `peak`, `beach`, `wetland`, `cliff`, `spring`, `scrub`                                                                                                                                                                             |
| `landuse`  | how land is used (areas)      | `residential`, `commercial`, `industrial`, `forest`, `farmland`, `grass`, `cemetery`, `retail`                                                                                                                                                              |
| `tourism`  | tourist-relevant              | `hotel`, `motel`, `guest_house`, `attraction`, `viewpoint`, `museum`, `artwork`, `camp_site`, `picnic_site`, `information`                                                                                                                                  |
| `building` | structures (areas)            | `yes`, `house`, `residential`, `apartments`, `commercial`, `industrial`, `church`, `school`                                                                                                                                                                 |
| `waterway` | water lines                   | `river`, `stream`, `canal`, `ditch`, `riverbank`                                                                                                                                                                                                            |
| `boundary` | administrative/other areas    | `administrative` (with `admin_level`), `national_park`, `protected_area`                                                                                                                                                                                    |
| `office`   | offices                       | `company`, `government`, `lawyer`, `estate_agent`, `it`                                                                                                                                                                                                     |
| `man_made` | built structures              | `bridge`, `tower`, `pier`, `water_tower`, `surveillance`                                                                                                                                                                                                    |

## admin_level (for `area`/`boundary` queries)

US-relevant levels on `boundary=administrative`:

| level | US meaning          | example       |
| ----- | ------------------- | ------------- |
| 2     | country             | United States |
| 4     | state               | Idaho         |
| 6     | county              | Ada County    |
| 8     | city / town         | Boise         |
| 10    | neighborhood/suburb | North End     |

Useful in Overpass: `area[name="Boise"][admin_level=8]` pins the city boundary
(not a random thing also named "Boise").

## Common attribute tags (on many features)

`name`, `name:en`, `addr:housenumber`, `addr:street`, `addr:city`,
`addr:postcode`, `website`, `contact:website`, `phone`, `opening_hours`,
`wheelchair`, `cuisine`, `operator`, `brand`, `wifi`/`internet_access`,
`outdoor_seating`, `takeaway`, `ele` (elevation, on peaks).

## opening_hours quick read

`opening_hours` is a mini-language, e.g.
`Mo-Fr 07:00-18:00; Sa 08:00-14:00; Su off`. Don't hand-parse it — if you need
to evaluate "is it open now", use the `opening_hours.js` library on the web side.

## Finding tags for a thing you have in mind

1. Search the wiki Map Features page for the category.
2. Check **taginfo** for the real-world value distribution (e.g. is it
   `amenity=fast_food` or `shop=fast_food`? taginfo settles it).
3. Prototype the query in **overpass-turbo.eu** and eyeball the results.

When in doubt, query `nwr[key](area)` with `out tags;` and inspect what values
actually come back before committing to a value filter.
