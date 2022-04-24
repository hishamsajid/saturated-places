from hmac import trans_36
import json
from numpy import flip
from shapely.geometry import Polygon
# import numpy as np
from functions import func_flip, func_get_grid_from_poly
from functions import func_generate_fishnet
from functions import func_flip
from functools import partial

with open('lahore_sample.geojson','r') as file:
    poly = json.load(file)

poly = poly['features'][0]['geometry']['coordinates'][0]
# print(type(poly))
poly = Polygon(poly)
# print(poly)
mesh = func_get_grid_from_poly(poly=poly,resolution=500)
#print(oly)
flipped_poly = partial(func_flip,poly)
print(flipped_poly)
vor_gpd = func_generate_fishnet(mesh,poly)
 
print(vor_gpd)
# mesh.to_csv('temp.csv')

"""
TO-DO

1. voronoi created, next is to to delauny triangulation for area
2. add comments for all functions, coordinate sequence should be x,y not y,x
"""