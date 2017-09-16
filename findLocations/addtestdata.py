import googlemaps
import pymongo
from pymongo import MongoClient
from datetime import datetime
import math
from collections import OrderedDict

client = MongoClient("localhost:27017")

cafedb = client.cafedb

cafedb.cafes.delete_many({})

cafes = cafedb.cafes

cafes.insert_one({"Nw-lat":-33.8728314,"nw-lng":151.2046884,"name":"Test Place","address":"Test Address","se-lat":-33.8728314,"se-lng":151.2046884}).inserted_id
