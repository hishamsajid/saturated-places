# saturated-places

<!-- badges: start -->
[![PyPI version](https://badge.fury.io/py/saturatedplaces.svg)](https://badge.fury.io/py/saturatedplaces)
<!-- badges: end -->

A python package for effeciently downloading Point of Interest (POI) data from Google Places API for large geographies. Currently, this is done by creating a fishnet grid within a custom polygon and
running Delauny Triangulation for each grid cell till the API result is saturated i.e the API returns < 60 results. 

We are open to contributors who wish to further optimize this logic. 

## Installation

You can either go the latest release, download the tarball to your local directory and run: <br/>

`pip install saturated-places-X.Y.Z.tar.gz`

Or you can go simply download it from [PyPi](https://pypi.org/project/saturatedplaces/) by running: <br/>

`pip install saturatedplaces`

## Usage

```

import saturatedplaces as sp
from shapely.geometry import Polygon
import json

# Put Google API key here with Places API service enabled.
api_key = "#######"


# Custom GeoJson created using geojson.io
with open('lahore_sample.geojson','r') as file:
    poly = json.load(file)


# Convert GeoJson coordinates feature into shapely.geometry.Polygon object.
# This is important since later functions only accepts this data type.
poly = poly['features'][0]['geometry']['coordinates'][0]
poly = Polygon(poly)


# resolution determines the space between each Point of the mesh. The same variable 
# is also used in the 'radius' parameter for the Places API call, as used the saturate
# function. You could set this variable independently for both get_grid_from_poly and
# and saturate function.
resolution = 500

# Creates a mesh of equally spaced points within a polygon 'poly', resolution controls
# distance between each point of the mesh.
mesh = sp.get_grid_from_poly(poly=poly,resolution=resolution)

# Generates a fishnet grid using the mesh of point generated using mesh get_grid_from_poly function
vor_gpd = sp.generate_fishnet(mesh,poly)


# Runs saturation algorithm to return a dataframe with places data for area within a polygon.
places_df = sp.saturate(grid_df=vor_gpd,boundary_poly=poly,
                        fp_working_file='working.shp',
                        fp_outpt='final.pkl',
                        api_request_limit=2000,
                        api_key=api_key,
                        resolution = resolution)

# Saves places data as flat csv file.
places_df.to_csv('places_data.csv',index=False)


```


## Contribution

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.
I will also be creating issues to chalk out what features, or improvements need to be worked on next. Feel free to pick
up any one of these issues after aligning. 

For any queries feel free to reach out to hishamsajid113@gmail.com or drop a DM [@hishamsajid](https://twitter.com/hishamsajid)

