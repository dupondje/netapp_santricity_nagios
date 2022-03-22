#!/usr/bin/python
# Copyright 2015 NetApp Inc.  All rights reserved.
import sys
import csv
import logging

import SANtricityStorage
from logging.handlers import RotatingFileHandler

serverUrl = "https://10.0.1.30:8443"
__author__ = 'hardikJsheth'
urlToServer = serverUrl + "/devmgr/v2"
loginUrl = serverUrl + "/devmgr/utils"


logging.basicConfig(format='%(asctime)s - %(name)s : %(message)s', filename='/tmp/nagios-python.log', level=logging.DEBUG)
handler = RotatingFileHandler('/tmp/nagios-python.log', maxBytes=SANtricityStorage.maxbytes,
                                  backupCount=20)
warning=0
critical=95

stat = 0
hostipaddress = ""
logger = logging.getLogger("VOLUMECACHSTATE")
logger.setLevel(logging.INFO)
logger.addHandler(handler)
username="rw"
password="rw"

def get_ssd_drive_stat(arrayid,sessionid,arrayinfo):
    global  stat
    logger.info("Inside get_phy_comp_temprature")
    stroutput="\nArray Name:"+arrayinfo[arrayid]["arrayName"]
    strperdata=""


    data = SANtricityStorage.get_data_from_REST(urlToServer,sessionid,arrayid,"drives")
    driveinfo= SANtricityStorage.read_csv_file("driverMap.csv","diskId","")

    stroutput+= "\n\nSSD Wear Life Monitoring"
    for ele in data:
        if ele["driveMediaType"] =="ssd" :
            rawcapacity=round(int(ele["rawCapacity"])/(1024*1024*1024),2)
            usablecapacity=round(int(ele["usableCapacity"])/(1024*1024*1024),2)
            avgerasecountper=round(ele["ssdWearLife"]["averageEraseCountPercent"],2)
            spareblkrem=round(ele["ssdWearLife"]["spareBlocksRemainingPercent"],2)
            if avgerasecountper >= warning and avgerasecountper < critical and stat <1:

                stat = 1
            elif avgerasecountper >=critical and stat < 2:

                stat=2
            logger.debug("Drive Id : "+ele["id"] +", Average Erase Count : "+str(avgerasecountper) +", Spare Block Percent : "+str(spareblkrem))
            stroutput+= "\nDrive : "+driveinfo[ele["id"]]["driveLabel"] + ", Raw Capacity : "+str(rawcapacity) +\
                        "GB, Usable Capacity : "+str(usablecapacity) +"GB, Average Erase Count : "+str(avgerasecountper)\
                        +"%, Spare Block Remaining : "+str(spareblkrem) +"%"
            strperdata+=driveinfo[ele["id"]]["driveLabel"]+"="+str(spareblkrem) +"%;"+str(warning)+";"+str(critical)+";;; "

    return {"strOutPut":stroutput,"strPerData":strperdata}
'''
   Read controller.csv file to read array information. Then use it to fetch SSD drive stats.
'''
def getssddrivelinfo():
    global stat
    sessionid= SANtricityStorage.login(loginUrl,username,password)
    SANtricityStorage.getStorageSystemDetails(urlToServer,sessionid, SANtricityStorage.getTime())
    file = SANtricityStorage.getStoragePath() + "/controller.csv"
    fileforread=open(file,"r")
    csvreader=csv.reader(fileforread,delimiter=",")
    firstline=True
    currentarrayid=""
    arrayinfo={}
    strresultdata=""
    strresultperdata=""
    lstresult=[]
    firstarray=True
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
                contcount+=1
                if contcount ==2:
                    break
            elif hostipaddress == "":
                arrayid=row[headerList.index("arrayId")]
                arrayinfo[arrayid]={"arrayName":row[headerList.index("arrayName")]}
                if currentarrayid != arrayid and firstarray ==False:
                        lstresult.append(get_ssd_drive_stat(currentarrayid,sessionid,arrayinfo))
                else:
                     firstarray =False

                currentarrayid =arrayid
    if arrayid :
        lstresult.append(get_ssd_drive_stat(arrayid,sessionid,arrayinfo))
        firstPerData=""
        firstline =True

        for listEle in lstresult:
            strresultdata += listEle["strOutPut"]
            if firstline and len(listEle["strPerData"]) >0:
                firstPerData =listEle["strPerData"]
                strArry=firstPerData.split(" ")
                firstspace=firstPerData.index(" ")
                strresultperdata +=firstPerData[firstspace +1:] +" "
                firstPerData=firstPerData[0:firstPerData.index(" ")]

                firstline=False
            else:
                strresultperdata+= listEle["strPerData"]

        strresultperdata = strresultperdata.strip()
        strresultdata = "\nThreshold Values - Warning : " + str(warning) + ", Critical : " + str(critical) +strresultdata
        if len(firstPerData) ==0:
            strResult = "STATUS UNKNOWN - No SSD drives found on this host."
            stat=3
        elif stat ==0 :
           strResult = "OK - All SSD Drives are good |"+firstPerData +"\n"+strresultdata +"|"+strresultperdata
        elif stat ==1 :
           strResult = "Warning -Some of the SSD drive has Average Erase Count above warning threshold. |"+firstPerData +"\n"+strresultdata +"|"+strresultperdata
        elif stat == 2:
            strResult="Critical- Some of the SSD drive has Average Erase Count above critical threshold.|"+firstPerData +"\n"+strresultdata +"|"+strresultperdata
    else:
        strResult = "Unknown-  Host ip address is not configured in web proxy."
        stat=3
    fileforread.close()
    return strResult


'''
MAIN Method
'''
try:
    if len(sys.argv) < 7:
        print("STATUS UNKNOWN - Required parameters not set")
        sys.exit(3)
    else:
        nextelearg=False
        argmap={"hostIp":"","proxyUrl":"","warning":"","critical":"","username":"","password":""}
        argname=""
        for element in sys.argv:
            if element.endswith(".py"):
               continue
            elif nextelearg :
                if element !="":
                    argmap[argname] =element
                    nextelearg=False
                else:
                    print("STATUS UNKNOWN - Incorrect value passed for"+argname)

            elif element == "-warning":
                nextelearg=True
                argname="warning"
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
            elif element == "-debug":

                logger = logging.getLogger("VOLUMESTATBYCONT")
                logger.setLevel(logging.DEBUG)
                logger.addHandler(handler)
            else:
                print("Invalid arguments passed")
                sys.exit(3)


        serverUrl="https://"+argmap["proxyUrl"];

        urlToServer=serverUrl+"/devmgr/v2"

        loginUrl=serverUrl +"/devmgr/utils"


        try:
            warning=float(argmap["warning"])
        except Exception as err:
            print("STATUS UNKNOWN - Warning threshold must be numeric")
            sys.exit(3)



        try:
            critical=float(argmap["critical"])
        except Exception as err:
            print("STATUS UNKNOWN - Critical threshold must be numeric")
            sys.exit(3)

        if warning >= critical:
            print('STATUS UNKNOWN - Incorrect value for warning  and critical threshold')
            sys.exit(3)

        if argmap["username"] !="":

            username = argmap["username"]
        if argmap["password"] !="":

            password = argmap["password"]

        hostipaddress = argmap["hostIp"]



    logger.debug("Low Threshold:"+str(warning))
    logger.debug("High Threshold:"+str(critical))
    logger.debug("Server URL:"+serverUrl)
    logger.debug("Host Add"+hostipaddress)

    str = getssddrivelinfo()
    print(str)
    sys.exit(stat)
except Exception as err:
        print("STATUS UNKNOWN")
        logger.error("Error in SSD drive statistics",exc_info=True)
        sys.exit(3)




