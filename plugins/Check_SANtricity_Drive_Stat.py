#!/usr/bin/python
# Copyright 2015 NetApp Inc.  All rights reserved.

__author__ = 'hardikJsheth'
import sys
import csv
import logging

import SANtricityStorage
from logging.handlers import RotatingFileHandler

serverUrl="https://10.0.1.30:8443"
mode= ""
listMode = {"RIOP":"readIOps","WIOP":"writeIOps","RLAT":"readResponseTime","WLAT":"writeResponseTime","RTHP":"readThroughput","WTHP":"writeThroughput"}
dirmsg ={"RIOP":"Read IOP","WIOP":"Write IOP","RLAT":"Read Latency","WLAT":"Write Latency","RTHP":"Read Throughput","WTHP":"Write Throughput"}
dirunit={"RIOP":"MS","WIOP":"MS","RLAT":"MS","WLAT":"MS","RTHP":"B","WTHP":"B"}
timewindow=5
urlToServer=serverUrl+"/devmgr/v2"
loginUrl=serverUrl +"/devmgr/utils"
logging.basicConfig(format='%(asctime)s - %(name)s : %(message)s',filename='nagios-python.log',level=logging.DEBUG)
handler = RotatingFileHandler('nagios-python.log', maxBytes=SANtricityStorage.maxbytes,
                                  backupCount=20)
high=95.0
low=0.0
stat=0
hostipaddress=""
logger = logging.getLogger("DRIVESTATE")
logger.setLevel(logging.INFO)
logger.addHandler(handler)
username="rw"
password="rw"
range ="low"
'''
    This method fetches drive stats from REST end point "analysed-drive-statistics"
'''
def get_drive_detail(arrayid,sessionid,arrayinfo):
    global stat
    datalist = SANtricityStorage.get_data_from_REST(urlToServer,sessionid,arrayid,"analysed-drive-statistics")
    stroutput=""
    strperfoutput=""
    driveinfo= SANtricityStorage.read_csv_file("driverMap.csv","diskId","")
    showoutput=False
    totaldrives=0
    criticaldrive=0
    warningdrive=0

    for ele in datalist:
        totaldrives+=1
        logger.debug("Drive Id : "+ele["diskId"]+", "+listMode[mode]+" : "+str(round(ele[listMode[mode]],2)))
        if mode == "RTHP" or mode =="WTHP" :
            val = ele[listMode[mode]]
        else:
            val = ele[listMode[mode]]

        val= round(val,2)
        if (range== "low" and val <=low and val >high) or (range =="high" and val >=low and val <high):
            if stat <1:

                stat=1
            showoutput =True
            warningdrive += 1

        elif (range == "low" and val <= high) or (range == "high" and val >=high):
            if stat < 2:

                stat=2
            showoutput =True
            criticaldrive += 1


        if showoutput:
            stroutput += "\nDrive Label : "+driveinfo[ele["diskId"]]["driveLabel"] +", "+dirmsg[mode] +" : "+str(val)

        showoutput=False
        strperfoutput+=driveinfo[ele["diskId"]]["driveLabel"]+"="+str(val)+dirunit[mode]+";"+str(low)+":"+ str(low) +";@"+str(low)+":"+str(high) +"; "
        finaloutput="\nThresold Values - Range Selector : "+range+", Warning : "+str(low)+", Critical : "+str(high)+"\nDrive Statistics\nTotal : "+str(totaldrives) +", Critical : "+str(criticaldrive) + ", Warning : "+str(warningdrive) + ", OK : "+str(totaldrives -criticaldrive -warningdrive)+"\nArray Name:"+ arrayinfo[arrayid]["arrayName"]+stroutput
    return {"strOutPut":finaloutput ,"strPerData":strperfoutput}

'''
    Read controller.csv file to get array information. Use this information for fetching drive stats.
'''
def get_drive_state():
    global stat
    logger.info("Inside get_drive_state method.")
    sessionid= SANtricityStorage.login(loginUrl,username,password)
    SANtricityStorage.getStorageSystemDetails(urlToServer,sessionid,timewindow)
    file = SANtricityStorage.getStoragePath() + "/controller.csv"
    fileforread=open(file,"rb")
    csvreader=csv.reader(fileforread,delimiter=",")
    firstline=True
    currentarrayid=""

    arrayinfo={}
    strresultdata=""
    strresultperdata=""
    lstResult=[]
    firstArray=True
    controllername={}
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
                controllername[row[headerList.index("controllerRef")]]=row[headerList.index("controllerLabel")]
                contcount += 1
                if contcount == 2:
                    break
            elif  hostipaddress == "":
                arrayid=row[headerList.index("arrayId")]
                arrayinfo[arrayid]={"arrayName":row[headerList.index("arrayName")]}
                if currentarrayid <> arrayid and firstArray == False:
                    lstResult.append(get_drive_detail(currentarrayid,sessionid,arrayinfo))
                    controllername={}
                    controllername[row[headerList.index("controllerRef")]]=row[headerList.index("controllerLabel")]
                else:
                   firstArray =False
                currentarrayid = arrayid

    if arrayid:
        lstResult.append(get_drive_detail(arrayid,sessionid,arrayinfo))
        firstperdata = ""
        firstline = True

        for listEle in lstResult:
            strresultdata += listEle["strOutPut"]
            if firstline :
                firstperdata =listEle["strPerData"]
                firstspace=firstperdata.index(" ")
                strresultperdata +=firstperdata[firstspace +1:] +" "
                firstperdata=firstperdata[0:firstperdata.index(" ")]
                firstline=False
            else:
                strresultperdata+= listEle["strPerData"]

        strresultperdata = strresultperdata.strip()

        if stat ==0 :
           strresult = "OK - All  drives are working within defined threshold values.|"+firstperdata +"\n"+strresultdata +"|"+strresultperdata
        elif stat == 1 :
           strresult = "Warning - Some drives are working at threshold values.|"+firstperdata +"\n"+strresultdata +"|"+strresultperdata
        elif stat == 2:
            strresult = "Critical - Some drives are working beyond threshold values.|"+firstperdata +"\n"+strresultdata +"|"+strresultperdata
    else:
        strresult = "Unknown -  Host ip address not configured in web proxy."

        stat=3
    fileforread.close()
    return strresult

try:
    if len(sys.argv) < 10:
        print "STATUS UNKNOWN - Required parameters not set"
        sys.exit(3)
    else:
        nextelearg=False
        argmap={"mode":"","hostIp":"","proxyUrl":"","warning":"","critical":"","username":"","password":"", "r":""}
        argname=""

        for element in sys.argv:
            if element.endswith(".py"):
               continue
            elif nextelearg :
                argmap[argname] =element
                nextelearg=False
            elif element == "-mode":
                nextelearg=True
                argname="mode"
            elif element == "-warning":
                nextelearg=True
                argname= "warning"
            elif element == "-critical":
                nextelearg=True
                argname="critical"
            elif element == "-h":
                nextelearg=True
                argname="hostIp"
            elif element == "-webproxy":
                nextelearg=True
                argname="proxyUrl"
            elif element =="-username":
                nextelearg=True
                argname="username"
            elif element =="-password":
                nextelearg=True
                argname="password"
            elif element =="-r":
                nextelearg=True
                argname="r"
            elif element == "-debug":

                logger = logging.getLogger("DRIVESTATE")
                logger.setLevel(logging.DEBUG)
                logger.addHandler(handler)
            else:
                print "Invalid arguments passed"
                sys.exit(3)


        serverUrl="https://"+argmap["proxyUrl"];

        urlToServer=serverUrl+"/devmgr/v2"

        loginUrl=serverUrl +"/devmgr/utils"


        mode = argmap["mode"];

        try:
            index=listMode[mode];
        except:
            print "STATUS UNKNOWN - Incorrect value for mode"
            sys.exit(3)


        if argmap["r"] !="":

            range= argmap["r"]
            if range !="low" and range !="high":
                print "STATUS UNKNOW - Incorrect value for range selector. It must be either \"low\" or \"high\". "
                sys.exit(3)

        try:
            low=float(argmap["warning"])
        except Exception,err:
            print "STATUS UNKNOWN - Warning threshold must be numeric"
            sys.exit(3)



        try:
            high=float(argmap["critical"])
        except Exception,err:
            print "STATUS UNKNOWN - Critical threshold must be numeric"
            sys.exit(3)


        if (range == "high" and low >=high) or (range =="low" and low <= high):
            print 'STATUS UNKNOWN - Incorrect value for warning and critical threshold'
            sys.exit(3)


        if argmap["hostIp"] != '127.0.0.1':
            hostipaddress = argmap["hostIp"]

        if argmap["username"] !="":

            username = argmap["username"]

        if argmap["password"] !="":

            password = argmap["password"]


    logger.debug("Low Threshold:"+str(low))
    logger.debug("High Threshold:"+str(high))
    logger.debug("Server URL:"+serverUrl)
    logger.debug("Host Add"+hostipaddress)
    logger.debug("Mode:"+mode)
    logger.debug("Range:"+range)
    str=get_drive_state()
    print str
    sys.exit(stat)
except Exception,err:
    logging.error("Error in main block",exc_info=True)

    print "STATUS UNKNOWN"
    sys.exit(3)