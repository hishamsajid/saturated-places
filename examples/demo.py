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
mesh = sp.func_get_grid_from_poly(poly=poly,resolution=resolution)

# Generates a fishnet grid using the mesh of point generated using mesh get_grid_from_poly function
vor_gpd = sp.func_generate_fishnet(mesh,poly)


# Runs saturation algorithm to return a dataframe with places data for area within a polygon.
places_df = sp.func_saturate(grid_df=vor_gpd,boundary_poly=poly,
                        fp_working_file='working.shp',
                        fp_outpt='final.pkl',
                        api_request_limit=2000,
                        api_key=api_key,
                        resolution = resolution)

# Saves places data as flat csv file.
places_df.to_csv('places_data.csv',index=False)
