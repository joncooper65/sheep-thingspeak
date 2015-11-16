#!/usr/bin/env

import os
#from pymongo import MongoClient

def pushdata():
  print 'Lets get some data out of mongodb'
  print MONGOUSER
  print MONGOPASSWORD

#  client = MongoClient()
#  db = client.test
#  db.collection_names(include_system_collections=False)


def main():
  global MONGOUSER
  global MONGOPASSWORD
  if os.path.isfile('mongoToThingspeak.cfg')==True:
    print "Found config file"
    f = open('mongoToThingspeak.cfg','r')
    data = f.read().splitlines()
    f.close()
    if data[0]=='mongo to thingspeak':
      MONGOUSER = data[1]
      MONGOPASSWORD = data[2]
      pushdata()
    else:
      print "Found config, but content is wrong"
  else:
    print "Could not find config"

if __name__=="__main__":
  main()
