import csv
import json

# csv header for shapes.txt
# shape_id,shape_pt_lat,shape_pt_lon,shape_pt_sequence
header = [
    "shape_id",
    "shape_pt_lat",
    "shape_pt_lon",
    "shape_pt_sequence"
]

with open("route.geojson", "r", encoding="utf-8") as f:
    data = json.load(f)
    features = data["features"]
    # only keep the line features
    features = [feature for feature in features if feature["geometry"]["type"] == "LineString"]

    with open("shapes.txt", "w", newline="", encoding="utf-8") as f_out:
        writer = csv.writer(f_out)
        # write the header
        writer.writerow(header)
        
        # iterate through features and write to shapes.txt
        for feature in features:
            shape_id = str(feature["id"]) + "_1_shp"

            coordinates = feature["geometry"]["coordinates"]
            for i, (lon, lat) in enumerate(coordinates):
                # write the row
                writer.writerow([shape_id, lat, lon, i])
            
            # also write the reverse order for the shape
            shape_id_reversed = str(feature["id"]) + "_0_shp"
            for i, (lon, lat) in enumerate(reversed(coordinates)):
                # write the row
                writer.writerow([shape_id_reversed, lat, lon, i])

        