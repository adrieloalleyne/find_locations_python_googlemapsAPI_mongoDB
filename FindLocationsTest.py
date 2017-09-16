from findLocations import findLocations

key = "*************************************************"
start = "Sydney Town Hall"
end = "Parramatta, NSW"

fc = findLocations()
fc.google_auth(key=key)
cafedata = fc.getLocations(start,end,"localhost:27017",dbname="libraries",dbcollection="libraries")


