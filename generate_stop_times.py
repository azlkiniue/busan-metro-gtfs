import csv
import json

service_lookup = {
    "1": "WD",
    "2": "SAT",
    "3": "SUN",
}

# csv header for stop_times.txt
# trip_id,arrival_time,departure_time,stop_id,stop_sequence,stop_headsign
header = [
    "trip_id",
    "arrival_time",
    "departure_time",
    "stop_id",
    "stop_sequence",
    "stop_headsign"
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
        previous_row = None
        for row in schedules:
            unique_values = (
                row["line"],
                row["day"],
                row["updown"],
                row["endcode"],
                row["trainno"],
            )
            if unique_values not in unique_schedules:
                unique_schedules[unique_values] = []
            
            if row["updown"] == "1":
                unique_schedules[unique_values].append(row)
            if row["updown"] == "0":
                # reverse the order of the rows for updown = 0
                unique_schedules[unique_values].insert(0, row)

        # open stop_times.txt for writing
        with open("stop_times.txt", "w", newline="", encoding="utf-8") as f_out:
            writer = csv.writer(f_out)
            # write the header
            writer.writerow(header)
            # iterate through unique schedules
            for (line, day, updown, endcode, trainno), rows in unique_schedules.items():
                service_id = service_lookup[str(day)]
                trip_id = f"{endcode}_{line}_{updown}_{service_id}_{trainno}"
                stop_headsign = station_lookup[int(endcode)]
                previous_time = ''
                for sequence, row in enumerate(rows):
                    current_time = f"{row['hour']}{row['time']}"
                    if previous_time != '' and previous_time == current_time:
                        # skip this row if the time is the same as the previous row
                        continue
                    previous_time = current_time

                    arrival_time = f"{row['hour']}:{row['time']}:15"
                    departure_time = f"{row['hour']}:{row['time']}:45"
                    stop_id = row["scode"]
                    # write the row
                    writer.writerow(
                        [
                            trip_id,
                            arrival_time,
                            departure_time,
                            stop_id,
                            sequence,
                            stop_headsign
                        ]
                    )