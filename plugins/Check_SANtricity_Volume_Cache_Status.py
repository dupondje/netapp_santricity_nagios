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
logger = logging.getLogger("VOLUMECACHSTATE")
logger.setLevel(logging.INFO)
logger.addHandler(handler)
username="rw"
password="rw"
'''
    To fetch volume wise cache statistics using REST endpoint /analysed-volume-statistics
'''

def getVolumeInfo(arrayId, controllerIds, sessionId, arrayInfo, controllername, controllerdetails):
    try:
        logger.info("In Volume INFO")

        filedata = SANtricityStorage.get_data_from_REST(urlToServer, sessionId, arrayId, "analysed-volume-statistics")
        if filedata:
            lstofarraysys = filedata
            lst = []
            logger.debug("Response received")

            logger.debug(len(lstofarraysys))

            dirData = {}

            arryIdWiseInfo = arrayInfo[arrayId]
            arrayname=arryIdWiseInfo["arrayName"]
            volumegroupname = arryIdWiseInfo["volumeGroup"]

            strPerData = ""
            showoutput = False

            for lst in lstofarraysys:

                controllerid = lst["controllerId"]
                cntContWise = 0
                if lst["poolId"] +"~"+controllerid in dirData:
                     stroutput=(dirData[lst["poolId"] +"~"+controllerid])["strOutput"]
                else:
                    stroutput = "\nVolume Group Name:"+volumegroupname[lst["poolId"]]


                stroutput += "\n\nVolume Name:" + lst["volumeName"]
                if mode == "PRC":
                    readHitOp = round(lst["readHitOps"], 2)
                    readIOP = round(lst["readIOps"], 2)
                    readcacheuti = round(lst["readCacheUtilization"], 2)
                    writecacheuti = round(lst["writeCacheUtilization"], 2)
                    readHitBytes = round(lst["readHitBytes"] / (1024 * 1024), 2)

                    writeIOP = round(lst["writeIOps"], 2)
                    writeHitOp = round(lst["writeHitOps"], 2)

                    writeHitBytes = round(lst["writeHitBytes"] / (1024 * 1024), 2)
                    logger.debug(
                        "Volume Id:" + lst["volumeId"] + ",controllerId:" + lst["controllerId"] + ",poolId:" + lst[
                            "poolId"] + ",readHitOp:" + str(readHitOp) + "readHitBytes:" + str(
                            readHitBytes) + "readIops:" + str(readIOP) + "readCacheUtilization:" + str(readcacheuti))
                    logger.debug(
                        "writeHitOp:" + str(writeHitOp) + ",writeHitBytes:" + str(writeHitBytes) + ",writeIops:" + str(
                            writeIOP) + ",writeCacheUtilization:" + str(writecacheuti))

                    totalCacheHit = readHitOp + writeHitOp
                    totalCacheHitPer = 0
                    if readcacheuti > 0 and writecacheuti > 0:
                        totalCacheHitPer = round((readcacheuti + writecacheuti) / 2, 2)
                    elif readcacheuti > 0 and writecacheuti == 0:
                        totalCacheHitPer =readcacheuti
                    elif writecacheuti >0 and readcacheuti ==0:
                        totalCacheHitPer = writecacheuti

                    totalCacheByte = readHitBytes + writeHitBytes
                    totatlCachBytePer = 0

                    stroutput += "\nNo of Read I/O that hit cache : " + str(
                        readHitOp) + ", No of bytes of Read I/O that hit I/O : " + str(
                        readHitBytes) + "MB, % of Read I/O that hit cache : " + str(readcacheuti)
                    stroutput += "\nNo of Write I/O that hit cache : " + str(
                        writeHitOp) + ", No of bytes of Write I/O that hit cache : " + str(
                        writeHitBytes) + "MB, % of Write I/O that hit cache : " + str(writecacheuti)
                    stroutput += "\nNo of Read/Write I/O that hit cache : " + str(
                        totalCacheHit) + ", No of bytes of Read/Write Hit I/O that hit cache : " + str(
                        totalCacheByte) + "MB, % of Read/Write I/O that hit cache :" + str(totalCacheHitPer)
                    strPerData += lst["volumeName"] + "=" + str(totalCacheHitPer) + "%; "

                elif mode == "SSDC":
                    readHitOp = round(lst["flashCacheReadHitOps"], 2)
                    readcacheuti = round(lst["readCacheUtilization"], 2)
                    readHitBytes = round(lst["flashCacheReadHitBytes"], 2)
                    readIOP = round(lst["readIOps"], 2)
                    # logger.debug("Volume Id:"+lst["volumeId"]+",controllerId:"+lst["controllerId"]+",poolId:"+lst["poolId"]+",flashCacheReadHitOPs:"+str(readHitOp) +",flashCacheReadHitBytes:"+str(readHitBytes) +",readIops:"+readIOP+",readBytes:"+readBytes)
                    logger.debug(
                        "Volume Id:" + lst["volumeId"] + ",controllerId:" + lst["controllerId"] + ",poolId:" + lst[
                            "poolId"] + ",flashCacheReadHitOPs:" + str(
                            readHitOp) + ",flashCacheReadHitBytes:" + str(readHitBytes) + ",readIops:" + str(
                            readIOP) + ",readCacheHit:" + str(readcacheuti))

                    stroutput += "\n No of Read I/O that hit SSD cache : " + str(
                        readHitOp) +", No of bytes of Read I/O that hit cache :" + str(
                        readHitBytes) + ", % of Read I/O that hit cache :" + str(readcacheuti)
                    strPerData += lst["volumeName"] + "=" + str(readcacheuti) + "%; "

                dirData[lst["poolId"] + "~" + controllerid] = {"strOutput": stroutput, "arrayId": arrayId,
                                                                      "controllerId": controllerid}
            stroutput ="Array Name : "+arrayname
            if mode == "PRC":
                stroutput = "\n\nPrimary Cache Statistics"
            elif mode == "SSDC":
                stroutput = "\n\nFlash Cache Statistics"


            for lstContId in dirData.keys():
                mapdata = dirData[lstContId]
                if mapdata["arrayId"] + "~" + mapdata["controllerId"] not in controllerdetails:
                    stroutput += "\n\nController Name : " + controllerdetails[mapdata["controllerId"]]
                    controllerdetails[mapdata["arrayId"] + "~" + mapdata["controllerId"]] = 1
                stroutput += mapdata["strOutput"]

            dirData["strOutPut"] = stroutput
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
    To read controller.csv file for fetching details of array information. Then use this to fetch volume wise cache
    stats.
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
                controllername[row[headerList.index("arrayId")] + "~" + row[headerList.index("controllerRef")]] = "\nArray Name:" + \
                    row[headerList.index("arrayName")] + ",Controller Name:" + row[headerList.index("controllerLabel")] + "\n"
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
        strResultData = "Array Name : " + arrayInfo[arrayId]["arrayName"] + strResultData
        if stat == 0:
            strResult = "OK - Volume cache statistics fetched.|" + firstPerData + "\n" + strResultData + "|" + strResultPerData
        elif stat == 1:
            strResult = "Warning- Some volume  are functioning at threshold values.|" + firstPerData + "\n" + strResultData + "|" + strResultPerData
        elif stat == 2:
            strResult = "Critical- Some volume  are out side threshold values.|" + firstPerData + "\n" + strResultData + "|" + strResultPerData
    else:
        strResult = "Unknown -  Host ip address not configured in web proxy."

        stat = 3
    fileForRead.close()
    return strResult

'''
Main method
Checks if all required arguments are passed or not.
'''
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

                # logging.basicConfig(format='%(asctime)s - %(name)s : %(message)s',filename='/tmp/nagios-python.log',level=logging.DEBUG)
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



        if argmap["username"] !="":

            username = argmap["username"]

        if argmap["password"] !="":

            password = argmap["password"]


        if argmap["hostIp"] != '127.0.0.1':
            hostipaddress = argmap["hostIp"]

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

