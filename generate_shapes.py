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
    # only keep first four features
    features = features[:4]

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

        