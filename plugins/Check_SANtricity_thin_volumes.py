#!/usr/bin/python
# Copyright 2015 NetApp Inc.  All rights reserved.
import sys
import csv
import logging

import SANtricityStorage
from logging.handlers import RotatingFileHandler


serverUrl = 'https://10.0.1.30:8443'
critical = "95.0"
warning = "75.0"
urlToServer = serverUrl + "/devmgr/v2"
loginUrl = serverUrl + "/devmgr/utils"
stat = 0
noofoutput = -1
dirdiskdata = {}
hostipaddress = ""
logging.basicConfig(format='%(asctime)s - %(name)s : %(message)s', filename='/tmp/nagios-python.log', level=logging.DEBUG)
handler = RotatingFileHandler('/tmp/nagios-python.log', maxBytes=SANtricityStorage.maxbytes,
                                  backupCount=20)
logger = logging.getLogger("STORAGEPOOL")
logger.setLevel(logging.INFO)
logger.addHandler(handler)
username="rw"
password="rw"
'''
    This method fetches thin-volumes statistics for a particular array.
'''


def getStoragePoolInfo(eleMap, sessionid):
    try:
        global stat
        logging.info("In StoragePool INFO")
        arrayid = eleMap["arrayId"]
        arrayname = eleMap["arrayName"]
        lstofarraysys = SANtricityStorage.get_data_from_REST(urlToServer, sessionid, arrayid, "thin-volumes")

        logging.info(len(lstofarraysys))
        strdata = ""
        strrepdata = ""

        if len(lstofarraysys) >0:
            for lst in lstofarraysys:
                if lst["capacity"]:
                    capacity = round(float(lst["capacity"]) / (1024 * 1024 * 1024), 2)
                    inpprovcap = round(float(lst["initialProvisionedCapacity"]) / (1024 * 1024 * 1024), 2)
                    currprovcap = round(float(lst["currentProvisionedCapacity"]) / (1024 * 1024 * 1024), 2)
                    freespace = capacity - inpprovcap
                    totalspace = round(float(lst["totalSizeInBytes"]) / (1024 * 1024 * 1024), 2)
                    calwarning = round((float(warning) * totalspace / 100), 2)
                    calcritical = round((float(critical) * totalspace / 100), 2)
                    usedpercentage = round(((freespace * 100) / totalspace), 2)
                    reqcapacity = capacity - currprovcap

                    poolname = lst["label"]

                    if freespace <= calwarning and freespace > calcritical and stat < 1:
                        stat = 1
                    elif freespace <= calcritical:
                        stat = 2

                    logger.debug(
                        "Pool Id : " + lst["id"] + " Label : " + poolname + ", Full thin prov. volume allocation : " + str(
                            capacity) + "GB, Actual thin prov. capacity : " + str(
                            inpprovcap) + "GB, Actual capacity consumed : " + str(
                            currprovcap) + "GB, Free space available : " + str(
                            currprovcap) + "GB, Capacity req to satisfy full demand allocation : " + str(reqcapacity))
                    if hostipaddress:
                        strrepdata = "\nLabel : " + poolname + ", Full thin prov. volume allocation : " + str(
                            capacity) + "GB, Actual thin prov. volume allocation : " + str(
                            inpprovcap) + "GB, Actual capacity consumed : " + str(
                            currprovcap) + "GB, Free space available : " + str(
                            freespace) + "GB, Capacity req to satisfy full demand allocation : " + str(reqcapacity)
                    else:
                        strrepdata = "\nArray Name : " + arrayname + ", Label : " + poolname + ", Full thin prov. volume allocation : " + str(
                            capacity) + "GB, Actual thin prov. volume allocation : " + str(
                            inpprovcap) + "GB, Actual capacity consumed : " + str(
                            currprovcap) + "GB, Free space available : " + str(
                            freespace) + "GB, Capacity req to satisfy full demand allocation : " + str(reqcapacity)

                    reslistdata = {"strData": poolname + "=" + str(freespace) + "GB;"
                                              + str(calwarning) + ";" + str(calcritical) + ";0;" + str(totalspace) + " ",
                                   "strRepData": strrepdata}

                    if dirdiskdata.get(usedpercentage):
                        listFromDir = dirdiskdata.get(usedpercentage)
                        listFromDir.append(reslistdata)
                        dirdiskdata[usedpercentage] = listFromDir
                    else:
                        dirdiskdata[usedpercentage] = [reslistdata]
        else:
            strrepdata="No thin volumes found"
            stat=3
        return {"strPerfData": strdata, "reportData": strrepdata}

    except Exception, err:
        logger.error("Error in Storage pool", exc_info=True)
        print "STATUS UNKNOWN - Error in storage pool"
        sys.exit(3)


'''
    To read array information from the csv file and use it to fetch thin volume stats.
'''


def getStoragePoolInformation():
    global stat
    sessionid = SANtricityStorage.login(loginUrl,username,password)
    SANtricityStorage.getStorageSystemDetails(urlToServer, sessionid)
    file = SANtricityStorage.getStoragePath() + "/controller.csv"
    fileforread = open(file, "rb")
    csvreader = csv.reader(fileforread, delimiter=",")
    firstline = True
    arrayinfo = {}
    strperfdata = ""
    strrepdata = ""
    contcount = 0
    currentarrayid = ""
    firstarray = True
    arrayId = ""
    for row in csvreader:
        if firstline:
            headerList = row
            firstline = False
        else:
            if hostipaddress and (
                    row[headerList.index("ip1")] == hostipaddress or row[headerList.index("ip2")] == hostipaddress):
                arrayId = row[headerList.index("arrayId")]
                lstEle = {"arrayName": row[headerList.index("arrayName")], "arrayId": arrayId}
                contcount += 1
                if contcount == 2:
                    break
            elif hostipaddress == "":
                arrayId = row[headerList.index("arrayId")]
                arrayinfo[arrayId] = {"arrayName": row[headerList.index("arrayName")]}
                if currentarrayid <> arrayId and firstarray == False:
                    lstEle = {"arrayName": currentarrayname, "arrayId": currentarrayid}
                    getStoragePoolInfo(lstEle, sessionid)
                else:
                    firstarray = False

                currentarrayid = arrayId
                currentarrayname = row[headerList.index("arrayName")]

    if arrayId:
        getStoragePoolInfo(lstEle, sessionid)
    else:

        stat = 3
        return "STATUS UNKNOWN - Host ip is not configured with webproxy"

    lstsorted = sorted(dirdiskdata.keys())
    size = len(lstsorted) - 1
    totalcnt = 0
    if hostipaddress != '':
        strrepdata = "\n\nArray Name:" + lstEle["arrayName"]

    while size >= 0:
        data = dirdiskdata[lstsorted[size]]
        if len(data) == 1 and (noofoutput == -1 or (noofoutput != -1 and totalcnt < noofoutput)):
            datafromdir = data[0]
            strperfdata += datafromdir["strData"]
            strrepdata += datafromdir["strRepData"]
            totalcnt += 1
        else:
            for lstitem in data:
                if noofoutput == -1 or (noofoutput != -1 and totalcnt < noofoutput):
                    strperfdata += lstitem["strData"]
                    strrepdata += lstitem["strRepData"]
                    totalcnt += 1
                else:
                    break
        size -= 1

    if stat == 0:
        stResult = "OK - All thin volumes have used space within threshold range."
    elif stat == 1:
        stResult = "Warning - Some thin volumes have free space below the warning threshold"
    elif stat == 2:
        stResult = "Critical - Some thin volumes have free space below the critical threshold"
    elif stat ==3:
        stResult = "STATUS UNKNOWN - No thin volumes configured on this host "
    if " " in strperfdata:
        strFirstPerfData = strperfdata[0:strperfdata.index(" ")]
        strperfdata = strperfdata[strperfdata.index(" ") + 1:]
        strrepdata = "\nThreshold Values -   Warning : " + str(warning) + "%,  Critical : " + str(
        critical) + "%" + strrepdata
        stResult += "|" + strFirstPerfData + strrepdata + "|" + strperfdata
    else:
        strFirstPerfData=""



    logging.info("dataa=" + stResult)
    return stResult


try:
    if len(sys.argv) < 7:
        print "STATUS UNKNOWN - Required parameters not set"
        sys.exit(3)
    else:
        nextelearg = False
        argmap = {"hostIp": "", "proxyUrl": "", "warning": "", "critical": "","username":"","password":""}
        argname = ""
        for element in sys.argv:
            if element.endswith(".py"):
                continue
            elif nextelearg:
                if element != "":
                    argmap[argname] = element
                    nextelearg = False
                else:
                    print "STATUS UNKNOWN - Incorrect value passed for" + argname

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
            elif element =="-username":
                    nextelearg=True
                    argname="username"
            elif element =="-password":
                    nextelearg=True
                    argname="password"
            elif element == "-debug":
                logger = logging.getLogger("VOLUMESTATBYCONT")
                logger.addHandler(handler)
                logger.setLevel(logging.DEBUG)
            else:
                print "Invalid arguments passed"
                sys.exit(3)


        serverUrl = "https://" + argmap["proxyUrl"];

        urlToServer = serverUrl + "/devmgr/v2"

        loginUrl = serverUrl + "/devmgr/utils"



        try:
            warning = float(argmap["warning"])
        except Exception, err:
            print "STATUS UNKNOWN - Warning threshold must be numeric"
            sys.exit(3)



        try:
            critical = float(argmap["critical"])
            if critical < 5:
                print "STATUS UNKNOWN - Critical threshold must be greater than 5"
                sys.exit(3)
        except Exception, err:
            print "STATUS UNKNOWN - Critical threshold must be numeric"
            sys.exit(3)

        if warning <= critical:
            print 'STATUS UNKNOWN - Incorrect value for warning and critical threshold'
            sys.exit(3)

        if argmap["username"] !="":

            username = argmap["username"]

        if argmap["password"] !="":

            password = argmap["password"]



        hostipaddress = argmap["hostIp"]

    logger.debug("Low Threshold:" + str(warning))
    logger.debug("High Threshold:" + str(critical))
    logger.debug("Server URL:" + serverUrl)
    logger.debug("Host Add" + hostipaddress)

    str = getStoragePoolInformation()
    print str
    sys.exit(stat)
except Exception, err:
    print "STATUS UNKNOWN"
    logger.error("Error in Storage Pool Status", exc_info=True)
    sys.exit(3)



