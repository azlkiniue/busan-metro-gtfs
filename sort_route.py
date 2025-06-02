# create a script to sort the route data from route.geojson
import json


with open('route.geojson', 'r', encoding='utf-8') as f:
    data = json.load(f)
    # {
    #   ...
    #   "features": [
    #     {
    #       "id": 1,
    #       ...
    #     }
    #   ]
    # }
    features = data['features']
    # sort the features by 'id' in ascending order
    features.sort(key=lambda x: x['id'])
    # write the sorted data back to the file
    with open('route.geojson', 'w', encoding='utf-8') as f_out:
        json.dump(data, f_out, ensure_ascii=False, indent=4)
