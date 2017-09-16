from setuptools import setup

with open("README",'r') as f:
    long_description = f.read()
    
setup(name = 'findLocations',
    version='1.0',
    description='Find Locations in a mongo database along a path using the googlemaps api',
    packages=["findLocations"],
    long_description = long_description,
    install_requires=['googlemaps','pymongo']
    )
