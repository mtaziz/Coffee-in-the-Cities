# The purpose of this file is to take a shapefile of ZCTAs for Minnesota
# and extract the zip codes that lie (either wholly or partially) in a county
# considered part of the Twin Cities metropolitan area by the Census

import pandas as pd
import geopandas as gpd

# name of directory where most data will be read and written
datadir = '/Users/jennifer/Documents/cariboucity/sourcegis/'

# reading in a copy of the Census csv I saved to disk
# the raw data in text format can be found at
# https://www2.census.gov/geo/docs/maps-data/data/rel/zcta_county_rel_10.txt
# alternately, I could have written as
# fun = pd.read_csv('https://www2.census.gov/geo/docs/maps-data/data/rel/zcta_county_rel_10.txt')
# this file just matches ZCTAs / zip codes to counties - it has no geometry
# information and I am using it to find zip codes that either fall completely
# or partially within a Meotropolitan Council county

fun = pd.read_csv(str(datadir+ 'zctatocounty.csv'), dtype={'ZCTA5': 'unicode'})
# taking only the Minnesota (state number 27) counties from this lengthy file
minnesota = fun[fun['STATE'] == 27]
# then filter just for the counties we want
mncounties = pd.DataFrame({'Name': ['Anoka', 'Carver', 'Dakota', 'Hennepin',
                                    'Ramsey', 'Scott', 'Washington',],
                           'COUNTY': [3, 19, 37, 53, 123, 139, 163]})
mnfips = minnesota.merge(mncounties, on='COUNTY', how='inner')

# put them together - now we have all the ZCTAs in the Twin Cities MSA
both = mnfips
del(fun, minnesota, mncounties, mnfips)

metrofips = both.drop_duplicates()
fipsofinterest = metrofips[['ZCTA5']].drop_duplicates()
fipsofinterest.index = range(0, len(fipsofinterest))
fipsofinterest.to_csv(str(datadir+ 'myziplist.csv'))
metrofips['ZCTA5'] = metrofips['ZCTA5'].astype('unicode')

# taking the zips of interest from a locally saved copy of shapefile:
# ZIP Code Tabulation Areas 2010 Census
# this is using the file directly provided by the Census - it is in GCS NAD83 projection
# fro the .prj file directly, it is:
# GEOGCS["GCS_North_American_1983",DATUM["D_North_American_1983",
# SPHEROID["GRS_1980",6378137,298.257222101]],PRIMEM["Greenwich",0],
# UNIT["Degree",0.017453292519943295]]
# aka EPSG 4269
zipshape = gpd.read_file('/Users/jennifer/Documents/GIS/GIS data/TIGER/tl_2018_us_zcta510/tl_2018_us_zcta510.shp')

zipshape = zipshape.rename(columns = {'ZCTA5CE10': 'ZCTA5'})
somezips = zipshape.merge(metrofips, on = 'ZCTA5', how = 'right')
# projection of outgoing shapefile
# want to change from EPSG 4269 to EPSG 26915
# running somezips.crs in the console will show EPSG 4269 is the current projection

# Geopandas frames have a function .to_crs, which I will use to reproject the
# shapefile before I write it to disk
somezips = somezips.to_crs({'init': 'epsg:26915'})
somezips.to_file(datadir+ 'edited/tczips/twincitiesmetrozips.shp')
