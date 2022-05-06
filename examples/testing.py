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

places_df.to_csv('places_data.csv',index=False)

# from hmac import trans_36
# import json
# from matplotlib.pyplot import grid
# from numpy import flip
# from shapely.geometry import Polygon
# # import numpy as np
# # from functions import func_flip, func_get_grid_from_poly
# # from functions import func_generate_fishnet
# # from functions import func_flip
# # from functions import func_saturate
# from functools import partial


# with open('lahore_sample.geojson','r') as file:
#     poly = json.load(file)

# with open('api_key.json','r') as file:
#     api_key = json.load(file)
    
# poly = poly['features'][0]['geometry']['coordinates'][0]
# api_key = api_key['api_key']
# print(api_key)
# # resolution = 500
# # # print(type(poly))
# # poly = Polygon(poly)
# # # print(poly)
# # mesh = func_get_grid_from_poly(poly=poly,resolution=resolution)
# # # print(oly)
# # flipped_poly = partial(func_flip,poly)
# # print(flipped_poly)
# # vor_gpd = func_generate_fishnet(mesh,poly)
 
# # print(vor_gpd)
# # # mesh.to_csv('temp.csv')

# # func_saturate(grid_df=vor_gpd,boundary_poly=poly,
# #                         fp_working_file='working.pkl',
# #                         fp_outpt='final.shp',
# #                         api_request_limit=2000,
# #                         api_key=api_key,
# #                         resolution = resolution)

# """
# TO-DO

# 1. Write demo code
# 2. Write README.MD
# 3. Distrubtion on PyPi
# 3. Add comments for all functions, coordinate sequence should be x,y not y,x

# """

# # check if places API function is working or not

# # places_df = func_get_places_poi(lat=31.53019,lon=74.30109,resolution=500,api_key=api_key)
# # places_df.to_csv('temp.csv')
# # print(places_df)