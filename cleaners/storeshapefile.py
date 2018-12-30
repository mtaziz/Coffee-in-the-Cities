
import pandas as pd

# reading in the scraped store data
star = pd.read_csv('~/Documents/cariboucity/scrapers/data/twincitysbux.csv')
bou = pd.read_csv('~/Documents/cariboucity/scrapers/data/twincitycaribou.csv')

# I want to join the data from both stores into one frame that has store name (Caribou or Starbucks),
# store id, and coordinates.
# This is the data I will eventually use for ML, but also for Tableau and visualization.
# Becauze ZCTA and USPS zip code do not 100% match, and website has potential for misentered data,
# I will use GIS to create a new zip code column based on polygon where lat and long point lies

# note I want to work in projection NA83 / UTM zone 15N
# aka EPSG: 26915

# first, I'm making sure each row states whether it is Caribou or Starbucks by creating a 'brand' column
bou['brand'] = 'Caribou'
star['brand'] = 'Starbucks'
# combining all stores into one table, and deleting the two separate tables
both = bou.append(star)
del(bou, star)
# keeping the brand, latitude, longitude, id, and city information
both = both[['brand', 'latitude', 'longitude', 'id', 'city']]
both.index = (range(len(both)))

# now to begin the GIS work of finding each store's zip code / ZCTA
# must make the data from the 'both' frame into a dictionary for use w Shapely and Fiona,
# which work better with something resembling GeoJSON
storepoints = both.to_dict(orient = 'records')
# adding point geometry to each store in storepoints requires the Shapely library
from shapely.geometry import Point
# pyporj library handles projections
import pyproj
# oldProj is the projection of the Google web service - how our scraped data was projected
oldProj = pyproj.Proj(init='epsg:3857')
# newProj is the GIS projection of the Census shapefiles
newProj = pyproj.Proj(init='epsg:26915')

for row in storepoints:
    # adding point info to each store in storepoints
    # first making sure projection is correct
    x0, y0 = oldProj(float(row['longitude']), float(row['latitude']))
    x1, y1 = pyproj.transform(oldProj, newProj, x0, y0)
    row['point'] = Point(x1, y1)
# now to read in the shapefile of ZCTAs created with 'countyfips.py'
# we want to add zip code info for each store based in what zip code polygon it's coords fall into
# https://automating-gis-processes.github.io/2016/Lesson3-point-in-polygon.html#how-to-check-if-point-is-inside-a-polygon

# first reading zip code shapefile with fiona
import fiona
zipframe = fiona.open("~/Documents/cariboucity/sourcegis/edited/tczips/census2010zips.shp",'r')
zipshape = range(len(zipframe))
# converting each polygon/multipolygon from zipshape to a shapely polygon
from shapely.geometry import shape
for i in(range(len(zipframe))):
    zipshape[i] = shape(zipframe[i]['geometry'])

'''

# going through each point and seeing where it falls within a polygon
# id 34 and 42 and 55 are a single polygon each
     # point 78 should fall in polygon 55

     
There are 410 stores and only 185 shapefiles/zip codes
will iterate though stores, stop if/when a zip is found
'''
for i in range(len(storepoints)):
    storepoints[i]['zip code'] = 'NaN'
    for j in range(len(zipshape)):
        if zipshape[j].contains(storepoints[i]['point']) == True:
            storepoints[i]['zip code'] = str(zipframe[j]['properties']['ZCTA5'])


# writing the points to a shapefile

from fiona import collection
from fiona.crs import from_epsg
from shapely.geometry import mapping, shape

schema1 = { 'geometry': 'Point', 'properties': { 'id': 'int' , 'brand': 'str', 'zip code': 'str','latitude': 'float', 'longitude': 'float', 'city': 'str'} }

with collection(
    "~/Documents/cariboucity/sourcegis/edited/tczips/myfiona", "w", "ESRI Shapefile", schema = schema1, crs = from_epsg(26915)) as output:
        for row in storepoints:
            # adding point info to each store in storepoints
            output.write({
                'geometry': mapping(row['point']),
                'properties': {
                    'id': row['id'],
                    'brand': row['brand'],
                    'zip code': row['zip code'],
                    'latitude': row['latitude'],
                    'longitude': row['longitude'],
                    'city': row['city']
                }
            })
    
# exporting store data to csv archive - will later join this data with ACS data
storepoints = pd.DataFrame.from_dict(storepoints)
storepoints = storepoints.drop(labels = 'point', axis=1)
storepoints.to_csv('~/Documents/cariboucity/scrapers/data/cleanstores.csv')
