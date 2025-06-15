import csv
import json

service_lookup = {
    "1": "WD",
    "2": "SAT",
    "3": "SUN",
}

# csv header for trips.txt
# route_id,service_id,trip_id,trip_headsign,direction_id,shape_id
header = [
    "route_id",
    "service_id",
    "trip_id",
    "trip_headsign",
    "direction_id",
    "shape_id",
    "wheelchair_accessible",
]

with open("route.geojson", "r", encoding="utf-8") as f:
    data = json.load(f)
    features = data["features"]
    # delete first four features
    features = features[4:]

    # lookup the name of station by id in features
    station_lookup = {
        feature["id"]: feature["properties"]["name"] for feature in features
    }

    # open timetable.csv for reading
    with open("timetable.csv", "r", encoding="utf-8") as f_in:
        reader = csv.DictReader(f_in)
        schedules = list(reader)
        # select distinct by scode, line, day, updown, endcode and count the number of each unique schedule
        unique_schedules = {}
        for row in schedules:
            unique_values = (
                row["line"],
                row["day"],
                row["updown"],
                row["endcode"],
                row["trainno"],
            )
            if row["scode"] == row["endcode"]:
                continue
            if unique_values not in unique_schedules:
                unique_schedules[unique_values] = 1
            else:
                unique_schedules[unique_values] += 1

        # open trips.txt for writing
        with open("trips.txt", "w", newline="", encoding="utf-8") as f_out:
            writer = csv.writer(f_out)
            # write the header
            writer.writerow(header)
            # iterate through unique schedules
            for (line, day, updown, endcode, trainno), count in unique_schedules.items():
                route_id = line
                service_id = service_lookup[str(day)]
                trip_id = f"{endcode}_{line}_{updown}_{service_id}_{trainno}"
                trip_headsign = station_lookup[int(endcode)]
                direction_id = updown
                shape_id = f"{line}_{updown}_shp"
                wheelchair_accessible = 1
                # write the row
                writer.writerow(
                    [
                        route_id,
                        service_id,
                        trip_id,
                        trip_headsign,
                        direction_id,
                        shape_id,
                        wheelchair_accessible,
                    ]
                )
    print(f"Generated trips.txt with {len(unique_schedules)} trips.")