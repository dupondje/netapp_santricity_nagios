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

logging.basicConfig(format='%(asctime)s - %(name)s : %(message)s', filename='nagios-python.log', level=logging.INFO)
handler = RotatingFileHandler('nagios-python.log', maxBytes=SANtricityStorage.maxbytes,
                                  backupCount=20)

high = 95.0
low = 0.0
range = ""
username = "rw"
password = "rw"
warningdrive=0
criticaldrive=0
stat = 0
hostipaddress = ""
logger = logging.getLogger("VOLUMESTATBYCONT")

logger.setLevel(logging.INFO)
logger.addHandler(handler)

def get_volume_info(arrayid, controllerids, sessionid, arrayinfo):
    global total
    global stat
    global warningdrive
    global criticaldrive
    try:
        logger.debug("In Volume INFO")

        lstOfArraySys = []
        lstOfArraySys = SANtricityStorage.get_data_from_REST(urlToServer, sessionid, arrayid,
                                                             "analysed-volume-statistics")

        if lstOfArraySys and len(lstOfArraySys) > 0:

            logger.debug("Response received")
            logger.debug(len(lstOfArraySys))

            dirdata = {}

            arrayidwiseinfo = arrayinfo[arrayid]
            controllername = arrayidwiseinfo["controllerLabel"]
            keytofatch = listMode[mode]
            for lst in lstOfArraySys:

                if lst["controllerId"] not in dirdata:
                    dirdata[lst["controllerId"]] = {"readIOP": 0}
                    cntconwise = 0

                logger.debug(
                    "Volume Id : " + lst["volumeId"] + ", controllerId : " + lst["controllerId"] + ", poolId : " + lst[
                        "poolId"] + ", " + keytofatch + " : " + str(round(lst[keytofatch], 2)))
                cntconwise = (dirdata[lst["controllerId"]])["readIOP"]
                if mode == "RTHP" or mode == "WTHP":
                    # cntconwise+=(lst[keytofatch] /(1024*1024))
                    cntconwise += round(lst[keytofatch], 2)
                else:
                    # cntconwise+=lst[keytofatch]/1000
                    cntconwise += round(lst[keytofatch], 2)

                (dirdata[lst["controllerId"]])["readIOP"] = cntconwise

            strOutPut = ""
            strPerData = ""
            showoutput = False

            total =len(controllerids)
            for lstContId in controllerids:
                lstrContData = dirdata[lstContId]
                contwiseLat = lstrContData["readIOP"]
                if (range== "low" and contwiseLat <=low and contwiseLat >high) or (range =="high" and contwiseLat >=low and contwiseLat <high):
                    if stat < 1:

                        stat = 1

                    warningdrive +=1
                    showoutput = True
                elif (range == "low" and contwiseLat <= high) or (range == "high" and contwiseLat >=high):
                    if stat < 2:

                        stat = 2
                    showoutput = True

                    criticaldrive +=1

                contwiseLat = round(contwiseLat, 2)
                if showoutput:
                    strOutPut += "\nArray Name : " + arrayidwiseinfo["arrayName"] + ", Controller Name : " + \
                                 controllername[lstContId] + ", " + dirmsg[mode] + " : " + str(contwiseLat)
                strPerData += arrayidwiseinfo["arrayName"] + "-" + controllername[lstContId] + "=" + str(contwiseLat) + \
                              dirunit[mode] + ";" + str(low) + ":" + str(low) + ";@" + str(low) + ":" + str(high) + "; "
                showoutput = False
            dirdata["strOutPut"] = strOutPut
            dirdata["strPerData"] = strPerData

            return dirdata
        else:
            print "STATUS UNKNOWN - No details fetched from the array."
            sys.exit(3)

    except Exception, err:
        logger.error("Error in get volume info", exc_info=True)
        # return False


def getVolumeState():
    global stat
    sessionId = SANtricityStorage.login(loginUrl,username,password)
    logger.debug("In getVolume State method")
    SANtricityStorage.getStorageSystemDetails(urlToServer, sessionId, SANtricityStorage.getTime())

    file = SANtricityStorage.getStoragePath() + "/controller.csv"
    fileForRead = open(file, "rb")
    csvReader = csv.reader(fileForRead, delimiter=",")
    firstLine = True
    currentArrayId = ""
    controllerId = []
    arrayInfo = {}
    strResultData = ""
    strResultPerData = ""
    lstResult = []
    controllerName = {}
    arrayId = ""
    for row in csvReader:
        if firstLine:
            headerList = row
            firstLine = False
        else:
            if hostipaddress and (
                    row[headerList.index("ip1")] == hostipaddress or row[headerList.index("ip2")] == hostipaddress):
                controllerId.append(row[headerList.index("controllerRef")])
                controllerName[row[headerList.index("controllerRef")]] = row[headerList.index("controllerLabel")]
                arrayId = row[headerList.index("arrayId")]
                arrayInfo[arrayId] = {"arrayName": row[headerList.index("arrayName")],
                                      "controllerLabel": controllerName}

            elif hostipaddress == "":

                arrayId = row[headerList.index("arrayId")]
                arrayInfo[arrayId] = {"arrayName": row[headerList.index("arrayName")],
                                      "controllerLabel": controllerName}
                if currentArrayId <> arrayId and len(controllerId) <> 0:
                    (arrayInfo[currentArrayId])["controllerLabel"] = controllerName
                    lstResult.append(get_volume_info(currentArrayId, controllerId, sessionId, arrayInfo))
                    controllerId = []
                    controllerName = {}
                    controllerId.append(row[headerList.index("controllerRef")])
                    controllerName[row[headerList.index("controllerRef")]] = row[headerList.index("controllerLabel")]
                elif currentArrayId <> arrayId:
                    controllerId = []
                    controllerName = {}
                    controllerId.append(row[headerList.index("controllerRef")])
                    controllerName[row[headerList.index("controllerRef")]] = row[headerList.index("controllerLabel")]
                else:
                    controllerId.append(row[headerList.index("controllerRef")])
                    controllerName[row[headerList.index("controllerRef")]] = row[headerList.index("controllerLabel")]
                currentArrayId = arrayId
    if arrayId:
        (arrayInfo[arrayId])["controllerLabel"] = controllerName

        lstResult.append(get_volume_info(arrayId, controllerId, sessionId, arrayInfo))
        firstPerData = ""
        firstLine = True
        for listEle in lstResult:
            strResultData += listEle["strOutPut"]
            if firstLine:
                firstPerData = listEle["strPerData"]
                strArry = firstPerData.split(" ")
                firstPerData = strArry[0]
                strResultPerData += strArry[1] + " "
                firstLine = False
            else:
                strResultPerData += listEle["strPerData"]

        strResultPerData = strResultPerData.strip()

        strResultData = "\nThreshold Values - Range Selector : "+range +", Warning : " + str(low) + ", Critical : " \
                        + str(high)+"\nVolume Statistics by Controller\nTotal : "+str(total)+", OK : "+\
                        str(total -(warningdrive +criticaldrive))+", Warning : "+str(warningdrive)+\
                        ", Critical : "+str(criticaldrive) + strResultData


        if stat == 0:
            strResult = "OK - All controllers are within defined threshold.|" + firstPerData + "\n" + strResultData + "|" + strResultPerData
        elif stat == 1:
            strResult = "Warning - Some controllers are functioning at threshold values.|" + firstPerData + "\n" + strResultData + "|" + strResultPerData
        elif stat == 2:
            strResult = "Critical - Some controllers are out side threshold values.|" + firstPerData + "\n" + strResultData + "|" + strResultPerData

    else:

        stat = 3
        strResult = "Unknown - Host Ip is not configured with web proxy"

    fileForRead.close()
    return strResult


try:
    logger.info("Hi in file")
    if len(sys.argv) < 8:
        print "STATUS UNKNOWN - Required parameters not set"
        sys.exit(3)
    else:
        nextelearg = False
        argmap = {"mode": "", "hostIp": "", "proxyUrl": "", "warning": "", "critical": "","r":"","username":"","password":""}
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

                logger = logging.getLogger("VOLUMESTATBYCONT")
                logger.setLevel(logging.DEBUG)
                logger.addHandler(handler)
            else:
                print "Invalid arguments passed"
                sys.exit(3)


        serverUrl = "https://" + argmap["proxyUrl"];

        urlToServer = serverUrl + "/devmgr/v2"

        loginUrl = serverUrl + "/devmgr/utils"

        if argmap["r"] != "":

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
            global username
            username = argmap["username"]

        if argmap["password"] !="":
            global password
            password = argmap["password"]


        mode = argmap["mode"];

        try:
            index = listMode[mode];
        except:
            print "STATUS UNKNOWN - Incorrect value for mode"
            sys.exit(3)


        hostipaddress = argmap["hostIp"]

    logger.debug("Low Threshold:" + str(low))
    logger.debug("High Threshold:" + str(high))
    logger.debug("Server URL:" + serverUrl)
    logger.debug("Host Add" + hostipaddress)
    logger.debug("Mode:" + mode)
    str = getVolumeState()
    print str
    sys.exit(stat)
except Exception, err:
    logger.error("Error inside get volume stat by controller", exc_info=True)
    print "STATUS UNKNOWN"
    sys.exit(3)

