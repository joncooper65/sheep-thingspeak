#!/usr/bin/env

import json
import os
import pymongo
import time
import urllib
import urllib2
import unicodedata
#from pymongo import MongoClient
from dateutil.parser import *

def senddata(measurement):
  values = {
    'key': THINGSPEAKKEY, 
    'created_at': measurement["timestamp"],
    'field1': measurement["air_humidity_1"],
    'field2': measurement["air_temp_1"],
    'field3': measurement["air_temp_2"],
    'field4': measurement["soil_moisture_1"],
    'field5': measurement["soil_temp_1"],
    'field6': measurement["soil_temp_2"],
    'field7': measurement["soil_temp_3"],
    'field8': measurement["surface_flow"]
  }
  postdata = urllib.urlencode(values)
  req = urllib2.Request(THINGSPEAKURL + "/update",postdata)
  log = time.strftime("%d-%m-%Y,%H:%M:%S") + ","
  try:
    response = urllib2.urlopen(req, None, 5)
    html_string = response.read()
    response.close()
    log = log + 'Update ' + html_string
  except urllib2.HTTPError, e:
    log = log + 'Server could not fulfill the request. Error code: ' + str(e.code)
  except urllib2.URLError, e:
    log = log + 'Failed to reach server. Reason: ' + e.reason
  except:
    log = log + 'Unknown error'
  print log  

def getandsend(latestThingspeakMeasurement):
  print 'getting data out of mongodb'

  connectionUri = "mongodb://{0}:{1}@localhost/envdata".format(MONGOUSER, MONGOPASSWORD, MONGOUSERDB)
  client = pymongo.MongoClient(connectionUri)
  #note: the database and collection are both called envdata
  db = client.envdata
  measurements = db.envdata

  #Limit to just soil sensors
  query = {
    "sensor": "soil",
    "timestamp": {
      "$gte": latestThingspeakMeasurement
    }
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

  previousTimestamp = ""
  #The batchsize added to the following query ensures we don't hit mongodb's 10 min timeout on the cursor
  for measurement in measurements.find(query,projection).sort([("timestamp", pymongo.ASCENDING)]).batch_size(20):
    #The data contains duplicate records, remove them using the timestamp as a test
    if (measurement["timestamp"] != previousTimestamp):
      senddata(measurement)
      #Thingspeak is limited to one update per channel per 15s
      time.sleep(15)
    previousTimestamp = measurement["timestamp"]

def latestThingspeakUpdate(url):
  defaultStartDate = parse('2000-01-01T00:00:00Z')
  url = url + "?key=" + THINGSPEAKKEY
  try:
    data = urllib2.urlopen(url).read()
    if ("\"-1\"" == data):
      return defaultStartDate
    else:
      datadict = json.loads(data)
      latestUpdate = datadict["created_at"]
      return parse(latestUpdate)
  except urllib2.HTTPError, e:
    print e
  except urllib2.URLError, e:
    print "Network error: {}".format(e.reason.args[1])

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
  latestThingspeakMeasurement =  latestThingspeakUpdate(THINGSPEAKURL + "/channels/66379/feeds/last")
  getandsend(latestThingspeakMeasurement)

if __name__=="__main__":
  main()
