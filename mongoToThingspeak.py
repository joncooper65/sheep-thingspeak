#!/usr/bin/env

import os
import time
import urllib
import urllib2
import unicodedata
from pymongo import MongoClient

def senddata(measurement):
  values = {
    'key': THINGSPEAKKEY, 
    'created_at': measurement["timestamp"],
    'field1': measurement["air_humidity_1"],
    'field2': measurement["air_temp_1"],
    'field3': measurement["air_temp_2"],
    'field4': measurement["soil_moisture_1"],
    'field5': measurement["soil_moisture_2"],
    'field6': measurement["soil_temp_1"],
    'field7': measurement["soil_temp_2"],
    'field8': measurement["surface_flow"]
  }
  postdata = urllib.urlencode(values)
  req = urllib2.Request(THINGSPEAKURL,postdata)
  log = time.strftime("%d-%m-%Y,%H:%M:%S") + ","
  try:
    response = urllib2.urlopen(req, None, 5)
    html_string = response.read()
    response.close()
    log = log + 'Update ' + html_string
  except urllib2.HTTPError, e:
    log = log + 'Server could not fulfill the request. Error code: ' + e.code
  except urllib2.URLError, e:
    log = log + 'Failed to reach server. Reason: ' + e.reason
  except:
    log = log + 'Unknown error'
  print log  

def getandsend():
  print 'getting data out of mongodb'

  connectionUri = "mongodb://{0}:{1}@localhost/envdata".format(MONGOUSER, MONGOPASSWORD, MONGOUSERDB)
  print connectionUri
  client = MongoClient(connectionUri)
  #note: the database and collection are both called envdata
  db = client.envdata
  measurements = db.envdata

  #Limit to just soil sensors
  query = {
    "sensor": "soil"
 #   "timestamp": {
 #     "$gte": "2010-04-29T00:00:00.000Z", 
 #     "$lte": "2015-07-13T11:53:01.452Z"
 #   }
  }

  projection = {
    "timestamp": 1, 
    "air_humidity_1": 1,
    "air_humidity_2": 1,
    "air_humidity_3": 1,
    "air_temp_1": 1,
    "air_temp_2": 1,
    "air_temp_3": 1,
    "soil_moisture_1": 1,
    "soil_moisture_2": 1,
    "soil_moisture_3": 1,
    "soil_temp_1": 1,
    "soil_temp_2": 1,
    "soil_temp_3": 1,
    "surface_flow": 1,
    "trial": 1,
    "_id":1
  }

  for measurement in measurements.find(query,projection):
    #Thingspeak is limited to one update per channel per 15s
    senddata(measurement)
    time.sleep(15)

def config():
  global MONGOUSER
  global MONGOPASSWORD
  global MONGOUSERDB
  global THINGSPEAKURL
  global THINGSPEAKKEY
  f = open('mongoToThingspeak.cfg','r')
  data = f.read().splitlines()
  f.close()
  MONGOUSER = data[0]
  MONGOPASSWORD = data[1]
  MONGOUSERDB = data[2]
  THINGSPEAKURL = data[3]
  THINGSPEAKKEY = data[4]

def main():
  config()
  getandsend()

if __name__=="__main__":
  main()
