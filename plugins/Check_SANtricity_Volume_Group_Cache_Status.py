#!/usr/bin/python
# Copyright 2015 NetApp Inc.  All rights reserved.
import sys
import csv
import logging

import SANtricityStorage
from logging.handlers import RotatingFileHandler


serverUrl = "https://10.0.1.30:8443"
mode = ""
listMode = {"PRC": "", "SSDC": ""}
urlToServer = serverUrl + "/devmgr/v2"
loginUrl = serverUrl + "/devmgr/utils"


logging.basicConfig(format='%(asctime)s - %(name)s : %(message)s', filename='/tmp/nagios-python.log', level=logging.DEBUG)
handler = RotatingFileHandler('/tmp/nagios-python.log', maxBytes=SANtricityStorage.maxbytes,
                                  backupCount=20)

stat = 0
hostipaddress = ""
logger = logging.getLogger("VOLUMEGRPCACHSTATE")
logger.setLevel(logging.INFO)
logger.addHandler(handler)
username="rw"
password="rw"

'''
    To fetch cache statistics for a particular volume.
'''
def getVolumeInfo(arrayId, controllerIds, sessionId, arrayInfo, controllername, controllerdetails):
    try:
        logger.info("In Volume INFO")

        filedata = SANtricityStorage.get_data_from_REST(urlToServer, sessionId, arrayId, "analysed-volume-statistics")
        if filedata:
            lstOfArraySys = filedata
            logger.debug("Response received")
            logger.debug(len(lstOfArraySys))

            dirData = {}
            arryIdWiseInfo = arrayInfo[arrayId]
            volumegroupname = arryIdWiseInfo["volumeGroup"]


            showoutput = False
            readHitPer = 0

            for lst in lstOfArraySys:
                controllerid = lst["controllerId"]
                volumegroupid = lst["poolId"]

                if volumegroupid + "~" + controllerid in dirData:
                    map = dirData[lst["poolId"] + "~" + controllerid]
                    readIOP = map["readIOP"]
                    readcacheuti = map["readCacheUtilization"]
                    readHitOp = map["readHitOp"]
                    writecacheuti = map["writeCacheUtilization"]
                    writeHitOp = map["writeHitOp"]
                    writeHitBytes = map["writeHitBytes"]
                    readHitBytes = map["readHitBytes"]
                    noofreadcachhit = map["noofreadcachehit"]
                    noofwritecachehit = map["noofwritecachehit"]
                else:
                    readIOP = 0
                    writeIOP = 0
                    readHitOp = 0
                    writeHitOp = 0
                    readHitBytes = 0
                    writeHitBytes = 0
                    noofreadcachhit = 0
                    noofwritecachehit = 0
                    writecacheuti=0
                    readcacheuti=0


                if mode == "PRC":
                    readHitOp += lst["readHitOps"]
                    readIOP += lst["readIOps"]
                    readHitBytes += round(lst["readHitBytes"] / (1024 * 1024), 2)

                    writeIOP += lst["writeIOps"]
                    writeHitOp += lst["writeHitOps"]

                    if lst["readCacheUtilization"] > 0:
                        noofreadcachhit += 1
                        readcacheuti += round(lst["readCacheUtilization"], 2)

                    if lst["writeCacheUtilization"] > 0:
                        noofwritecachehit += 1
                        writecacheuti += round(lst["writeCacheUtilization"], 2)

                    writeHitBytes += round(lst["writeHitBytes"] / (1024 * 1024), 2)
                    logger.debug(
                        "Volume Id:" + lst["volumeId"] + ",controllerId:" + lst["controllerId"] + ",poolId:" + lst[
                            "poolId"] + ",readHitOp:" + str(readHitOp) + "readHitBytes:" + str(
                            readHitBytes) + "readIops:" + str(readIOP) + "readCacheHit:" + str(readcacheuti))
                    logger.debug(
                        "writeHitOp:" + str(writeHitOp) + ",writeHitBytes:" + str(writeHitBytes) + ",writeIops:" + str(
                            writeIOP) + ",writeCacheUti:" + str(writecacheuti))




                elif mode == "SSDC":
                    readHitOp += round(lst["flashCacheReadHitOps"], 2)

                    if lst["readCacheUtilization"] >0:
                        readcacheuti +=round(lst["readCacheUtilization"],2)
                        noofreadcachhit +=1
                    readHitBytes += round(lst["flashCacheReadHitBytes"] / (1024 * 1024), 2)
                    readIOP += round(lst["readIOps"], 2)
                    logger.debug(
                        "Volume Id:" + lst["volumeId"] + ",controllerId:" + lst["controllerId"] + ",poolId:" + lst[
                            "poolId"] + ",flashCacheReadHitOPs:" + str(
                            readHitOp) + ",flashCacheReadHitBytes:" + str(readHitBytes) + ",readIops:" + str(
                            readIOP) + ",readCacheUti:" + str(readcacheuti))
                    if lst["readCacheUtilization"] > 0:
                        noofreadcachhit += 1
                        readcacheuti += round(lst["readCacheUtilization"], 2)

                dirData[lst["poolId"] + "~" + controllerid] = {"arrayId": arrayId, "controllerId": controllerid,
                                                                      "volumeGroupId": volumegroupid,
                                                                      "readIOP": readIOP, "writeIOP": writeIOP,
                                                                      "readCacheUtilization": readcacheuti,
                                                                      "writeCacheUtilization": writecacheuti,
                                                                      "readHitOp": readHitOp, "writeHitOp": writeHitOp,
                                                                      "readHitBytes": readHitBytes,
                                                                      "writeHitBytes": writeHitBytes,
                                                                      "noofreadcachehit":noofreadcachhit,
                                                                      "noofwritecachehit":noofwritecachehit}

            strOutPut = "\nArray Name : " + arrayInfo[arrayId]["arrayName"]

            if mode == "PRC":
                strOutPut += "\nPrimary Cache Statistics"
            elif mode == "SSDC":
                strOutPut += "\nFlash Cache Statistics"

            strPerData = ""

            for lstContId in dirData.keys():
                mapdata = dirData[lstContId]
                if mapdata["arrayId"] + "~" + mapdata["controllerId"] not in controllerdetails:
                    strOutPut += "\n\nController Name : " + controllerdetails[mapdata["controllerId"]]
                    controllerdetails[mapdata["arrayId"] + "~" + mapdata["controllerId"]] = 1

                strOutPut += "\n\nVolume Group Name:" + volumegroupname[mapdata["volumeGroupId"]]
                if mode == "PRC":

                    readHitOp = mapdata["readHitOp"]
                    readcacheuti = mapdata["readCacheUtilization"]
                    readHitBytes = mapdata["readHitBytes"]
                    writecacheuti = mapdata["writeCacheUtilization"]
                    writeHitOp = mapdata["writeHitOp"]
                    writeHitBytes = mapdata["writeHitBytes"]
                    noofreadcachhit=mapdata["noofreadcachehit"]
                    noofwritecachehit = mapdata["noofwritecachehit"]

                    totalCacheHit = readHitOp + writeHitOp
                    totalCacheByte = readHitBytes + writeHitBytes
                    if noofwritecachehit >0:
                        writecacheuti=writecacheuti / noofwritecachehit

                    if noofreadcachhit >0:
                        readcacheuti = readcacheuti / noofreadcachhit

                    toatlCacheHitPer = 0
                    if readcacheuti > 0 and writecacheuti > 0:
                        toatlCacheHitPer = round((readcacheuti + writecacheuti) / 2, 2)
                    elif readcacheuti > 0 and writecacheuti == 0:
                        toatlCacheHitPer = readcacheuti
                    elif readcacheuti == 0 and writecacheuti > 0:
                        toatlCacheHitPer = writecacheuti

                    strOutPut += "\nNo of Read I/O that hit cache : " + str(readHitOp) + \
                                 ", No of bytes of Read I/O that hit I/O : " + str(readHitBytes) + \
                                 "MB, % of Read I/O that hit cache : " + str(readcacheuti)
                    strOutPut += "\nNo of Write I/O that hit cache : " + str(writeHitOp) + \
                                 ", No of bytes of Write I/O that hit cache : " + str(writeHitBytes) + \
                                 "MB, % of Write I/O that hit cache : " + str(writecacheuti)

                    strOutPut += "\nNo of Read/Write I/O that hit cache : " + str(totalCacheHit) + \
                                 ", No of bytes of Read/Write Hit I/O that hit cache : " + str(totalCacheByte) \
                                 + "MB, % of Read/Write I/O that hit cache :" + str(toatlCacheHitPer)
                    strPerData += volumegroupname[mapdata["volumeGroupId"]] + "=" + str(toatlCacheHitPer) + "%; "

                elif mode == "SSDC":
                    readHitBytes = mapdata["readHitBytes"]
                    readHitOp = mapdata["readHitOp"]
                    readcacheuti = mapdata["readCacheUtilization"]
                    noofreadcachhit = mapdata["noofreadcachehit"]
                    if noofreadcachhit >0:
                        readcacheuti = round(readcacheuti / noofreadcachhit,2)
                    strOutPut += "\n No of Read I/O that hit SSD cache : " + str(readHitOp) + \
                                 ", No of bytes of Read I/O that hit cache :" + str(readHitBytes) + \
                                 ", % of Read I/O that hit cache :" + str(readcacheuti)
                    strPerData += volumegroupname[mapdata["volumeGroupId"]] + "=" + str(readHitPer) + "%; "

            dirData["strOutPut"] = strOutPut
            dirData["strPerData"] = strPerData

            return dirData
        else:
            print "STATUS UNKNOWN"
            sys.exit(3)

    except Exception, err:
        logger.error("Error in getvolumeinfo", exc_info=True)
        print "STATUS UNKNOWN"
        sys.exit(3)


'''
    Read the CSV files to get the volume details. Then use it for fetching cache statistics.
'''
def getVolumeState():
    global stat
    sessionid = SANtricityStorage.login(loginUrl,username,password)
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
                controllername[row[headerList.index("arrayId")] + "~" + row[headerList.index("controllerRef")]] = \
                    "\nArray Name:" + row[headerList.index("arrayName")] + ",Controller Name:" + \
                       row[headerList.index("controllerLabel")] + "\n"
                controllerdetails[row[headerList.index("controllerRef")]] = row[headerList.index("controllerLabel")]
    if len(controllername) == 0:
        strResult = "Unknown - Host ip address not configured in web proxy."
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

        if stat == 0:
            strResult = "OK - Volume Group cache statistics fetched.|" + firstPerData + "\n" + strResultData + "|" + strResultPerData
        elif stat == 1:
            strResult = "Warning - Some volume  are functioning at threshold values.|" + firstPerData + "\n" + strResultData + "|" + strResultPerData
        elif stat == 2:
            strResult = "Critical - Some volume  are out side threshold values.|" + firstPerData + "\n" + strResultData + "|" + strResultPerData
    else:
        strResult = "Unknown -  Host ip address not configured in web proxy."

        stat = 3
    fileForRead.close()
    return strResult


try:
    logger.debug("STarting execution of Volume Status")
    if len(sys.argv) < 7:
        print "STATUS UNKNOWN - Required parameters not set"
        sys.exit(3)
    else:
        nextelearg = False
        argmap = {"mode": "", "hostIp": "", "proxyUrl": "","username":"","password":""}
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

            elif element == "-h":
                nextelearg = True
                argname = "hostIp"
            elif element == "-webproxy":
                nextelearg = True
                argname = "proxyUrl"
            elif element =="-username":
                nextelearg=True
                argname="username"
            elif element =="-password":
                nextelearg=True
                argname="password"
            elif element == "-debug":
                logger = logging.getLogger("VOLUMESTATE")
                logger.setLevel(logging.DEBUG)
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
            print "STATUS UNKNOWN-Incorrect value for mode"
            sys.exit(3)



        if argmap["hostIp"] != '127.0.0.1':
            hostipaddress = argmap["hostIp"]

        if argmap["username"] !="":

            username = argmap["username"]
        if argmap["password"] !="":

            password = argmap["password"]
    logger.debug("Server URL:" + serverUrl)
    logger.debug("Host Add" + hostipaddress)
    logger.debug("Mode:" + mode)
    str = getVolumeState()
    print str
    sys.exit(stat)
except Exception, err:
    logging.error("Error in Volume Status", exc_info=True)
    print "STATUS UNKNOWN"
    sys.exit(3)

