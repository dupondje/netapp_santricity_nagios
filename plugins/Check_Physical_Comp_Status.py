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
listmode = ["RBCON", "EBIOM", "TRAY", "BATT", "FAN", "PSU", "DDS", "ARRY","ALL"]
msglist = {"BATT": "Batteries", "": "Physical Components", "RBCON": "RBOD Controllers", "EBIOM": "EBOD IOMs",
           "TRAY": "Trays ", "FAN": "Fans", "PSU": "Power Supply Units", "DDS": "Disk Drives", "ARRY": "Arrays"}
logging.basicConfig(format='%(asctime)s - %(name)s : %(message)s', filename='/tmp//tmp/nagios-python.log', level=logging.DEBUG)
handler = RotatingFileHandler('/tmp/nagios-python.log', maxBytes=SANtricityStorage.maxbytes,
                                  backupCount=20)
logger = logging.getLogger("PHYCOMPSTAT")
logger.setLevel(logging.INFO)
logger.addHandler(handler)
username ="rw"
password="rw"
'''
    Method to get Physical Component information for specific array from REST end point /graph
'''


def get_phy_comp_stat_by_array(arrayid, sessionid, arrinfo, controllername):
    data = SANtricityStorage.get_data_from_REST(urlToServer, sessionid, arrayid, "graph")
    strOutPut = "\nArray Name : " + arrinfo[arrayid]["arrayName"]
    resultdata = get_array_status(sessionid, arrayid)
    strOutPut += resultdata["strOutPut"]
    if stat == 2:
        print "Critical - Array is down, no other status can be fetched"
        sys.exit(2)

    resultdata = {}
    strPerfData = ""
    if data:
        if mode == "":
            resultdata = get_drive_status(data)
            strOutPut += resultdata["strOutPut"]
            strPerfData += resultdata["strPerfData"]
            resultdata = get_controller_status(data, arrayid, controllername)
            strOutPut += resultdata["strOutPut"]
            strPerfData += resultdata["strPerfData"]
            resultdata = get_battery_status(data)
            strOutPut += resultdata["strOutPut"]
            strPerfData += resultdata["strPerfData"]
            resultdata = get_fan_status(data)
            strOutPut += resultdata["strOutPut"]
            strPerfData += resultdata["strPerfData"]
            resultdata = get_powersupp_status(data)
            strOutPut += resultdata["strOutPut"]
            strPerfData += resultdata["strPerfData"]
            resultdata = get_esm_status(data)
            strOutPut += resultdata["strOutPut"]
            strPerfData += resultdata["strPerfData"]
            resultdata = get_tray_status(data)
            strOutPut += resultdata["strOutPut"]
            strPerfData += resultdata["strPerfData"]

        elif mode == "BATT":
            resultdata = get_battery_status(data)
            strOutPut += resultdata["strOutPut"]
            strPerfData += resultdata["strPerfData"]
        elif mode == "RBCON":
            resultdata = get_controller_status(data, arrayid, controllername)
            strOutPut += resultdata["strOutPut"]
            strPerfData += resultdata["strPerfData"]
        elif mode == "PSU":
            resultdata = get_powersupp_status(data)
            strOutPut += resultdata["strOutPut"]
            strPerfData += resultdata["strPerfData"]
        elif mode == "DDS":
            resultdata = get_drive_status(data)
            strOutPut += resultdata["strOutPut"]
            strPerfData += resultdata["strPerfData"]
        elif mode == "FAN":
            resultdata = get_fan_status(data)
            strOutPut += resultdata["strOutPut"]
            strPerfData += resultdata["strPerfData"]
        elif mode == "EBIOM":
            resultdata = get_esm_status(data)
            strOutPut += resultdata["strOutPut"]
            strPerfData += resultdata["strPerfData"]
        elif mode == "TRAY":
            resultdata = get_tray_status(data)
            strOutPut += resultdata["strOutPut"]
            strPerfData += resultdata["strPerfData"]
        resultdata["strOutPut"] = strOutPut
        resultdata["strPerfData"] = strPerfData
        return resultdata


'''
    To fetch status of particular array.
'''


def get_array_status(sessionid, arrayid):
    data = SANtricityStorage.get_data_from_REST(urlToServer, sessionid, arrayid, "")
    global stat
    if data:
        status = data["status"]
        if status == "needsAttn" and stat < 1 and (mode == "" or mode == "ARRY"):
            stat = 1
        elif status == "neverContacted":

            stat = 2

        stroutput = ", Status : " + data["status"]

    return {"strOutPut": stroutput}


'''
    To fetch drive status from the passed data
'''


def get_drive_status(data):
    global stat
    datalist = data["drive"]
    driveinfo = SANtricityStorage.read_csv_file("driverMap.csv", "diskId", "")

    stroutput = "\n\nDrive Status"
    optimal = 1
    strPerfData = ""
    total = 0
    if len(datalist) >0:
        for ele in datalist:
            if ele["status"] != "optimal" and stat <2:

                stat = 2
                optimal = 0
            else:
                optimal = 1
            stroutput += "\nDrive : " + driveinfo[ele["id"]]["driveLabel"] + ", Product Id : " + ele[
                "productID"].strip() + ", Status : " + ele["status"]
            strPerfData += "Drive:" + driveinfo[ele["id"]]["driveLabel"] + "=" + str(optimal) + ";;0;1; "
            total += 1
    else:
        stat =3
        stroutput+="No drives found in array."
    return {"strOutPut": stroutput, "strPerfData": strPerfData}


'''
    To get esm status from the passed data
'''


def get_esm_status(data):
    datalist = data["componentBundle"]["esm"]
    global stat
    stroutput = "\n\nEBOD IOMs"
    optimal = 0
    total = 0
    strPerfData = ""
    if len(datalist) > 0:
        for ele in datalist:
            if ele["status"] != "optimal" and stat <2:

                stat = 2
                optimal = 0
            else:
                optimal = 1
            stroutput += "\nSlot : " + str(ele["physicalLocation"]["slot"]) + ", Status : " + ele[
                "status"] + ", Product ID : " + ele["productID"] + ", Part No : " + ele[
                             "partNumber"] + ", Serial No : " + ele["serialNumber"] + ", Date of Manufacture : " + str(
                datetime.datetime.fromtimestamp(int(ele["manufacturerDate"])).strftime("%m/%d/%y"))
            strPerfData += "Slot:" + str(ele["physicalLocation"]["slot"]) + "=" + str(optimal) + ";;0;1; "
            total += 1
    else:
        stat =3
        stroutput += "\nNo EBOD IOM available in array."
    return {"strOutPut": stroutput, "strPerfData": strPerfData}


'''
    To get tray status from the data map
'''


def get_tray_status(data):
    global stat
    datalist = data["tray"]
    stroutput = "\n\nTray Status"
    optimal = 1
    total = 0
    strPerfData = ""
    if len(datalist) > 0:
        for ele in datalist:
            currentstat = "Optimal"
            if (ele["trayIDMismatch"] or ele["trayIDConflict"] or ele["esmVersionMismatch"] or ele["esmMiswire"] or ele[
                "drvMHSpeedMismatch"] or ele["unsupportedTray"] or ele["esmHardwareMismatch"] or ele[
                "isMisconfigured"] or ele["esmFactoryDefaultsMismatch"]) and stat <2:

                stat = 2
                optimal = 0
                currentstat = "Need Attention"
            else:
                optimal = 1
            stroutput += "\nTray Id : " + str(ele["trayId"]) + ", Slot : " + str(
                ele["physicalLocation"]["slot"]) + ", Status : " + currentstat + ", Part Number : " + ele[
                             "partNumber"].strip() + ", S. No : " + ele["serialNumber"].strip() \
                         + ", Date of Manufacture : " + str(
                datetime.datetime.fromtimestamp(int(ele["manufacturerDate"])).strftime("%m/%d/%y"))
            strPerfData += "TrayId:" + str(ele["trayId"]) + "=" + str(optimal) + ";;0;1; "
            total += 1
    else:
        stat =3
        stroutput += "\nNo Tray available in array."
    return {"strOutPut": stroutput, "strPerfData": strPerfData}


'''
    To load battery status from the data
'''


def get_battery_status(data):
    datalist = data["componentBundle"]["battery"]
    global stat
    stroutput = "\n\nBatteries Status "
    strPerfData = ""
    optimal = 1
    total = 0
    if len(datalist) >0:
        for ele in datalist:
            if ele["status"] != "optimal" and stat <2:

                stat = 2
                optimal = 0
            else:
                optimal = 1
            stroutput += "\nSlot : " + str(ele["physicalLocation"]["slot"]) + ", Status : " + ele[
                "status"] + ", Battery can Expire : " + str(ele["batteryCanExpire"]) + ", Automatic Age Reset : " + str(
                ele["automaticAgeReset"]) + ", Date of manufacture : " + str(
                datetime.datetime.fromtimestamp(int(ele["manufacturerDate"])).strftime("%m/%d/%y")) + ", Vendor Name : " + \
                         ele["vendorName"].strip() + ", Part No : " + ele["vendorPN"].strip() + ", S.no : " + ele[
                             "vendorSN"].strip()
            strPerfData += "Slot:" + str(ele["physicalLocation"]["slot"]) + "=" + str(optimal) + ";;0;1; "
            total += 1
    else:
        stat =3
        stroutput+="No Batteries found in array."
    return {"strOutPut": stroutput, "strPerfData": strPerfData}


'''
    To load fan status from the data
'''


def get_fan_status(data):
    global stat
    datalist = data["componentBundle"]["fan"]
    stroutput = "\n\nFans Details"
    optimal = 1
    total = 0
    strperfdata = ""
    if len(datalist) >0:
        for ele in datalist:
            if ele["status"] != "optimal" and stat <2:

                stat = 2
                optimal = 0
            else:
                optimal = 1
            stroutput += "\nSlot : " + str(ele["physicalLocation"]["slot"]) + ", Status : " + ele["status"]
            strperfdata += "Slot:" + str(ele["physicalLocation"]["slot"]) + "=" + str(optimal) + ";;0;1; "
            total += 1
    else:
        stat =3
        stroutput+="No fans found in array."
    return {"strOutPut": stroutput, "strPerfData": strperfdata}


'''
    To load power supply data
'''


def get_powersupp_status(data):
    global stat
    datalist = data["componentBundle"]["powerSupply"]
    stroutput = "\n\nPower Supplies"
    optimal = 1
    strPerfData = ""
    total = 0
    if len(datalist) >0:
        for ele in datalist:
            if ele["status"] != "optimal" and stat <2:

                stat = 2
                optimal = 0
            else:
                optimal = 1
            stroutput += "\nSlot : " + str(ele["physicalLocation"]["slot"]) + ", Status : " + ele[
                "status"] + ", Part No : " + ele["partNumber"].strip() + ", Serial No : " + ele[
                             "serialNumber"].strip() + ", Date of Manufacture : " + str(
                datetime.datetime.fromtimestamp(int(ele["manufacturerDate"])).strftime("%m/%d/%y"))
            strPerfData += "Slot:" + str(ele["physicalLocation"]["slot"]) + "=" + str(optimal) + ";;0;1; "
            total += 1
    else:
        stat =3
        stroutput +="No Power Supplies found in array"
    return {"strOutPut": stroutput, "strPerfData": strPerfData}


'''
    To load controller status
'''


def get_controller_status(data, arrayid, controllername):
    global stat
    datalist = data["controller"]
    stroutput = "\n\nController Status"
    optimal = 1
    strPerfData = ""
    total = 0
    if len(datalist) >0 :
        for ele in datalist:
            if ele["status"] != "optimal" and stat <2:

                stat = 2
                optimal = 0
            else:
                optimal = 1
            stroutput += "\nController : " + controllername[ele["controllerRef"]] + ", Status : " + ele["status"]
            strPerfData += "Controller:" + controllername[ele["controllerRef"]] + "=" + str(optimal) + ";;0;1; "
            total += 1
    else:
        stat =3
        stroutput +=" No controllers found in array."
    return {"strOutPut": stroutput, "strPerfData": strPerfData}


'''
    To get physical component status for a particular array. Read the controller.csv file to get the data of array.
'''


def getphysicalcomptstatus():
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

                    lstresult.append(get_phy_comp_stat_by_array(currentarrayid, sessionid, arrayinfo, controllername))
                    controllername = {}
                    controllername[row[headerList.index("controllerRef")]] = row[headerList.index("controllerLabel")]

                else:
                    firstarray = False

                currentarrayid = arrayId
    if arrayId:

        lstresult.append(get_phy_comp_stat_by_array(arrayId, sessionid, arrayinfo, controllername))
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
            strResult = "Critical - Some physical components are down.|" + firstPerData + "\n" + strresultdata + "|" + strresultperdata
        elif stat ==3:
            strResult = "STATUS UNKNOWN - Physical component not found" +strresultdata
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
        argmap = {"mode": "", "hostIp": "", "proxyUrl": "", "username":"","password":""}
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
                logger = logging.getLogger("PHYCOMPSTAT")
                logger.setLevel(logging.DEBUG)
                logger.addHandler(handler)
            else:
                print "Invalid arguments passed"
                logging.error("Invalid arguments passed",exc_info=True)
                sys.exit(3)

        global serverUrl;
        if argmap["proxyUrl"]:
            serverUrl = "https://" + argmap["proxyUrl"];

            urlToServer = serverUrl + "/devmgr/v2"

            loginUrl = serverUrl + "/devmgr/utils"
        else:
            print "STATUS UNKNOWN- Webproxy must be set"
            logging.error("Webproxy not set",exc_info=True)
            sys.exit(3)



        mode = argmap["mode"];
        if mode!="" and mode!="ALL":
            try:
                index = listmode.index(mode);
            except:
                print "STATUS UNKNOWN-Incorrect value for mode"
                sys.exit(3)
        else:
            mode =""
        if argmap["username"] !="":

            username = argmap["username"]

        if argmap["password"] !="":

            password = argmap["password"]


        if argmap["hostIp"] != "127.0.0.1":
            hostipaddress = argmap["hostIp"]

    logger.debug("Host Ip:" + hostipaddress)
    logger.debug("Webproxy:" + argmap["proxyUrl"])
    logger.debug("Mode:" + argmap["mode"])

    str = getphysicalcomptstatus()
    print str
    sys.exit(stat)
except Exception, err:
    logger.error("Error inside get volume stat by controller", exc_info=True)
    print "STATUS UNKNOWN"
    sys.exit(3)
