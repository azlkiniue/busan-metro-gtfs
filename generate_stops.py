import csv
import json

# csv header for stops.txt
# stop_id,stop_code,stop_name,stop_lat,stop_lon,location_type,wheelchair_boarding
header = [
    "stop_id",
    "stop_code",
    "stop_name",
    "stop_lat",
    "stop_lon",
    "location_type",
    "wheelchair_boarding",
]
# generate stops.txt in the csv format from route.geojson
with open("route.geojson", "r", encoding="utf-8") as f:
    data = json.load(f)
    features = data["features"]
    # delete first four features
    features = features[4:]

    # open stops.txt for writing
    with open("stops.txt", "w", newline="", encoding="utf-8") as f_out:
        writer = csv.writer(f_out)
        # write the header
        writer.writerow(header)
        # write the data
        for feature in features:
            properties = feature["properties"]
            geometry = feature["geometry"]
            # extract the required fields
            stop_id = feature["id"]
            stop_code = feature["id"]
            stop_name = properties["name"]
            stop_lat = geometry["coordinates"][1]
            stop_lon = geometry["coordinates"][0]
            location_type = 0
            wheelchair_boarding = 1
            # write the row
            writer.writerow(
                [
                    stop_id,
                    stop_code,
                    stop_name,
                    stop_lat,
                    stop_lon,
                    location_type,
                    wheelchair_boarding,
                ]
            )
    print(f"Generated stops.txt with {len(features)} stops.")
