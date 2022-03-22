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


logging.basicConfig(format='%(asctime)s - %(name)s : %(message)s', filename='/tmp/nagios-python.log', level=logging.DEBUG)
logger = logging.getLogger("VOLSTATBYVG")
high = 95.0
low = 0.0

stat = 0
hostipaddress = ""
handler = RotatingFileHandler('/tmp/nagios-python.log', maxBytes=SANtricityStorage.maxbytes, backupCount=20)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

range = "r"
username = "rw"
password = "rw"
warningdrive=0
criticaldrive=0
total=0

def getVolumeInfo(arrayId, controllerIds, sessionId, arrayInfo, controllername, controllerDetails):
    global stat
    global warningdrive
    global  total
    global criticaldrive
    try:
        logger.info("In Volume INFO")

        lstOfArraySys = SANtricityStorage.get_data_from_REST(urlToServer, sessionId, arrayId,
                                                             "analysed-volume-statistics")
        if lstOfArraySys and len(lstOfArraySys) > 0:
            logger.info("Response received")
            logger.info(len(lstOfArraySys))

            dirData = {}

            arryIdWiseInfo = arrayInfo[arrayId]
            volumegroupname = arryIdWiseInfo["volumeGroup"]
            keytofatch = listMode[mode]
            for lst in lstOfArraySys:
                controllerid = lst["controllerId"]

                if lst["poolId"] + "~" + controllerid in dirData:
                    cntContWise = (dirData[lst["poolId"] + "~" + controllerid])["readIOP"]
                else:
                    cntContWise = 0.0
                    dirData[lst["poolId"] + "~" + controllerid] = {"readIOP": 0, "controllerId": controllerid,
                                                                   "poolId": lst["poolId"]}
                if mode == "RTHP" or mode == "WTHP":
                    # cntContWise+=int(lst[keytofatch] /(1024*1024))
                    cntContWise += (lst[keytofatch])
                else:
                    # cntContWise+=lst[keytofatch]/1000
                    cntContWise += lst[keytofatch]

                logger.debug(
                    "Volume Id : " + lst["volumeId"] + ", controllerId : " + lst["controllerId"] + ", poolId : " + lst[
                        "poolId"] + ", " + keytofatch + " : " + str(round(lst[keytofatch], 2)))

                (dirData[lst["poolId"] + "~" + controllerid])["readIOP"] = cntContWise

            strPerData = ""

            showoutput = False

            total = len(dirData.keys())
            for lstContId in dirData.keys():
                lstrContData = dirData[lstContId]
                contwiseLat = lstrContData["readIOP"]
                contwiseLat = round(contwiseLat, 2)
                if (range== "low" and contwiseLat <=low and contwiseLat >high) or (range =="high" and contwiseLat >=low and contwiseLat <high):
                    if stat < 1:

                        stat = 1
                    showoutput = True

                    warningdrive +=1
                elif (range == "low" and contwiseLat <= high) or (range == "high" and contwiseLat >=high):
                    if stat < 2:

                        stat = 2
                    showoutput = True

                    criticaldrive +=1

                if showoutput:
                    strOutPut = controllername[arrayId + "~" + lstrContData["controllerId"]]
                    strOutPut += "\nVolume Group Name : " + volumegroupname[lstrContData["poolId"]] + ", " + dirmsg[
                        mode] + " : " + str(contwiseLat)
                    controllername[arrayId + "~" + lstrContData["controllerId"]] = strOutPut
                showoutput = False
                strPerData += controllerDetails[lstrContData["controllerId"]] + "-" + volumegroupname[
                    lstrContData["poolId"]] + "=" + str(contwiseLat) + dirunit[mode] + ";" + str(low) + ":" + str(
                    low) + ";@" + str(low) + ":" + str(high) + "; "

            strOutPut = ""
            for stopdata in list(controllername.keys()):
                if stopdata.find(arrayId) > -1:
                    strOutPut += "\n" + controllername[stopdata]

            dirData["strOutPut"] = strOutPut
            dirData["strPerData"] = strPerData

            return dirData
        else:
            print("STATUS UNKNOWN - No volumes returned from array.")
            sys.exit(3)

    except Exception as err:
        logger.error("Error in getting volume state by controller", exec_info=True)

        # return False


def getVolumeState():
    global stat
    sessionid = SANtricityStorage.login(loginUrl,username,password)

    SANtricityStorage.getStorageSystemDetails(urlToServer, sessionid,SANtricityStorage.getTime())
    file = SANtricityStorage.getStoragePath() + "/controller.csv"
    fileForRead = open(file, "r")
    csvReader = csv.reader(fileForRead, delimiter=",")
    firstLine = True
    controllername = {}
    controllerDetails = {}
    for row in csvReader:
        if firstLine:
            headerList = row
            firstLine = False
        else:
            if (hostipaddress and row[headerList.index("ip1")] == hostipaddress or row[
                headerList.index("ip2")] == hostipaddress ) or hostipaddress == "":
                controllername[row[headerList.index("arrayId")] + "~" + row[
                    headerList.index("controllerRef")]] = "\nArray Name : " + row[
                    headerList.index("arrayName")] + ", Controller Name : " + row[
                                                              headerList.index("controllerLabel")] + "\n"
                controllerDetails[row[headerList.index("controllerRef")]] = row[headerList.index("controllerLabel")]
    file = SANtricityStorage.getStoragePath() + "/VolumeGroup.csv"
    fileForRead = open(file, "r")
    csvReader = csv.reader(fileForRead, delimiter=",")
    firstLine = True
    currentArrayId = ""
    controllerId = []

    arrayInfo = {}
    strresultdata = ""
    strResultPerData = ""
    lstResult = []
    volumegroupname = {}
    arrayId = ""
    for row in csvReader:
        if firstLine:
            headerList = row
            firstLine = False
        else:
            if hostipaddress and (
                    row[headerList.index("ip1")] == hostipaddress or row[headerList.index("ip2")] == hostipaddress):
                controllerId.append(row[headerList.index("volumeGroupRef")])
                volumegroupname[row[headerList.index("volumeGroupRef")]] = row[headerList.index("volumeGroup")]
                arrayId = row[headerList.index("arrayId")]
                arrayInfo[arrayId] = {"arrayName": row[headerList.index("arrayName")], "volumeGroup": volumegroupname}

            elif hostipaddress == "":

                arrayId = row[headerList.index("arrayId")]
                arrayInfo[arrayId] = {"arrayName": row[headerList.index("arrayName")], "volumeGroup": volumegroupname}
                if currentArrayId != arrayId and len(controllerId) != 0:
                    (arrayInfo[arrayId])["volumeGroup"] = volumegroupname
                    lstResult.append(getVolumeInfo(currentArrayId, controllerId, sessionid, arrayInfo, controllername,
                                                   controllerDetails))
                    controllerId = []
                    volumegroupname = {}
                    controllerId.append(row[headerList.index("volumeGroupRef")])
                    volumegroupname[row[headerList.index("volumeGroupRef")]] = row[headerList.index("volumeGroup")]
                elif currentArrayId != arrayId:
                    controllerId = []
                    volumegroupname = {}
                    controllerId.append(row[headerList.index("volumeGroupRef")])
                    volumegroupname[row[headerList.index("volumeGroupRef")]] = row[headerList.index("volumeGroup")]
                else:
                    controllerId.append(row[headerList.index("volumeGroupRef")])
                    volumegroupname[row[headerList.index("volumeGroupRef")]] = row[headerList.index("volumeGroup")]
                currentArrayId = arrayId
    if arrayId:
        (arrayInfo[arrayId])["volumeGroup"] = volumegroupname

        lstResult.append(getVolumeInfo(arrayId, controllerId, sessionid, arrayInfo, controllername, controllerDetails))
        firstPerData = ""
        firstLine = True
        for listEle in lstResult:
            strresultdata += listEle["strOutPut"]
            if firstLine:
                firstPerData = listEle["strPerData"]
                strArry = firstPerData.split(" ")
                firstspace = firstPerData.index(" ")
                strResultPerData += firstPerData[firstspace + 1:] + " "
                firstPerData = firstPerData[0:firstPerData.index(" ")]

                firstLine = False
            else:
                strResultPerData += listEle["strPerData"]

        strResultPerData = strResultPerData.strip()
        strresultdata = "\nThreshold Values - Range Selector : "+range +", Warning : " + str(low) + ", Critical : " \
                        + str(high)+"\n Volume Statistics By Volume Group\nTotal : "+str(total) +", Ok : "+ \
                        str(total - (warningdrive + criticaldrive))+", Warning : "+str(warningdrive)\
                        +", Critical : "+str(criticaldrive)+ strresultdata
        if stat == 0:
            strResult = "OK - All volume groups are within the defined threshold.|" + firstPerData + strresultdata + "|" + strResultPerData
        elif stat == 1:
            strResult = "Warning - Some volume groups are functioning at threshold values.|" + firstPerData + "\n" + strresultdata + "|" + strResultPerData
        elif stat == 2:
            strResult = "Critical - Some volume groups are out side threshold values.|" + firstPerData + "\n" + strresultdata + "|" + strResultPerData

    else:
        strResult = "Unknown -  Host ip address is not configured in web proxy."

        stat = 3
    fileForRead.close()
    return strResult


try:
    if len(sys.argv) < 10:
        print("STATUS UNKNOWN - Required parameters not set")
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

                logger = logging.getLogger("VOLUMESTATE")
                logger.setLevel(logging.DEBUG)
                logger.addHandler(handler)
            else:
                print("Invalid arguments passed")
                sys.exit(3)


        serverUrl = "https://" + argmap["proxyUrl"];

        urlToServer = serverUrl + "/devmgr/v2"

        loginUrl = serverUrl + "/devmgr/utils"


        mode = argmap["mode"];

        try:
            index = listMode[mode];
        except:
            print("STATUS UNKNOWN - Incorrect value for mode")
            sys.exit(3)

        if argmap["r"] != "":

            range = argmap["r"]
        else:
            print("STATUS UNKNOW - No range selector defined.")
            sys.exit(3)

        if range != "low" and range != "high":
            print("STATUS UNKNOW - Incorrect value for range selector. It must be either \"low\" or \"high\". ")
            sys.exit(3)



        try:
            low = float(argmap["warning"])
        except Exception as err:
            print("STATUS UNKNOWN - Warning threshold must be numeric")
            sys.exit(3)


        try:
            high = float(argmap["critical"])
        except Exception as err:
            print("STATUS UNKNOWN - Critical threshold must be numeric")
            sys.exit(3)

        if (range == "high" and low >= high) or (range == "low" and low <= high):
            print('STATUS UNKNOWN - Incorrect value for warning and critical threshold')
            sys.exit(3)

        if argmap["username"] !="":

            username = argmap["username"]

        if argmap["password"] !="":

            password = argmap["password"]


        hostipaddress = argmap["hostIp"]

    logger.debug("Low Threshold:" + str(low))
    logger.debug("High Threshold:" + str(high))
    logger.debug("Server URL:" + serverUrl)
    logger.debug("Host Add" + hostipaddress)
    logger.debug("Mode:" + mode)
    logger.debug("Range:" + range)
    str = getVolumeState()
    print(str)
    sys.exit(stat)
except Exception as err:
    logger.error("Error in volume state by volume group", exc_info=True)
    print("STATUS UNKNOWN")
    sys.exit(3)

