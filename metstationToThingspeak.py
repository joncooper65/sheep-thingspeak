#!/usr/bin/env python

import json
import os
import urllib
import urllib2
import time
from itertools import imap

THINGSPEAK_API='https://api.thingspeak.com'
THINGSPEAKKEY='NOT_DEFINED_HERE'

def met_to_thingspeak(data):
  return {
    'created_at': data["TIMESTAMP"],
    'field1':     data["WS"],
    'field2':     data["WD"],
    'field3':     data["STP_TSoil2_Avg"],
    'field4':     data["STP_TSoil5_Avg"],
    'field5':     data["STP_TSoil10_Avg"],
    'field6':     data["STP_TSoil20_Avg"],
    'field7':     data["STP_TSoil50_Avg"],
    'field8':     data["Rain_Tot"]
  }

def submit(data, key, api=THINGSPEAK_API):
  for obs in data:
    req = urllib2.Request(api + "/update", urllib.urlencode(obs))
    req.add_header('THINGSPEAKAPIKEY', key)
    try:
      urllib2.urlopen(req).read()
      print 'Submitted ' + obs['created_at']
      time.sleep(15) #Thingspeak is limited to one update per channel per 15s
    except urllib2.HTTPError, e:
      print 'Server could not fulfill the request. Error code: ' + str(e.code)
    except urllib2.URLError, e:
      print 'Failed to reach server. Reason: ' + e.reason
    except:
      print 'Unknown error'

def last_update(channel, key, empty=None, api=THINGSPEAK_API):
  url = api + "/channels/" + channel + "/feeds/last?key=" + key
  data = json.load(urllib2.urlopen(url))
  if ("-1" == data):
    return empty
  else:
    return data['created_at']

def get_met_data(since, url='http://fme.ceh.ac.uk/fmedatastreaming/IoT/conwyMetData.fmw?'):
  params = urllib.urlencode({'since': since})
  res = urllib2.urlopen(url + params).read()
  return json.loads(res) if res else []

latest_update = last_update("66820", THINGSPEAKKEY, empty='2000-01-01T00:00:00Z')
print 'Last updated ' + latest_update
met_data = get_met_data(latest_update)
print 'Found ' + str(len(met_data)) + ' records'

submit(imap(met_to_thingspeak, met_data), THINGSPEAKKEY)
