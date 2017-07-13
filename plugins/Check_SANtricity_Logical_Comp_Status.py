#!/usr/bin/python
# Copyright 2015 NetApp Inc.  All rights reserved.
__author__ = 'hardikJsheth'
import sys
import csv
import datetime
import logging

import SANtricityStorage
from logging.handlers import RotatingFileHandler

mode = ""
hostipaddress = ""
webproxy = ""
stat = 0
listmode = ["VOL", "DPOOL", "MIRV", "SNP", "RPR", "CON", "ALL"]
msglist = {"VOL": "Volumes", "": "Logical Components", "DPOOL": "Storage Pools", "MIRV": "Mirror Volumes",
           "CON": "Consistency Groups", "SNP": "Snapshot Volumes", "RPR": "Repositories", "MIRR": "Mirror Repository"}
logging.basicConfig(format='%(asctime)s - %(name)s : %(message)s', filename='nagios-python.log', level=logging.DEBUG)
handler = RotatingFileHandler('nagios-python.log', maxBytes=SANtricityStorage.maxbytes,
                                  backupCount=20)
logger = logging.getLogger("LOGICALCOMPSTAT")
logger.setLevel(logging.INFO)
logger.addHandler(handler)
username="rw"
password="rw"

'''
    Method to get Logical Component information for specific array from REST end point /graph
'''


def get_logical_comp_stat_by_array(arrayid, sessionid, arrinfo, controllername):
    strOutPut = "\nArray Name : " + arrinfo[arrayid]["arrayName"]

    if stat == 2:
        print "Critical - Array is down, no other status can be fetched"
        sys.exit(2)

    resultdata = {}
    strPerfData = ""

    if mode == "":
        resultdata = get_storage_pool_status(arrayid, sessionid, arrinfo, controllername)
        strOutPut += resultdata["strOutPut"]
        strPerfData += resultdata["strPerfData"]

        resultdata = get_con_group_status(arrayid, sessionid, arrinfo, controllername)
        strOutPut += resultdata["strOutPut"]
        strPerfData += resultdata["strPerfData"]

        resultdata = get_volume_status(arrayid, sessionid, arrinfo, controllername)
        strOutPut += resultdata["strOutPut"]
        strPerfData += resultdata["strPerfData"]

        resultdata = get_legacy_snap_status(arrayid, sessionid, arrinfo, controllername)
        strOutPut += resultdata["strOutPut"]
        strPerfData += resultdata["strPerfData"]

        resultdata = get_pit_snap_status(arrayid, sessionid, arrinfo, controllername)
        strOutPut += resultdata["strOutPut"]
        strPerfData += resultdata["strPerfData"]

        resultdata = get_mirror_vol_status(arrayid, sessionid, arrinfo, controllername)
        strOutPut += resultdata["strOutPut"]
        strPerfData += resultdata["strPerfData"]

        resultdata = get_asynch_mirror_status(arrayid, sessionid, arrinfo, controllername)
        strOutPut += resultdata["strOutPut"]
        strPerfData += resultdata["strPerfData"]

        resultdata = get_pit_repo_status(arrayid, sessionid, arrinfo, controllername)
        strOutPut += resultdata["strOutPut"]
        strPerfData += resultdata["strPerfData"]

        '''
        resultdata = get_mirr_repo_status(arrayid,sessionid,arrinfo,controllername)
        strOutPut += resultdata["strOutPut"]
        strPerfData += resultdata["strPerfData"]
        '''
    elif mode == "DPOOL":
        resultdata = get_storage_pool_status(arrayid, sessionid, arrinfo, controllername)
        strOutPut += resultdata["strOutPut"]
        strPerfData += resultdata["strPerfData"]
    elif mode == "VOL":
        resultdata = get_volume_status(arrayid, sessionid, arrinfo, controllername)
        strOutPut += resultdata["strOutPut"]
        strPerfData += resultdata["strPerfData"]

    elif mode == "STPOOL":
        resultdata = get_storage_pool_status(arrayid, sessionid, arrinfo, controllername)
        strOutPut += resultdata["strOutPut"]
        strPerfData += resultdata["strPerfData"]

    elif mode == "MIRV":
        resultdata = get_mirror_vol_status(arrayid, sessionid, arrinfo, controllername)
        strOutPut += resultdata["strOutPut"]
        strPerfData += resultdata["strPerfData"]
        resultdata = get_asynch_mirror_status(arrayid, sessionid, arrinfo, controllername)
        strOutPut += resultdata["strOutPut"]
        strPerfData += resultdata["strPerfData"]

    elif mode == "SNP":
        resultdata = get_legacy_snap_status(arrayid, sessionid, arrinfo, controllername)
        strOutPut += resultdata["strOutPut"]
        strPerfData += resultdata["strPerfData"]
        resultdata = get_pit_snap_status(arrayid, sessionid, arrinfo, controllername)
        strOutPut += resultdata["strOutPut"]
        strPerfData += resultdata["strPerfData"]

    elif mode == "RPR":

        resultdata = get_pit_repo_status(arrayid, sessionid, arrinfo, controllername)
        strOutPut += resultdata["strOutPut"]
        strPerfData += resultdata["strPerfData"]

        '''resultdata = get_mirr_repo_status(arrayid,sessionid,arrinfo,controllername)
        strOutPut += resultdata["strOutPut"]
        strPerfData += resultdata["strPerfData"]'''

    elif mode == "CON":
        resultdata = get_con_group_status(arrayid, sessionid, arrinfo, controllername)
        strOutPut += resultdata["strOutPut"]
        strPerfData += resultdata["strPerfData"]

    resultdata["strOutPut"] = strOutPut
    resultdata["strPerfData"] = strPerfData
    return resultdata


'''
    To get volume status
'''


def get_volume_status(arrayid, sessionid, arrinfo, controllername):
    global stat
    lstdata = SANtricityStorage.get_data_from_REST(urlToServer, sessionid, arrayid, "volumes")
    strresultdata = "\n\nVolume Status"
    strperfdata = ""

    if len(lstdata) >0:
        for item in lstdata:
            totalSize = round(float(item["totalSizeInBytes"]) / (1024 * 1024 * 1024), 2)
            strresultdata += "\nVolume Label : " + item["label"] + ", Disk Pool : " + str(
                item["diskPool"]) + ", Total Size : " + str(totalSize) + "GB, Volume Use : " + item[
                                 "volumeUse"] + ", Status : " + item["status"]
            if item["status"] != "optimal" and stat <2:

                stat = 2
                optimal = 0
            else:
                optimal = 1
            strperfdata += "Volume-Label:" + item["label"] + "=" + str(optimal) + ";;0;1; "
    else:
        stat =3
        strresultdata +="No Volumes found"
    return {"strOutPut": strresultdata, "strPerfData": strperfdata}


'''
    To get consistency group details
'''


def get_con_group_status(arrayid, sessionid, arrinfo, controllername):
    global stat
    lstdata = SANtricityStorage.get_data_from_REST(urlToServer, sessionid, arrayid, "consistency-groups")
    strresultdata = "\n\nConsistency Group Status"
    strperfdata = ""

    if len(lstdata):
        for item in lstdata:

            strresultdata += "\nLabel : " + item["label"] + ", Repository Full Policy : " + item[
                "repFullPolicy"] + ", Warning Threshold : " + str(
                item["fullWarnThreshold"]) + ", Auto Delete Limit : " + str(
                item["autoDeleteLimit"]) + ", Creation Pending Status : " + item["creationPendingStatus"]
            if item["creationPendingStatus"] != "none" and stat <2:

                stat = 2
                optimal = 0
            else:
                optimal = 1
            strperfdata += "Volume-Label:" + item["label"] + "=" + str(optimal) + ";;0;1; "
    else:
        stat =3
        strresultdata += "\nNo Consistency group found."
    return {"strOutPut": strresultdata, "strPerfData": strperfdata}


'''
    To get storage pool status
'''


def get_storage_pool_status(arrayid, sessionid, arrinfo, controllername):
    global stat
    lstdata = SANtricityStorage.get_data_from_REST(urlToServer, sessionid, arrayid, "storage-pools")
    strresultdata = "\n\nData Pool Status"
    strperfdata = ""

    if len(lstdata) >0:
        for item in lstdata:
            totalsize = round(float(item["totalRaidedSpace"]) / (1024 * 1024 * 1024), 2)
            freespace = round(float(item["freeSpace"]) / (1024 * 1024 * 1024), 2)
            usedspace = round(round(float(item["usedSpace"]) / (1024 * 1024 * 1024), 2))
            if item["diskPool"]:
                type = "Disk Pool"
            else:
                type = "Volume Group"
            strresultdata += "\nLabel : " + item["label"] + ", Type : " + type + ", Total Space : " + str(
                totalsize) + "GB, Used Space : " + str(usedspace) + "GB, Free Space :" + str(freespace) + "GB, Status : " + \
                             item["raidStatus"]
            if item["raidStatus"] != "optimal" and stat <2:

                stat = 2
                optimal = 0
            else:
                optimal = 1
            strperfdata += "Pool:" + item["label"] + "=" + str(optimal) + ";;0;1; "
    else:
        stat =3
        strresultdata +="No Storage Pool found."
    return {"strOutPut": strresultdata, "strPerfData": strperfdata}


'''
    To get Mirror repository details
'''


def get_mirror_vol_status(arrayid, sessionid, arrinfo, controllername):
    global stat
    lstdata = SANtricityStorage.get_data_from_REST(urlToServer, sessionid, arrayid, "remote-mirror-pairs")
    strresultdata = "\n\nMirror Volume Status\nMirror Repository Volumes Status"
    strperfdata = ""

    if len(lstdata) > 0:
        for item in lstdata:
            totalsize = round(float(item["base"]["capacity"]) / (1024 * 1024 * 1024), 2)

            lasttime = ""
            if item["lastCompleteTime"]:
                lasttime = str(datetime.datetime.fromtimestamp(int(item["lastCompleteTime"])).strftime("%m/%d/%y"))
            else:
                lasttime = "NA"
            strresultdata += "\nLabel : " + str(item["base"]["label"]) + ", Type : " + item["base"]["objectType"] + ", " \
                              "Last Start Time : " + lasttime + ", Capacity : " + str(
                totalsize) + "GB, Status : " + item["status"]
            if item["status"] != "optimal" and stat <2:

                stat = 2
                optimal = 0
            else:
                optimal = 1
            strperfdata += "Label:" + str(item["base"]["label"]) + "=" + str(optimal) + ";;0;1; "
    else:
        stat =3
        strresultdata += "\n No Mirror Repository Volumes found."

    return {"strOutPut": strresultdata, "strPerfData": strperfdata}


'''
    To get PIT repository details
'''


def get_pit_repo_status(arrayid, sessionid, arrinfo, controllername):
    global stat
    lstdata = SANtricityStorage.get_data_from_REST(urlToServer, sessionid, arrayid, "repositories/concat")
    strresultdata = "\n\nPIT Repository Status"
    strperfdata = ""
    if len(lstdata) >0:
        for item in lstdata:
            totalsize = round(float(item["aggregateCapacity"]) / (1024 * 1024 * 1024), 2)

            strresultdata += "\nVolume Handle : " + str(item["volumeHandle"]) + ", Type : " + item[
                "baseObjectType"] + ", Aggregated Capacity : " + str(totalsize) + "GB, Status : " + item["status"]
            if item["status"] != "optimal" and stat <2:

                stat = 2
                optimal = 0
            else:
                optimal = 1
            strperfdata += "Volume-Handle : " + str(item["volumeHandle"]) + "=" + str(optimal) + ";;0;1; "
    else:
        stat =3
        strresultdata +="No PIT Repository found"
    return {"strOutPut": strresultdata, "strPerfData": strperfdata}


'''
    To get Legacy snapshot details
'''


def get_legacy_snap_status(arrayid, sessionid, arrinfo, controllername):
    global stat
    lstdata = SANtricityStorage.get_data_from_REST(urlToServer, sessionid, arrayid, "legacy-snapshots")
    strresultdata = "\n\nSnapshot Volumes Status\n\nLegacy Snapshots Status"
    strperfdata = ""

    if len(lstdata) > 0:
        for item in lstdata:
            totalsize = round(float(item["totalSizeInBytes"]) / (1024 * 1024 * 1024), 2)

            strresultdata += "\nLabel : " + item["label"] + ", Type : " + item[
                "objectType"] + ", Snapshot Time : "+datetime.datetime.fromtimestamp(int(item["snapshotTime"])).strftime("%m/%d/%y")\
                             +", Total Capacity : " + str(totalsize) + "GB, Repository Full : "\
                             +str(item["repositoryFull"])+ ", Status : " + item["status"]
            if item["status"] != "active" and stat <2:

                stat = 2
                optimal = 0
            else:
                optimal = 1
            strperfdata += "Label:" + item["label"] + "=" + str(optimal) + ";;0;1; "
    else:
        stat = 3
        strresultdata += "\nNo Legacy snapshot found."
    return {"strOutPut": strresultdata, "strPerfData": strperfdata}


'''
    To get snap shot repository details
'''


def get_snap_rep_status(arrayid, sessionid, arrinfo, controllername):
    global stat
    lstdata = SANtricityStorage.get_data_from_REST(urlToServer, sessionid, arrayid, "legacy-snapshots")
    strresultdata = "\n\nRepository Status\nSnapshot Repository Status"
    strperfdata = ""

    if len(lstdata) > 0:
        for item in lstdata:
            totalsize = round(float(item["aggregateCapacity"]) / (1024 * 1024 * 1024), 2)

            strresultdata += "\nVolume Handle : " + item["volumeHandle"] + ", Type : " + item[
                "baseObjectType"] + ", Aggregated Capacity : " + str(totalsize) + "GB, Status : " + item["status"]
            if item["raidStatus"] != "optimal" and stat <2:

                stat = 2
                optimal = 0
            else:
                optimal = 1
            strperfdata += "Storage-Pool:" + item["label"] + "=" + str(optimal) + ";;0;1; "
    else:
        stat =3
        strresultdata += "\nNo Legacy Snapshot found."
    return {"strOutPut": strresultdata, "strPerfData": strperfdata}


'''
    To get PIT snapshot details
'''


def get_pit_snap_status(arrayid, sessionid, arrinfo, controllername):
    global stat
    lstdata = SANtricityStorage.get_data_from_REST(urlToServer, sessionid, arrayid, "snapshot-images")
    strresultdata = "\n\nPIT Snapshots Status"
    strperfdata = ""

    if len(lstdata) > 0:
        for item in lstdata:
            totalsize = round(float(item["pitCapacity"]) / (1024 * 1024 * 1024), 2)

            strresultdata += "\nSequence No : " + item["pitSequenceNumber"] + ", Creation Method : " + item[
                "creationMethod"] + \
                             ", Capacity : " + str(totalsize) + "GB, Utilization : " + str(
                item["repositoryCapacityUtilization"]) + \
                             ", Creation Time : " + str(
                datetime.datetime.fromtimestamp(int(item["pitTimestamp"])).strftime("%m/%d/%y")) + \
                             ", Status : " + item["status"]
            if item["status"] != "optimal" and stat <2:

                stat = 2
                optimal = 0
            else:
                optimal = 1
            strperfdata += "SeqNO:" + item["pitSequenceNumber"] + "=" + str(optimal) + ";;0;1; "
    else:
        stat =3
        strresultdata += "\nNo PIT Snapshot found."
    return {"strOutPut": strresultdata, "strPerfData": strperfdata}


'''
    To get Mirrors Volumes details
'''
'''
def get_mirr_repo_status(arrayid,sessionid, arrinfo, controllername):
    lstdata =SANtricityStorage.get_data_from_REST(urlToServer,sessionid,arrayid,"remote-mirror-pairs")
    strresultdata="\n\nMirror Volumes\n\nRemote Mirror Volumes Status"
    strperfdata=""

    if len(lstdata) >0:
        for item in lstdata:
            totalsize=round(float(item["totalSizeInBytes"])/(1024*1024*1024),2)

            strresultdata+= "\nRemote Volume Name : "+item["remoteVolumeName"] +", Last Recovery Point Time : "+str(
                    datetime.datetime.fromtimestamp(int(item["lastRecoveryPointTime"])).strftime("%m/%d/%y")) + ", " \
                    "Total Space : "+str(totalsize) +", Status : "+ item["remoteVolumeInfo"]["remoteVolState"]

            if item["remoteVolumeInfo"]["remoteVolState"] != "noLun":
                global stat
                stat = 2
                optimal = 0
            else:
                optimal = 1
            strperfdata += "Asynch-Label:" +item["remoteVolumeName"] + "=" + str(optimal) + ";;0;1; "
    else:
        strresultdata+= "\nNo Remote mirror volumes found"
    return {"strOutPut": strresultdata, "strPerfData": strperfdata}

'''
'''
    To get Asynch Mirrors status
'''


def get_asynch_mirror_status(arrayid, sessionid, arrinfo, controllername):
    global stat
    lstdata = SANtricityStorage.get_data_from_REST(urlToServer, sessionid, arrayid, "async-mirrors/pairs")
    strresultdata = "\n\nAsync Mirror Volumes Status"
    strperfdata = ""

    if len(lstdata) >0:
        for item in lstdata:
            totalsize = round(float(item["totalSizeInBytes"]) / (1024 * 1024 * 1024), 2)

            strresultdata += "\nRemote Volume Name : " + item["remoteVolumeName"] + ", Last Recovery Point Time : " + str(
                datetime.datetime.fromtimestamp(int(item["lastRecoveryPointTime"])).strftime("%m/%d/%y")) + ", " \
                                                                                                            "Total Space : " + str(
                totalsize) + "GB, Status : " + item["remoteVolumeInfo"]["remoteVolState"]

            if item["remoteVolumeInfo"]["remoteVolState"] != "optimal" and stat <2:

                stat = 2
                optimal = 0
            else:
                optimal = 1
            strperfdata += "Async-Label:" + item["remoteVolumeName"] + "=" + str(optimal) + ";;0;1; "
    else:
        stat =3
        strresultdata +="\nNo Async Mirror Volumes found"
    return {"strOutPut": strresultdata, "strPerfData": strperfdata}


'''
    To get Logica component status for a particular array. Read the controller.csv file to get the data of array.
'''


def getlogicalcomptstatus():
    global stat
    sessionid = SANtricityStorage.login(loginUrl,username,password)
    SANtricityStorage.getStorageSystemDetails(urlToServer, sessionid, SANtricityStorage.getTime())
    file = SANtricityStorage.getStoragePath() + "/controller.csv"
    fileforread = open(file, "rb")
    csvreader = csv.reader(fileforread, delimiter=",")
    firstline = True
    currentarrayid = ""
    arrayinfo = {}
    strresultdata = ""
    strresultperdata = ""
    lstresult = []
    firstarray = True
    controllername = {}
    contcount = 0
    arrayId = ""
    for row in csvreader:
        if firstline:
            headerList = row
            firstline = False
        else:
            if hostipaddress and (row[headerList.index("ip1")] == hostipaddress or row[headerList.index("ip2")] ==
                hostipaddress):
                arrayId = row[headerList.index("arrayId")]
                arrayinfo[arrayId] = {"arrayName": row[headerList.index("arrayName")]}
                controllername[row[headerList.index("controllerRef")]] = row[headerList.index("controllerLabel")]
                contcount += 1
                if contcount == 2:
                    break
            elif hostipaddress == "":

                arrayId = row[headerList.index("arrayId")]
                arrayinfo[arrayId] = {"arrayName": row[headerList.index("arrayName")]}
                if currentarrayid <> arrayId and firstarray == False:

                    lstresult.append(
                        get_logical_comp_stat_by_array(currentarrayid, sessionid, arrayinfo, controllername))
                    controllername = {}
                    controllername[row[headerList.index("controllerRef")]] = row[headerList.index("controllerLabel")]

                else:
                    firstarray = False

                currentarrayid = arrayId
    if arrayId:

        lstresult.append(get_logical_comp_stat_by_array(arrayId, sessionid, arrayinfo, controllername))
        firstPerData = ""
        firstline = True

        for listEle in lstresult:
            strresultdata += listEle["strOutPut"]
            if firstline:
                firstPerData = listEle["strPerfData"]
                strArry = firstPerData.split(" ")
                if " " in firstPerData:
                    firstspace = firstPerData.index(" ")
                    strresultperdata += firstPerData[firstspace + 1:] + " "
                    firstPerData = firstPerData[0:firstPerData.index(" ")]

                firstline = False
            else:
                strresultperdata += listEle["strPerData"]

        # strResultPerData = strResultPerData.strip()

        if stat == 0:
            strResult = "OK - All " + msglist[
                mode] + " are in optimal stat.|" + firstPerData + "\n" + strresultdata + "|" + strresultperdata
        elif stat == 1 and (mode == '' or mode == 'ARRY'):
            strResult = "Warning - Array is in need attention stat|" + firstPerData + "\n" + strresultdata + "|" + strresultperdata
        elif stat == 1 and mode != "" and mode != 'ARRY':
            strResult = "OK - All " + msglist[
                mode] + " are in optimal stat.|" + firstPerData + "\n" + strresultdata + "|" + strresultperdata
        elif stat == 2:
            strResult = "Critical - Some " + msglist[
                mode] + " are down.|" + firstPerData + "\n" + strresultdata + "|" + strresultperdata
        elif stat ==3:
            strResult = "STATUS UNKNOWN - Logical component not found" +strresultdata

    else:
        strResult = "Unknown -  Host ip address is not configured in web proxy."

        stat = 3
    fileforread.close()
    return strResult


'''
    Main method.
'''
try:
    if len(sys.argv) < 2:
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

                # logging.basicConfig(format='%(asctime)s - %(name)s : %(message)s',filename='nagios-python.log',level=logging.DEBUG)
                logger = logging.getLogger("LOGICALCOMPSTAT")
                logger.setLevel(logging.DEBUG)
                logger.addHandler(handler)
            else:
                print "Invalid arguments passed"
                sys.exit(3)


        if argmap["proxyUrl"]:
            serverUrl = "https://" + argmap["proxyUrl"];

            urlToServer = serverUrl + "/devmgr/v2"

            loginUrl = serverUrl + "/devmgr/utils"
        else:
            print "STATUS UNKNOWN- Webproxy must be set"
            sys.exit(3)



        mode = argmap["mode"];
        if mode!="" and mode !="ALL":
            try:
                index = listmode.index(mode);
            except:
                print "STATUS UNKNOWN-Incorrect value for mode"
                sys.exit(3)
        else:
            mode =""


        if argmap["hostIp"] != "127.0.0.1":
            hostipaddress = argmap["hostIp"]
        if argmap["username"] !="":

            username = argmap["username"]

        if argmap["password"] !="":

            password = argmap["password"]
    logger.debug("Host Ip:" + hostipaddress)
    logger.debug("Webproxy:" + argmap["proxyUrl"])
    logger.debug("Mode:" + argmap["mode"])

    str = getlogicalcomptstatus()
    print str
    sys.exit(stat)
except Exception, err:
    logger.error("Error inside get volume stat by controller", exc_info=True)
    print "STATUS UNKNOWN"
    sys.exit(3)
