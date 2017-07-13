#!/usr/bin/python
# Copyright 2015 NetApp Inc.  All rights reserved.
__author__ = 'hardikJsheth'
import sys
import csv
import logging

import SANtricityStorage
from logging.handlers import RotatingFileHandler

mode=""
hostipaddress=""
webproxy=""
stat=0
logging.basicConfig(format='%(asctime)s - %(name)s : %(message)s',filename='/tmp/nagios-python.log',level=logging.DEBUG)
handler = RotatingFileHandler('/tmp/nagios-python.log', maxBytes=SANtricityStorage.maxbytes,
                                  backupCount=20)
logger=logging.getLogger("PHYSICALCOMPTEMP")
logger.addHandler(handler)
username="rw"
password="rw"

'''
    Get the physical component information  for a array from REST endpoint /graph
    Fetch drive temperature details from  REST endpoint /drives
'''

def get_phy_comp_temprature(arrayid,sessionid,arrayinfo):
    global stat
    logger.info("Inside get_phy_comp_temprature")
    stroutput="\nArray Name:"+arrayinfo[arrayid]["arrayName"]
    strperdata=""

    data = SANtricityStorage.get_data_from_REST(urlToServer,sessionid,arrayid,"graph")
    tmpstatus= data["componentBundle"]["thermalSensor"]
    strpowesupp="\n\nPower Supply and Fan Temperature Status"
    strcont="\n\nController Temperature Status"
    stresm="\n\nESM Temperature Status"
    for ele in tmpstatus:
        crutype=ele["rtrAttributes"]["parentCru"]["type"]

        if crutype in ["supportCru","controller","esm"] and ele["status"] !="optimal":

            stat =2
        if crutype =="supportCru":
            strpowesupp+="\nSlot : "+str(ele["physicalLocation"]["slot"]) +" Status : "+ele["status"]
        elif crutype =="controller":
            strcont+="\nSlot : "+str(ele["physicalLocation"]["slot"]) +" Status : "+ele["status"]
        elif crutype =="esm":
            stresm+="\nSlot : "+str(ele["physicalLocation"]["slot"]) +" Status : "+ele["status"]

    stroutput += strpowesupp + strcont + stresm


    data = SANtricityStorage.get_data_from_REST(urlToServer,sessionid,arrayid,"drives")
    driveinfo= SANtricityStorage.read_csv_file("driverMap.csv","diskId","")

    stroutput+= "\n\nDrive Temperature"
    for ele in data:
        currtemp=float(ele["driveTemperature"]["currentTemp"])
        reftemp=float(ele["driveTemperature"]["refTemp"])
        calwarning = round((warning*reftemp)/100,2)
        calcritical = round((critical *reftemp)/100,2)

        if currtemp > calcritical and stat <2:

            stat = 2
        elif currtemp < calcritical and currtemp > calwarning and stat <= 1:

            stat=1
        logger.debug("Drive Id : "+ele["id"] +", Current Temp : "+str(currtemp) +", Ref Temp : "+str(reftemp))
        stroutput+= "\nDrive : "+driveinfo[ele["id"]]["driveLabel"] + ", Current Temp : "+str(currtemp) +"C, Ref Temp : "+str(ele["driveTemperature"]["refTemp"]) +"C"
        strperdata+=driveinfo[ele["id"]]["driveLabel"]+"="+str(currtemp) +"C;"+str(warning)+";"+str(critical)+";;; "

    return {"strOutPut":stroutput,"strPerData":strperdata}

def getphysicalcomtemprature():
    global stat
    sessionid= SANtricityStorage.login(loginUrl,username,password)
    SANtricityStorage.getStorageSystemDetails(urlToServer,sessionid, SANtricityStorage.getTime())
    file = SANtricityStorage.getStoragePath() + "/controller.csv"
    fileforread=open(file,"rb")
    csvreader=csv.reader(fileforread,delimiter=",")
    firstline=True
    currentarrayid=""
    arrayinfo={}
    strresultdata=""
    strresultperdata=""
    lstresult=[]
    firstarray=True
    contcount=0
    arrayid =""
    for row in csvreader:
        if firstline:
             headerList=row
             firstline =False
        else:
            if hostipaddress and (row[headerList.index("ip1")] == hostipaddress or row[headerList.index("ip2")] == hostipaddress):
                arrayid=row[headerList.index("arrayId")]
                arrayinfo[arrayid]={"arrayName":row[headerList.index("arrayName")]}
                contcount+=1
                if contcount ==2:
                    break
            elif hostipaddress == "":
                arrayid=row[headerList.index("arrayId")]
                arrayinfo[arrayid]={"arrayName":row[headerList.index("arrayName")]}
                if currentarrayid <> arrayid and firstarray ==False:
                        lstresult.append(get_phy_comp_temprature(currentarrayid,sessionid,arrayinfo))
                else:
                     firstarray =False

                currentarrayid =arrayid
    if arrayid :
        lstresult.append(get_phy_comp_temprature(arrayid,sessionid,arrayinfo))
        firstPerData=""
        firstline =True

        for listEle in lstresult:
            strresultdata += listEle["strOutPut"]
            if firstline :
                firstPerData =listEle["strPerData"]
                strArry=firstPerData.split(" ")
                firstspace=firstPerData.index(" ")
                strresultperdata +=firstPerData[firstspace +1:] +" "
                firstPerData=firstPerData[0:firstPerData.index(" ")]

                firstline=False
            else:
                strresultperdata+= listEle["strPerData"]

        strresultperdata = strresultperdata.strip()
        strresultdata = "\nThreshold Values - Warning : " + str(warning) + ", Critical : "+str(critical) +strresultdata
        if stat ==0 :
           strResult = "OK -Temperature of all physical components is good |"+firstPerData +"\n"+strresultdata +"|"+strresultperdata
        elif stat ==1 :
           strResult = "Warning -Temperature of some physical components is above threshold level |"+firstPerData +"\n"+strresultdata +"|"+strresultperdata
        elif stat == 2:
            strResult="Critical- Temperature of some physical components is above critical threshold.|"+firstPerData +"\n"+strresultdata +"|"+strresultperdata
    else:
        strResult = "Unknown-  Host ip address is not configured in web proxy."

        stat=3
    fileforread.close()
    return strResult

try:
    if len(sys.argv) < 8:
        print "STATUS UNKNOWN - Required parameters not set"
        sys.exit(3)
    else:
        nextelearg=False
        argmap={"hostIp":"","proxyUrl":"","warning":"","critical":"","username":"","password":""}
        argname=""
        for element in sys.argv:
            if element.endswith(".py"):
               continue
            elif nextelearg :
                argmap[argname] =element
                nextelearg=False
            elif element == "-h":
                nextelearg=True
                argname="hostIp"
            elif element == "-webproxy":
                nextelearg=True
                argname="proxyUrl"
            elif element == "-warning":
                nextelearg=True
                argname="warning"
            elif element == "-critical":
                nextelearg=True
                argname="critical"
            elif element =="-username":
                nextelearg=True
                argname="username"
            elif element =="-password":
                nextelearg=True
                argname="password"
            elif element == "-debug":

                #logging.basicConfig(format='%(asctime)s - %(name)s : %(message)s',filename='/tmp/nagios-python.log',level=logging.DEBUG)
                logger = logging.getLogger("PHYCOMPSTAT")
                logger.setLevel(logging.DEBUG)
                logger.addHandler(handler)
            else:
                print "STATUS UNKNOWN - Invalid arguments passed"
                sys.exit(3)


        serverUrl="https://"+argmap["proxyUrl"];

        urlToServer=serverUrl+"/devmgr/v2"

        loginUrl=serverUrl +"/devmgr/utils"

        try:

            warning =float(argmap["warning"])
        except Exception:
            logger.error("Error in physical component status",exc_info=True)
            print "STATUS UNKNOWN - Warning threshold must be numeric"
            sys.exit(3)

        try:

            critical =float(argmap["critical"])

        except Exception:
            logger.error("Error in physical component status",exc_info=True)
            print "STATUS UNKNOWN - Critical threshold must be numeric"
            sys.exit(3)

        if argmap["username"] !="":

            username = argmap["username"]

        if argmap["password"] !="":

            password = argmap["password"]

        if warning >= critical:
            print "STATUS UNKNOWN - Incorrect value for warning and critical thresold, warning must be less than critical"
            sys.exit(3)

        if argmap["hostIp"] != "127.0.0.1":
            hostipaddress = argmap["hostIp"]

        logger.debug("Warning Temp:"+argmap["warning"])
        logger.debug("Critical Temp:"+argmap["critical"])

    str=getphysicalcomtemprature()
    print str
    sys.exit(stat)
except Exception,err:
    logger.error("Error in Check_Physical_Comp_Temp",exc_info=True)
    print "STATUS UNKNOWN"
    sys.exit(3)
