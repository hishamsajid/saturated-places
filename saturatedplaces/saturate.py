import pandas as pd
import numpy as np
import pyproj
import requests as re
import geopandas as gpd
import json
import warnings
import requests
import time
import sys


from shapely.prepared import prep
from shapely.geometry import Point,Polygon
from shapely.ops import transform
from scipy.spatial import Delaunay,Voronoi
from functools import partial

import warnings
warnings.filterwarnings('ignore')

def func_voronoi_finite_polygons_2d(vor, radius=None):
    """
    Reconstruct infinite voronoi regions in a 2D diagram to finite
    regions.
    Parameters
    ----------
    vor : Voronoi
        Input diagram
    radius : float, optional
        Distance to 'points at infinity'.
    Returns
    -------
    regions : list of tuples
        Indices of vertices in each revised Voronoi regions.
    vertices : list of tuples
        Coordinates for revised Voronoi vertices. Same as coordinates
        of input vertices, with 'points at infinity' appended to the
        end.
    """

    if vor.points.shape[1] != 2:
        raise ValueError("Requires 2D input")

    new_regions = []
    new_vertices = vor.vertices.tolist()

    center = vor.points.mean(axis=0)
    if radius is None:
        radius = vor.points.ptp().max()*2

    # Construct a map containing all ridges for a given point
    all_ridges = {}
    for (p1, p2), (v1, v2) in zip(vor.ridge_points, vor.ridge_vertices):
        all_ridges.setdefault(p1, []).append((p2, v1, v2))
        all_ridges.setdefault(p2, []).append((p1, v1, v2))

    # Reconstruct infinite regions
    for p1, region in enumerate(vor.point_region):
        vertices = vor.regions[region]

        if all(v >= 0 for v in vertices):
            # finite region
            new_regions.append(vertices)
            continue

        # reconstruct a non-finite region
        ridges = all_ridges[p1]
        new_region = [v for v in vertices if v >= 0]

        for p2, v1, v2 in ridges:
            if v2 < 0:
                v1, v2 = v2, v1
            if v1 >= 0:
                # finite ridge: already in the region
                continue

            # Compute the missing endpoint of an infinite ridge

            t = vor.points[p2] - vor.points[p1] # tangent
            t /= np.linalg.norm(t)
            n = np.array([-t[1], t[0]])  # normal

            midpoint = vor.points[[p1, p2]].mean(axis=0)
            direction = np.sign(np.dot(midpoint - center, n)) * n
            far_point = vor.vertices[v2] + direction * radius

            new_region.append(len(new_vertices))
            new_vertices.append(far_point.tolist())

        # sort region counterclockwise
        vs = np.asarray([new_vertices[v] for v in new_region])
        c = vs.mean(axis=0)
        angles = np.arctan2(vs[:,1] - c[1], vs[:,0] - c[0])
        new_region = np.array(new_region)[np.argsort(angles)]

        # finish
        new_regions.append(new_region.tolist())

    return new_regions, np.asarray(new_vertices)

def func_transform_api_result(row):
    geometry = row.geometry['location']
    lat,lon = geometry['lat'],geometry['lng']
    types = row.types
    first_type = types[0]
    second_type = types[1]
    return lat,lon,first_type,second_type

def func_get_places_poi(lat,lon,resolution,api_key):
    
    url = """https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={lat},{lon}
    &radius={resolution}
    &type=point_of_interest
    &key={api_key}""".format(api_key=api_key,lat=lat,lon=lon,resolution=resolution)

    payload={}
    headers = {}
    params = {}

    response = requests.request("GET", url, headers=headers, data=payload)
    places_df = []

    results = json.loads(response.content)

    places_df.append(results['results'])

    while 'next_page_token' in results:
        time.sleep(1)
        params['pagetoken'] = results['next_page_token']
        response = requests.get(url,params=params)
        results = json.loads(response.content)
        places_df.append(results['results'])
        
    final_df = pd.concat([pd.DataFrame(df) for df in places_df])
    final_df = final_df.reset_index(drop=True)
    
    return final_df


def func_flip(x, y):
    """Flips the x and y coordinate values"""
    return y, x

# def func_intersect_vor(row):
#     return bbox.intersection(row.vor)

def func_point_from_latlon(row):
    return Point(row.lat,row.lon)


def func_latlon_from_lat_lon(row):
    return (row.lat,row.lon)

def func_lonlat_from_lat_lon(row):
    return (row.lon,row.lat)    



def get_grid_from_poly(poly,resolution,base_proj='epsg:4326'):
    """
    Takes a polygon and creates a mesh of equally spaced points within it.

    ---
    poly: bounding box polygon within which we want to create mesh of Points
    
    resolution: Distance in meters between each point of the equally spaced mesh of Points.
    This determines the size of each grid cell in the fishnet grid. generate_fishnet function
    esentially creates voronoi tesselations with each point of the mesh treated as a centroid.

    base_proj: Base Projection from which coordinates are projected to Web Mercator, EPSG: 3857

    """

    project = partial(
        pyproj.transform,
        pyproj.Proj(init=base_proj),
        pyproj.Proj(init='epsg:3857')
    )

    poly = transform(project,poly)

    # shp = districts_gpd[districts_gpd.DISTRICT==district_name]
    # shp = shp.to_crs(epsg=3857)
    # poly = shp.geometry.values[0]

    latmin, lonmin, latmax, lonmax = poly.bounds

    # construct a rectangular mesh

    prep_polygon = prep(poly)
    valid_points = []
    points = []

    #0.012 degrees is approximately equal to 1km
    # resolution = 1000

    for lat in np.arange(latmin, latmax, resolution):
        for lon in np.arange(lonmin, lonmax, resolution):
            points.append(Point((round(lat,4), round(lon,4))))

    # validate if each point falls inside shape using
    # the prepared polygon
    valid_points.extend(filter(prep_polygon.contains, points))


    mesh =  gpd.GeoDataFrame(valid_points)
    mesh = mesh.reset_index()
    mesh = mesh.rename(columns={
        'index':'p_id',
        0:'geometry'
        })

    mesh['p_id'] = mesh.p_id.apply(lambda x: 'p{id}'.format(id=str(x)))
    #print(mesh)
    mesh['geometry'] = mesh['geometry'].apply(lambda x: transform(func_flip,x))
    mesh['geometry'] = mesh['geometry'].apply(lambda x: transform(func_flip,x))
    
    mesh.crs = 'EPSG:3857'
    mesh = mesh.to_crs(crs=4326)
    mesh['coords']=mesh['geometry'].apply(lambda x: list(x.coords)[0])
    mesh['lon'],mesh['lat']=mesh.coords.apply(lambda x: x[0]),mesh.coords.apply(lambda x: x[1])
    mesh = mesh.drop(columns=['coords'])
    mesh['lon_lat'] =  mesh.apply(func_lonlat_from_lat_lon,1)
    mesh = gpd.GeoDataFrame(mesh,geometry='geometry',crs='EPSG:4326')
    
    return mesh

def generate_fishnet(mesh,bbox):
    # mesh['lat_lon'] =  mesh.apply(func_latlon_from_lat_lon,1)
    vor = Voronoi(list(mesh['lon_lat'].values))
    regions,vertices=func_voronoi_finite_polygons_2d(vor,radius=0.07)

    polys = []
    for region in regions:
        poly = vertices[region]
        polys.append(Polygon(poly))

    vor_gpd = gpd.GeoDataFrame(polys)
    vor_gpd = vor_gpd.rename(columns={
        0:'vor'
    })

    def func_intersect_vor(row):
        return bbox.intersection(row.vor)

    vor_gpd['bounded_vor'] = vor_gpd.apply(func_intersect_vor,1)
    vor_gpd = gpd.GeoDataFrame(vor_gpd,geometry='bounded_vor')
    vor_gpd = vor_gpd.drop(columns='vor')
    vor_gpd = vor_gpd.reset_index()
    vor_gpd = vor_gpd.rename(columns={'index':'vor_id'})
    vor_gpd['vor_id'] = vor_gpd.vor_id.apply(lambda x: 'vor'+str(x))

    return vor_gpd


# Function needs to be reworked to be made more dynamic instead of having 4 fixed levels (times triangulation is done)
def func_saturate(grid_df,boundary_poly,fp_working_file,fp_outpt,api_request_limit,api_key,resolution):
    """
    Takes a fishnet grid created using function generate_fishet and run Delauny Triangulation on each
    grid cell until the Places API result is saturated.

    ---
    grid_df: GeoDataFrame containing fishnet grid created using func_generate_fishent

    boundary_poly: Polygon which acts as the boundary for data pulled via the Places API

    fp_working_file: File path for working file, must be in .shp format, contains fishnet grid with 'fetched'
    attribute where fetched=1 means the data for fetched grid cell has already been fetched. If function is 
    interrupted during execution you may use this working file as grid_df input to ensure requests are not
    duplicated.

    fp_output: File path for final output file, must be in .pkl format

    api_request_limit: Maximum number of Places API requests that can be sent, use to control costs.

    api_key: Google API key.

    resolution: Sets the radius in meters in which the Google API searches, this shuld be roughly equal
    to the size of one grid-cell Polygon
    
    """
    rdf_list = []
    centroids = []
    requests_counter = 0
    limit = api_request_limit
    if('fetched' not in grid_df.columns):
        grid_df['fetched'] = 0

    grid_df['centroid'] = grid_df.bounded_vor.centroid
    for ind, row in grid_df.iterrows():
        if(row.fetched!=1):
            left = len(grid_df)-ind
            out_str = 'requests: {req} & vor_left: {left}'.format(req=requests_counter,left=left)
            sys.stdout.write(out_str)
            sys.stdout.flush()
            resolution = 200
            level = 1

            #LEVEL=1
            coords = row.centroid.xy
            # print(coords)
            lon,lat = coords[0][0],coords[1][0]
            centroids.append(np.array([lat,lon]))
            #print(np.array([lat,lon]))
            requests_counter+=3
            if(requests_counter<=limit):
                rdf = func_get_places_poi(lat=lat,lon=lon,resolution=resolution,api_key=api_key)
            else:
                print('LIMIT REACHED!')
                sys.exit()
                break
            rdf_list.append(rdf)

            #LEVEL=2
            if(len(rdf)==60):
                #print('reached L2')
                poly = row.geometry
                poly_points_list = []
                if(poly.geom_type=='MultiPolygon'):
                    poly_points = np.array(poly[0].exterior.coords)
                    poly_points_list.append(poly_points)
    #                 poly_points = [np.array(pol.exterior.coords) for pol in poly]
    #                 poly_points = np.concatenate(poly_points,axis=0)
    #                 poly_points_list.append(poly_points)
                elif(poly.geom_type=='Polygon'):   
                    poly_points = np.array(poly.exterior.coords)
                    poly_points_list.append(poly_points)
                tri = Delaunay(poly_points_list[0])
                polys = poly_points[tri.simplices]
                polys = [Polygon(poly) for poly in polys]
                if(len(polys)>1):
                    level += 1
                    for poly in polys:
                        centroid = poly.centroid
                        #checks if new centroid in Lahore
                        if(boundary_poly.contains(centroid) == True):
                            centroid = np.array(poly.centroid.coords)
                            #print(centroid[0])
                            centroids.append(centroid[0])
                            lon,lat = centroid[0][0],centroid[0][1]
                            requests_counter+=3
                            if(requests_counter<=limit):
                                rdf = func_get_places_poi(lat=lat,lon=lon,resolution=resolution/level,api_key=api_key)
                            else:
                                print('LIMIT REACHED!')
                                sys.exit()
                                break
                            rdf_list.append(rdf)
                        else:
                            pass

                        #LEVEL=3 
                        if(len(rdf)==60):
                            #print('reached L3')
                            poly_points = np.array(poly.exterior.coords)
                            poly_points = np.concatenate((poly_points,centroid),axis=0)
                            tri = Delaunay(poly_points)
                            l2_polys = poly_points[tri.simplices]
                            l2_polys = [Polygon(poly) for poly in l2_polys]
                            if(len(l2_polys)>1):
                                for poly in l2_polys:
                                    level += 1
                                    centroid = poly.centroid
                                    if(boundary_poly.contains(centroid)==True):
                                        centroid = np.array(centroid.coords)
                                        #print(centroid[0])
                                        centroids.append(centroid[0])
                                        lon,lat= centroid[0][0],centroid[0][1]
                                        requests_counter+=3
                                        if(requests_counter<=limit):
                                            rdf = func_get_places_poi(lat=lat,lon=lon,resolution=resolution/level,api_key=api_key)
                                        else:
                                            print('LIMIT REACHEAD!')
                                            sys.exit()
                                            break
                                        rdf_list.append(rdf)
                                    else:
                                        pass

                                    #LEVEL=4
                                    if(len(rdf)==60):
                                        #print('reached L4')
                                        poly_points = np.array(poly.exterior.coords)
                                        poly_points = np.concatenate((poly_points,centroid),axis=0)
                                        tri = Delaunay(poly_points)
                                        l3_polys = poly_points[tri.simplices]
                                        l3_polys = [Polygon(poly) for poly in l2_polys]
                                        for poly in l3_polys:
                                            level += 1
                                            centroid = poly.centroid
                                            if(boundary_poly.contains(centroid)==True):
                                                centroid = np.array(centroid.coords)
                                                #print(centroid[0])
                                                centroids.append(centroid[0])
                                                lon,lat= centroid[0][0],centroid[0][1]
                                                requests_counter+=3
                                                if(requests_counter<=limit):
                                                    rdf = func_get_places_poi(lat=lat,lon=lon,resolution=resolution/level,api_key=api_key)
                                                else:
                                                    print('LIMIT REACHED!')
                                                    sys.exit()
                                                    break

                                                rdf_list.append(rdf)
                                            else:
                                                pass
            temp_dfs = pd.concat(rdf_list)
            fname = fp_outpt
            temp_dfs.to_pickle(fname)
            
            grid_df.loc[ind,'fetched']=1
            temp = grid_df
            temp = temp.drop(columns=['centroid'])
            temp.to_file(fp_working_file)
            
        elif(row.fetched==1):
            pass

    return temp_dfs