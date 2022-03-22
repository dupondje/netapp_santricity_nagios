#!/usr/bin/python
# Copyright 2015 NetApp Inc.  All rights reserved.
__author__ = 'hardikJsheth'
import sys
import logging

import requests

import SANtricityStorage
from logging.handlers import RotatingFileHandler


serverUrl="https://10.0.1.30:8443"
urlToServer=serverUrl+"/devmgr/v2"
loginUrl=serverUrl +"/devmgr/utils"

stat =0
username="rw"
password="rw"
newarrayid=0
newarrayname=""
newarraystatus=""
logging.basicConfig(format='%(asctime)s - %(name)s : %(message)s',filename='/tmp/nagios-python.log',level=logging.DEBUG)
handler = RotatingFileHandler('/tmp/nagios-python.log', maxBytes=SANtricityStorage.maxbytes, backupCount=20)

logger =logging.getLogger("HOSTCON")
logger.addHandler(handler)
logger.setLevel(logging.INFO)


def checkStorageSystem(sessionId,ip1,ip2):
        try:
                logging.info("In getStorageSystem")
                url=urlToServer+'/storage-systems'

                r=requests.get(url,verify=False, headers={'Content-Type': 'application/json','Cookie':'JSESSIONID='+sessionId})


                lstOfArraySys= SANtricityStorage.get_data_from_REST(urlToServer,sessionId,None,"storage-systems")
                logging.info(len(lstOfArraySys))
                lst=[]

                for listEle in lstOfArraySys:

                        if listEle["ip1"] == ip1 and listEle["ip2"] == ip2:
                                dataMap={}
                                dataMap["arrayId"]=listEle["id"]
                                dataMap["arrayName"]=listEle["name"]
                                dataMap["status"] = listEle["status"]
                                return dataMap

                return False

        except Exception as err:
                logger.error("Error in checkStorageSystem",exc_info=True)
                print("STATUS UNKNOWN")
                sys.exit(3)


def getNewStorageSystem(sessionId,id):
        try:
                logging.info("In getStorageSystem")
                url=urlToServer+'/storage-systems/'+id

                r=requests.get(url,verify=False, headers={'Content-Type': 'application/json','Cookie':'JSESSIONID='+sessionId})


                listEle=r.json()



                dataMap={}
                dataMap["arrayId"]=listEle["id"]
                dataMap["arrayName"]=listEle["name"]
                dataMap["status"] = listEle["status"]
                return dataMap

                return False

        except Exception as err:
                logging.error(Exception)
                logging.error(err)
                print("STATUS UNKNOWN")
                sys.exit(3)

def configureArray(sessionid,ip1,ip2):
     try:
                logging.info("In configureArray")
                url=urlToServer+'/storage-systems'
                data = "{ \"controllerAddresses\": [\""+ip1+"\",\""+ip2+"\"]}"
                r=requests.post(url,data,verify=False, headers={'Content-Type': 'application/json','Cookie':'JSESSIONID='+sessionid})

                if r.status_code == 201 :
                    lstOfArraySys=r.json()

                   # datamap=getNewStorageSystem(sessionid,arrayid)
                    strresult= "Array configured successfully with id : "+lstOfArraySys["id"]
                    SANtricityStorage.getStorageSystemDetails(urlToServer,sessionid,0)
                    return strresult
                else:
                    global stat
                    stat =2
                    return "Array does not exist and it can't be configured with given ip"



     except Exception as err:
                logger.error("Error in configure array",exc_info=True)
                print("STATUS UNKNOWN")
                sys.exit(3)

def checkforhostconfiguration(ip1,ip2):
        global stat
        sessionid= SANtricityStorage.login(loginUrl,username,password)
        data=checkStorageSystem(sessionid,ip1,ip2)
        if data :
           if data["status"] == "optimal":
               stat=0
           elif data["status"] == "needAttn":
               stat=1
           elif data["status"] == "offline":
               stat=2
           return "Array : "+data["arrayName"] + " is up and running with status \"" + data["status"]+"\""
        else:

           return configureArray(sessionid,ip1,ip2)

try:

        if len(sys.argv) < 7:
            print("STATUS UNKNOWN-Required parameters not set")
            sys.exit(3)
        else:
            nextelearg=False
            argmap={"ip1":"","ip2":"","proxyUrl":"","username":"","password":""}
            argname=""
            for element in sys.argv:
                if element.endswith(".py"):
                   continue
                elif nextelearg :
                    argmap[argname] =element
                    nextelearg=False
                elif element == "-ip1":
                    nextelearg=True
                    argname="ip1"
                elif element =="-ip2":
                    nextelearg=True
                    argname="ip2"
                elif element =="-webproxy":
                    nextelearg=True
                    argname="proxyUrl"
                elif element =="-username":
                    nextelearg=True
                    argname="username"
                elif element =="-password":
                    nextelearg=True
                    argname="password"
                elif element == "-debug":

                    logger.setLevel(logging.DEBUG)
                    logger.addHandler(handler)
                else:
                    print("Invalid arguments passed")
                    sys.exit(3)


            serverUrl = "https://"+argmap["proxyUrl"]

            urlToServer=serverUrl+"/devmgr/v2"

            loginUrl=serverUrl +"/devmgr/utils"

            if argmap["username"] !="":

                username = argmap["username"]

            if argmap["password"] !="":

                password = argmap["password"]

            logger.debug("Server URL:"+serverUrl)
            logger.debug("IP1 :"+argmap["ip1"])
            logger.debug("IP2 :"+argmap["ip2"])
            str=checkforhostconfiguration(argmap["ip1"],argmap["ip2"])

      #  str=loadhardwareinventory()
        print(str)
        sys.exit(stat)
except Exception as err:
        logger.error("Error in HostConfiguration",exc_info=True)
        print("STATUS UNKNOWN")
        sys.exit(3)