#!/usr/bin/python
# Copyright 2015 NetApp Inc.  All rights reserved.
import sys
import csv
import logging

import SANtricityStorage
from logging.handlers import RotatingFileHandler

serverUrl = "https://10.0.1.30:8443"
mode = ""
listMode = {"RIOP": "readIOps", "WIOP": "writeIOps", "RLAT": "readResponseTime", "WLAT": "writeResponseTime",
            "RTHP": "readThroughput", "WTHP": "writeThroughput"}
dirmsg = {"RIOP": "Read IOP", "WIOP": "Write IOP", "RLAT": "Read Latency", "WLAT": "Write Latency",
          "RTHP": "Read Throughput", "WTHP": "Write Throughput"}
dirunit = {"RIOP": "MS", "WIOP": "MS", "RLAT": "MS", "WLAT": "MS", "RTHP": "B", "WTHP": "B"}

urlToServer = serverUrl + "/devmgr/v2"
loginUrl = serverUrl + "/devmgr/utils"

username = "rw"
password = "rw"
logging.basicConfig(format='%(asctime)s - %(name)s : %(message)s', filename='/tmp/nagios-python.log', level=logging.DEBUG)
handler = RotatingFileHandler('/tmp/nagios-python.log', maxBytes=SANtricityStorage.maxbytes,
                                  backupCount=20)

high = 95.0
low = 0.0

stat = 0
hostipaddress = ""
logger = logging.getLogger("VOLUMESTATE")
logger.setLevel(logging.INFO)
logger.addHandler(handler)
range = ""
warningdrives=0
criticaldrives=0
total=0
def getVolumeInfo(arrayId, controllerIds, sessionId, arrayInfo, controllername, controllerdetails):
    try:
        global stat
        logger.debug("In Volume INFO")

        #filedata = SANtricityStorage.getVolumeStates(urlToServer, sessionId, SANtricityStorage.getTime(), arrayId)
        filedata = SANtricityStorage.get_data_from_REST(urlToServer, sessionId, arrayId, "analysed-volume-statistics")
        if filedata:
            lstOfArraySys = filedata
            lst = []
            logger.debug("Response received")

            logger.debug(len(lstOfArraySys))

            dirData = {}

            arryIdWiseInfo = arrayInfo[arrayId]
            volumegroupname = arryIdWiseInfo["volumeGroup"]
            keytofatch = listMode[mode]

            strPerData = ""
            showoutput = False
            global total
            total=len(lstOfArraySys)
            for lst in lstOfArraySys:

                controllerid = lst["controllerId"]
                cntContWise = 0
                if mode == "RTHP" or mode == "WTHP":
                    cntContWise += lst[keytofatch]
                else:
                    cntContWise += lst[keytofatch]

                logger.debug(
                    "Volume Id : " + lst["volumeId"] + ", controllerId : " + lst["controllerId"] + ", poolId : " + lst[
                        "poolId"] + ", " + keytofatch + " : " + str(round(lst[keytofatch], 2)))

                cntContWise = round(cntContWise, 2)
                if (range== "low" and cntContWise <=low and cntContWise >high) or (range =="high" and cntContWise >=low and cntContWise <high):
                    if stat < 1:

                        stat = 1
                    showoutput = True
                    global warningdrives
                    warningdrives +=1
                elif (range == "low" and cntContWise <= high) or (range == "high" and cntContWise >=high):
                    if stat < 2:

                        stat = 2
                    showoutput = True
                    global criticaldrives
                    criticaldrives +=1
                if showoutput:
                    showoutput = False
                    if lst["poolId"] + "~" + controllerid in dirData:
                        strOutPut = (dirData[lst["poolId"] + "~" + controllerid])["strOutput"]
                    else:
                        # strOutPut = controllername[arrayId+"~"+controllerid]
                        strOutPut = "\n\nVolume Group Name : " + volumegroupname[lst["poolId"]]

                    strOutPut += "\nVolume Name : " + lst["volumeName"] + ", " + dirmsg[mode] + " : " + str(cntContWise)
                    dirData[lst["poolId"] + "~" + controllerid] = {"strOutput": strOutPut, "arrayId": arrayId,
                                                                   "controllerId": controllerid}

                strPerData += lst["volumeName"] + "=" + str(cntContWise) + dirunit[mode] + ";" + str(low) + ":" + str(
                    low) + ";@" + str(low) + ":" + str(high) + "; "

            strOutPut = "\nArray Name : " + arrayInfo[arrayId]["arrayName"]
            # controllerdetails={}
            for lstContId in dirData.keys():
                mapdata = dirData[lstContId]
                if mapdata["arrayId"] + "~" + mapdata["controllerId"] not in controllerdetails:
                    strOutPut += "\n\nController Name : " + controllerdetails[mapdata["controllerId"]]
                    controllerdetails[mapdata["arrayId"] + "~" + mapdata["controllerId"]] = 1
                strOutPut += mapdata["strOutput"]

            dirData["strOutPut"] = strOutPut
            dirData["strPerData"] = strPerData

            return dirData
        else:
            print "STATUS UNKNOWN"
            logger.error("No data returned from REST end point", exc_info=True)
            sys.exit(3)

    except Exception, err:
        logger.error("Error in getvolumeinfo", exc_info=True)
        print "STATUS UNKNOWN"
        sys.exit(3)
        # return False


def getVolumeState():
    global stat
    sessionid = SANtricityStorage.login(loginUrl, username, password)
    logger.debug("Inside getvolumestate")
    SANtricityStorage.getStorageSystemDetails(urlToServer, sessionid, SANtricityStorage.getTime())
    file = SANtricityStorage.getStoragePath() + "/controller.csv"
    fileForRead = open(file, "rb")
    csvReader = csv.reader(fileForRead, delimiter=",")
    firstLine = True
    controllername = {}
    controllerdetails = {}
    for row in csvReader:
        if firstLine:
            headerList = row
            firstLine = False
        else:
            if (hostipaddress and row[headerList.index("ip1")] == hostipaddress or row[
                headerList.index("ip2")] == hostipaddress ) or hostipaddress == "":
                controllername[row[headerList.index("arrayId")] + "~" + row[
                    headerList.index("controllerRef")]] = "\nArray Name : " + row[
                    headerList.index("arrayName")] + ", Controller Name : " + row[headerList.index("controllerLabel")]
                controllerdetails[row[headerList.index("controllerRef")]] = row[headerList.index("controllerLabel")]
    if len(controllername) == 0:
        strResult = "Unknown-  Host ip address not configured in web proxy."
        global stat;
        stat = 3
        return strResult
    file = SANtricityStorage.getStoragePath() + "/VolumeGroup.csv"
    fileForRead = open(file, "rb")
    csvReader = csv.reader(fileForRead, delimiter=",")
    firstLine = True
    currentArrayId = ""
    controllerId = []

    arrayInfo = {}
    strResultData = ""
    strResultPerData = ""
    lstResult = []
    volumegroupName = {}
    for row in csvReader:
        if firstLine:
            headerList = row
            firstLine = False
        else:
            if hostipaddress and (
                    row[headerList.index("ip1")] == hostipaddress or row[headerList.index("ip2")] == hostipaddress):
                controllerId.append(row[headerList.index("volumeGroupRef")])
                volumegroupName[row[headerList.index("volumeGroupRef")]] = row[headerList.index("volumeGroup")]
                arrayId = row[headerList.index("arrayId")]
                arrayInfo[arrayId] = {"arrayName": row[headerList.index("arrayName")], "volumeGroup": volumegroupName}

            elif hostipaddress == "":

                arrayId = row[headerList.index("arrayId")]
                arrayInfo[arrayId] = {"arrayName": row[headerList.index("arrayName")], "volumeGroup": volumegroupName}
                if currentArrayId <> arrayId and len(controllerId) <> 0:
                    (arrayInfo[currentArrayId])["volumeGroup"] = volumegroupName
                    lstResult.append(getVolumeInfo(currentArrayId, controllerId, sessionid, arrayInfo, controllername,
                                                   controllerdetails))

                    controllerId = []
                    volumegroupName = {}
                    controllerId.append(row[headerList.index("volumeGroupRef")])
                    volumegroupName[row[headerList.index("volumeGroupRef")]] = row[headerList.index("volumeGroup")]
                elif currentArrayId <> arrayId:
                    controllerId = []
                    volumegroupName = {}
                    controllerId.append(row[headerList.index("volumeGroupRef")])
                    volumegroupName[row[headerList.index("volumeGroupRef")]] = row[headerList.index("volumeGroup")]
                else:
                    controllerId.append(row[headerList.index("volumeGroupRef")])
                    volumegroupName[row[headerList.index("volumeGroupRef")]] = row[headerList.index("volumeGroup")]
                currentArrayId = arrayId
    if arrayId:
        (arrayInfo[arrayId])["volumeGroup"] = volumegroupName

        lstResult.append(getVolumeInfo(arrayId, controllerId, sessionid, arrayInfo, controllername, controllerdetails))
        firstPerData = ""
        firstLine = True
        for listEle in lstResult:
            strResultData += listEle["strOutPut"]
            if firstLine:
                firstPerData = listEle["strPerData"]

                firstspace = firstPerData.index(" ")
                strResultPerData += firstPerData[firstspace + 1:] + " "
                firstPerData = firstPerData[0:firstPerData.index(" ")]

                firstLine = False
            else:
                strResultPerData += listEle["strPerData"]

        strResultPerData = strResultPerData.strip()
        strResultData = "\nThreshold Values - Range Selector : "+ range +", Warning : " + str(low) + ", Critical : " + str(high) +\
                         "\nVolume Statistics\n Total : "+str(total) +", OK : "\
                         + str(total- (warningdrives + criticaldrives)) + ", Warning : "+str(warningdrives) + \
                         ", Critical : "+str(criticaldrives) + strResultData
        if stat == 0:
            strResult = "OK - All volumes are functioning within defined threshold values.|" + firstPerData + strResultData + "|" + strResultPerData
        elif stat == 1:
            strResult = "Warning - Some volumes  are functioning at beyond warning threshold.|" + firstPerData + "\n" + strResultData + "|" + strResultPerData
        elif stat == 2:
            strResult = "Critical - Some volumes  are functioning at beyond critical threshold.|" + firstPerData + "\n" + strResultData + "|" + strResultPerData
    else:
        strResult = "Unknown -  Host ip address not configured in web proxy."

        stat = 3
    fileForRead.close()
    return strResult


try:
    logger.debug("STarting execution of Volume Status")
    if len(sys.argv) < 10:
        print "STATUS UNKNOWN - Required parameters not set"
        logging.error("Required parameters not set")
        sys.exit(3)
    else:

        nextelearg = False
        argmap = {"mode": "", "hostIp": "", "proxyUrl": "", "warning": "", "critical": "", "r": "", "username": "",
                  "password": ""}
        argname = ""
        for element in sys.argv:
            if element.endswith(".py"):
                continue
            elif nextelearg:
                argmap[argname] = element
                nextelearg = False
            elif element == "-mode":
                nextelearg = True
                argname = "mode"
            elif element == "-warning":
                nextelearg = True
                argname = "warning"
            elif element == "-critical":
                nextelearg = True
                argname = "critical"
            elif element == "-h":
                nextelearg = True
                argname = "hostIp"
            elif element == "-webproxy":
                nextelearg = True
                argname = "proxyUrl"
            elif element == "-username":
                nextelearg = True
                argname = "username"
            elif element == "-password":
                nextelearg = True
                argname = "password"
            elif element == "-r":
                nextelearg = True
                argname = "r"
            elif element == "-debug":

                logger = logging.getLogger("VOLUMESTATE")
                logger.setLevel(logging.DEBUG)
                logger.addHandler(handler)
            else:
                print "Invalid arguments passed"
                sys.exit(3)


        serverUrl = "https://" + argmap["proxyUrl"];

        urlToServer = serverUrl + "/devmgr/v2"

        loginUrl = serverUrl + "/devmgr/utils"


        mode = argmap["mode"];

        try:
            index = listMode[mode];
        except:
            print "STATUS UNKNOWN - Incorrect value for mode"
            sys.exit(3)

        if argmap["r"] != "":
            global range
            range = argmap["r"]
        else:
            print "STATUS UNKNOW - No range selector defined."
            sys.exit(3)

        if range != "low" and range != "high":
            print "STATUS UNKNOW - Incorrect value for range selector. It must be either \"low\" or \"high\". "
            sys.exit(3)



        try:
            low = float(argmap["warning"])
        except Exception, err:
            print "STATUS UNKNOWN - Warning threshold must be numeric"
            sys.exit(3)


        try:
            high = float(argmap["critical"])
        except Exception, err:
            print "STATUS UNKNOWN - Critical threshold must be numeric"
            sys.exit(3)

        if (range == "high" and low >= high) or (range == "low" and low <= high):
            print 'STATUS UNKNOWN - Incorrect value for warning and critical threshold'
            sys.exit(3)

        if argmap["username"] !="":

            username = argmap["username"]

        if argmap["password"] !="":

            password = argmap["password"]


        if argmap["hostIp"] != '127.0.0.1':
            hostipaddress = argmap["hostIp"]
    logger.debug("Low Threshold:" + str(low))
    logger.debug("High Threshold:" + str(high))
    logger.debug("Server URL:" + serverUrl)
    logger.debug("Host Add" + hostipaddress)
    logger.debug("Mode:" + mode)
    logger.debug("Range:" + range)
    str = getVolumeState()
    print str
    sys.exit(stat)
except Exception, err:
    logging.error("Error in Volume Status", exc_info=True)
    print "STATUS UNKNOWN"
    sys.exit(3)

