import googlemaps
import pymongo
from pymongo import MongoClient
from datetime import datetime
import math
from collections import OrderedDict

# Find locations along a path using the googlemaps api
class findLocations:

    def __init__(self):
        self.R = 6378.1 #Radius of the Earth

    # authorize use of the google maps API
    def google_auth(self,key = None,client=None,secret=None):
        if key:
            self.gmaps = googlemaps.Client(key=key)
        elif client and secret:
            self.gmaps = googlemaps.Client(client=client,secret=secret)

    # calculate distance between 2 points on the globe
    def distance(self,lat1, lng1, lat2, lng2):
        #return distance as meters
        radius = 6371 * 1000 


        dLat = (lat2-lat1) * math.pi / 180
        dLng = (lng2-lng1) * math.pi / 180

        lat1 = lat1 * math.pi / 180
        lat2 = lat2 * math.pi / 180

        val = math.sin(dLat/2) * math.sin(dLat/2) + math.sin(dLng/2) * math.sin(dLng/2) * math.cos(lat1) * math.cos(lat2)    
        ang = 2 * math.atan2(math.sqrt(val), math.sqrt(1-val))
        return radius * ang

    # getRoute takes a start and destination location  as arguments
    # wayproints contains a list of waypoints for the route to pass through
    def getRoute(self,start,destination,waypoints=[]):

        self.start = start
        self.destination = destination
        
        # Request directions for the driving mode 
        now = datetime.now()
        directions_results = self.gmaps.directions(start,destination,mode="driving",waypoints=waypoints,departure_time=now)

        legs = directions_results[0]['legs']

        route = []
        i = 0

        for j in legs:
            leg = []
            while i < len(j['steps']):
               leg.append(j['steps'][i]) #
               i = i +1
            route.append(leg)
        return route

    # break a leg of the journey into multiple points
    def getPoints(self,lng1,lat1,lng2,lat2,numberofsegments):
        
        interpoints = []

        # with a short segment only one point is needed
        if num_of_segments  > 1:
            onelessthansegments = numberofsegments - 1
            fractionalincrement = (1.0/onelessthansegments)

            lng1_radians = math.radians(lng1)
            lat1_radians = math.radians(lat1)
            lng2_radians = math.radians(lng2)
            lat2_radians = math.radians(lat2)

            distance_radians=2*math.asin(math.sqrt(math.pow((math.sin((lat1_radians-lat2_radians)/2)),2) + math.cos(lat1_radians)*math.cos(lat2_radians)*math.pow((math.sin((lng1_radians-lng2_radians)/2)),2)))

            # 6371.009 represents the mean radius of the earth
            # shortest path distance
            distance_km = 6371.009 * distance_radians * 1000


            interpoints.append( {u'lat' : lat1,u'lng' : lng1})

            f = fractionalincrement
            icounter = 1
            while (icounter <  onelessthansegments):
                    icountmin1 = icounter - 1
                    # f is a fraction along the route from start to end point
                    A=math.sin((1-f)*distance_radians)/math.sin(distance_radians)
                    B=math.sin(f*distance_radians)/math.sin(distance_radians)
                    x = A*math.cos(lat1_radians)*math.cos(lng1_radians) + B*math.cos(lat2_radians)*math.cos(lng2_radians)
                    y = A*math.cos(lat1_radians)*math.sin(lng1_radians) +  B*math.cos(lat2_radians)*math.sin(lng2_radians)
                    z = A*math.sin(lat1_radians) + B*math.sin(lat2_radians)
                    newlat=math.atan2(z,math.sqrt(math.pow(x,2)+math.pow(y,2)))
                    newlon=math.atan2(y,x)
                    newlat_degrees = math.degrees(newlat)
                    newlon_degrees = math.degrees(newlon)
                    interpoints.append( {u'lat' : newlat_degrees,u'lng' : newlon_degrees})
                    icounter += 1
                    f = f + fractionalincrement
            # write the ending coordinates
            interpoints.append( {u'lat' : lat2,u'lng' : lng2})
        return interpoints
        

    
    # return locations along the path based on the database
    # save location data for the route   
    def getLocations(self,start=None,destination=None,mongo_url=None,route_name=None,dbname=None,dbcollection=None):
        client = MongoClient(mongo_url)

        if dbname == None or dbcollection == None:
            return dict()
        
        locationdb = client[dbname]

        matches = []
        seen = set()

        self.route = self.getRoute(start,destination)

        locations = locationdb[dbcollection].find()

        location_results = {}

        i = 0
        
        for leg in self.route:

            for step in leg:

                distance = int(step['distance']['value'])

                numpoints = distance/100

                i = i + 1
                
                # find matches for bounding box in the table
                # find by coordinates
                
                # db structure
                #name, address, nw-lat, nw-long, se-lat, se-long

                #find locations inside of ellipses and prevent overlaps

                if numpoints == 0:
                    interpoints.append(step['start_location'])
                else:
                    lat1 = step['start_location'][u'lat']
                    lng1 = step['start_location'][u'lng']
                    lat2 = step['end_location'][u'lat']
                    lng2 = step['end_location'][u'lng']
                    interpoints = self.getPoints(lng1,lat1,lng2,lat2,numpoints)
                    
                for interpoint in interpoints:

                    for location in locations:
                       distance = self.distance(interpoint[u'lat'],interpoint[u'lng'],location["nw-lat"],location["nw-lng"])
                       if distance < 100 and location != []:
                          if str(location) not in seen:
                              matches.append(location)
                              seen.add(str(location))
                              location_results[distance] = {"name":location["name"],"address":location["address"],"se-lat":location["se-lat"],"nw-lng":location[u'nw-lng'],"nw-lat":location["nw-lat"],"se-lng":location["se-lng"]}

        # get results by distance from intermediate points
        location_results = OrderedDict(sorted(location_results.items(), key=lambda t: t[0])).values()   

        # store completed routes in the mongo DB
        location_routes = locationdb.location_routes
        location_routes.insert_one({"start_address":start,"destination_address":destination,"start":self.route[0],"destination":self.route[-1],"route":self.route,"locations":location_results,"route_name":route_name}).inserted_id
        
        # return all the matches
        return {"start_address":start,"destination_address":destination,"start":self.route[0],"destination":self.route[-1],"route":self.route,"locations":location_results,"route_name":route_name}
 



    





        



    





        
