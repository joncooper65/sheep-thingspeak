#!/usr/bin/env

import json
import os
import pymongo
import time
import urllib
import urllib2
import unicodedata
from dateutil.parser import *

def sendAnUpdate(measurement, parameters, thingspeakKey):
  
  #Here is an example illustrating the structure of the dictionary being constructed in the next bit of code
  # values = {
  #   'key': THINGSPEAKKEY, 
  #   'created_at': measurement["timestamp"],
  #   'field1': measurement["air_humidity_1"],
  #   'field2': measurement["air_temp_1"],
  #   'field3': measurement["soil_moisture_1"],
  # }
  values = {
    'key': thingspeakKey, 
    'created_at': measurement["timestamp"],
  }
  for index, parameter in enumerate(parameters, start = 1):
    values['field' + str(index)] = measurement[parameter]

  postdata = urllib.urlencode(values)
  req = urllib2.Request(THINGSPEAKURL + "/update", postdata)
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

def sendUpdatesSince(latestThingspeakMeasurement, sensor, parameters, thingspeakKey):
  print 'Getting measurements from mongodb that are post ' + str(latestThingspeakMeasurement)

  connectionUri = "mongodb://{0}:{1}@localhost/envdata".format(MONGOUSER, MONGOPASSWORD, MONGOUSERDB)
  client = pymongo.MongoClient(connectionUri)
  #note: the database and collection are both called envdata
  db = client.envdata
  measurements = db.envdata

  #Limit to just soil sensors
  query = {
    "sensor": sensor,
    "timestamp": {
      "$gt": latestThingspeakMeasurement
    }
  }

  #Here is an example of the projection dictionary that the next bit of code creates
  # projection = {
  #   "timestamp": 1, 
  #   "air_humidity_1": 1,
  #   "air_temp_1": 1,
  #   "soil_moisture_1": 1,
  # }
  projection = {"timestamp": 1}
  for parameter in parameters:
    projection[parameter] = 1
  
  previousTimestamp = ""
  #The batchsize added to the following query ensures we don't hit mongodb's 10 min timeout on the cursor
  for measurement in measurements.find(query,projection).sort([("timestamp", pymongo.ASCENDING)]).batch_size(20):
    #The data contains duplicate records, remove them using the timestamp as a test
    if (measurement["timestamp"] != previousTimestamp):
      sendAnUpdate(measurement, parameters, thingspeakKey)
      #Thingspeak is limited to one update per channel per 15s
      time.sleep(15)
    previousTimestamp = measurement["timestamp"]

def latestThingspeakUpdate(url, thingspeakKey):
  defaultStartDate = parse('2000-01-01T00:00:00Z')
  url = url + "?key=" + thingspeakKey
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
  global THINGSPEAKKEY_SOIL
  global THINGSPEAKCHANNEL_SOIL
  global THINGSPEAKKEY_GPS
  global THINGSPEAKCHANNEL_GPS
  global THINGSPEAKKEY_ACC
  global THINGSPEAKCHANNEL_ACC
  f = open('mongoToThingspeak.cfg','r')
  data = f.read().splitlines()
  f.close()
  MONGOUSER = data[0]
  MONGOPASSWORD = data[1]
  MONGOUSERDB = data[2]
  THINGSPEAKURL = data[3]
  THINGSPEAKKEY_SOIL = data[4]
  THINGSPEAKCHANNEL_SOIL = data[5]
  THINGSPEAKKEY_GPS = data[6]
  THINGSPEAKCHANNEL_GPS = data[7]
  THINGSPEAKKEY_ACC = data[8]
  THINGSPEAKCHANNEL_ACC = data[9]

def main():
  config()
  
  #Identifier in mongodb documents for sensor type - seems that it can be 'soil', 'gps' or 'acc'
  sensorType = "acc"
  
  parameters = None
  latestThingspeakMeasurement = None
  thingspeakkey = None
  thingspeakchannel = None

  if (sensorType == "soil"):
    parameters = ["air_humidity_1","air_temp_1","air_temp_2","soil_moisture_1","soil_temp_1","soil_temp_2","soil_temp_3","surface_flow"]
    thingspeakkey = THINGSPEAKKEY_SOIL
    thingspeakchannel = THINGSPEAKCHANNEL_SOIL
  elif (sensorType == "gps"):
    parameters = ["lat","lon","gps_qual","rssi","batt_v"]
    thingspeakkey = THINGSPEAKKEY_GPS
    thingspeakchannel = THINGSPEAKCHANNEL_GPS
  elif (sensorType == "acc"):
    parameters = ["x","y","z","rssi","batt_v","src_addr"]
    thingspeakkey = THINGSPEAKKEY_ACC
    thingspeakchannel = THINGSPEAKCHANNEL_ACC

  latestThingspeakMeasurement =  latestThingspeakUpdate(THINGSPEAKURL + "/channels/" + thingspeakchannel + "/feeds/last", thingspeakkey)
  sendUpdatesSince(latestThingspeakMeasurement, sensorType, parameters, thingspeakkey)

if __name__=="__main__":
  main()
