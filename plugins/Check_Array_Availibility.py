#!/usr/bin/python
import sys
import csv
import logging

import SANtricityStorage
from logging.handlers import RotatingFileHandler

serverUrl = 'https://10.0.1.30:8443'
__author__ = 'hardikJsheth'
urlToServer = serverUrl + "/devmgr/v2"
loginUrl = serverUrl + "/devmgr/utils"
stat = 0
logging.basicConfig(format='%(asctime)s - %(name)s : %(message)s', filename='/tmp/nagios-python.log', level=logging.DEBUG)
handler = RotatingFileHandler('/tmp/nagios-python.log', maxBytes=SANtricityStorage.maxbytes, backupCount=20)
logger = logging.getLogger("STORAGEPOOL")
logger.addHandler(handler)
logger.setLevel(logging.INFO)
username = "rw"
password = "rw"
'''
    This method will fetch the current status of the array using the REST endpoint
'''


def get_array_availibility(sessionid, arrayid):
    global stat
    data = SANtricityStorage.get_data_from_REST(urlToServer, sessionid, arrayid)
    status = data["status"]
    if status == "needsAttn" and stat < 1:

        stat = 1
    elif status == "neverContacted" and stat < 2:

        stat = 2
    logger.debug("ArrayID:" + arrayid)
    logger.debug("Array Name:" + data["name"] + "ip1:" + data["ip1"] + "ip2: " + data["ip2"] + " id: " + data["id"])
    return "\nArray Name:" + data["name"] + " Status:" + data["status"] + " Last Boot Time:" + data["bootTime"]


'''
 This method reads array information from the controller.csv file to get the array id.
'''


def getArrayInformation():
    global stat
    logger.info("Inside getArrayInformation")
    sessionid = SANtricityStorage.login(loginUrl, username, password)
    SANtricityStorage.getStorageSystemDetails(urlToServer, sessionid)
    file = SANtricityStorage.getStoragePath() + "/controller.csv"
    fileForRead = open(file, "r")
    csvReader = csv.reader(fileForRead, delimiter=",")
    firstLine = True
    strResultData = ""
    contcount = 0
    currentArrayId = ""
    firstArray = True

    arrayId = ''
    for row in csvReader:
        if firstLine:
            headerList = row
            firstLine = False
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
                if currentArrayId != arrayId and firstArray == False:
                    strResultData += get_array_availibility(sessionid, currentArrayId)
                else:
                    firstArray = False

                currentArrayId = arrayId

    if arrayId:
        strResultData += get_array_availibility(sessionid, arrayId)
    else:

        stat = 3
        strResultData = "STATUS UNKNOWN - Host ip is not configured with webproxy"

    return strResultData


try:
    if len(sys.argv) < 3:
        print("STATUS UNKNOWN - Required parameters not set")
        sys.exit(3)
    else:
        nextelearg = False
        argmap = {"hostIp": "", "proxyUrl": "", "username": "", "password": ""}
        argname = ""
        for element in sys.argv:
            if element.endswith(".py"):
                continue
            elif nextelearg:
                argmap[argname] = element
                nextelearg = False

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
            elif element == "-debug":

                logger = logging.getLogger("VOLUMESTATBYCONT")
                logger.setLevel(logging.DEBUG)
                logger.addHandler(handler)
            else:
                print("Invalid arguments passed")
                sys.exit(3)


        serverUrl = "https://" + argmap["proxyUrl"];

        urlToServer = serverUrl + "/devmgr/v2"

        loginUrl = serverUrl + "/devmgr/utils"


        hostipaddress = argmap["hostIp"]

    if argmap["username"] != "":

        username = argmap["username"]

    if argmap["password"] != "":

        password = argmap["password"]

    logger.debug("Server URL:" + serverUrl)
    logger.debug("Host Add" + hostipaddress)

    str = getArrayInformation()

    if stat == 0:
        str = "OK - Array is up and running|" + str
    elif stat == 1:
        str = "Warning - Array is in needAttn stat|" + str
    elif stat == 2:
        str = "Critical - Array is down|" + str

    print(str)
    sys.exit(stat)

except Exception as err:
    print("STATUS UNKNOWN")
    logger.error("Error in Storage Pool Status", exc_info=True)
    sys.exit(3)
