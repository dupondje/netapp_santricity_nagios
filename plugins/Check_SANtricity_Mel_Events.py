#!/usr/bin/python
# Copyright 2015 NetApp Inc.  All rights reserved.
import sys
import csv
import datetime
import logging

import SANtricityStorage

from logging.handlers import RotatingFileHandler
serverUrl='https://10.0.1.30:8443'


urlToServer=serverUrl+"/devmgr/v2"
loginUrl=serverUrl +"/devmgr/utils"
logging.basicConfig(format='%(asctime)s - %(name)s : %(message)s',filename='/tmp/nagios-python.log',level=logging.DEBUG)
handler = RotatingFileHandler('/tmp/nagios-python.log', maxBytes=SANtricityStorage.maxbytes,
                                  backupCount=20)

logger = logging.getLogger("MELEVENTS")
logger.setLevel(logging.INFO)
logger.addHandler(handler)
oldesttime=0
stat=0
criticalcount=0
othercount=0
username="rw"
password="rw"

'''
This method is used to fetch Mel events from given array id.
'''
def getMelEvents(arrayinfo,sessionid):
    try:
        global stat
        global criticalcount
        global othercount
        logging.info("In StoragePool INFO")
        arrayid=arrayinfo["arrayId"]
        arrayName=arrayinfo["arrayName"]
        lstOfArraySys= SANtricityStorage.get_data_from_REST(urlToServer,sessionid,arrayid,"mel-events")
        criticalevents= {}
        otherevents={}
        criticalcnt=0
        othercnt=0
        for lst in lstOfArraySys:
            if lst["critical"] :
                if lst["timeStamp"] in criticalevents.keys():
                    (criticalevents[lst["timeStamp"]]).append(lst)
                else:
                    newlst=[]
                    newlst.append(lst)
                    criticalevents[lst["timeStamp"]] = newlst;
                criticalcnt+= 1
            else:
                if lst["timeStamp"] in otherevents.keys():
                    (otherevents[lst["timeStamp"]]).append(lst)
                else:
                    newlst=[]
                    newlst.append(lst)
                    otherevents[lst["timeStamp"]] =newlst
                othercnt += 1


        criticalcount=criticalcnt


        othercount = othercnt
        if criticalcnt >0:
            stat=2
        strrepdata=" Array Name :"+arrayName
        strrepdata+="\nNo of critical events : "+str(criticalcnt) +", No of Other events : "+ str(othercnt)
        strrepdata+="\nCritical Mel Events"
        strrepdata+=getoutput(criticalevents)
        strrepdata+="\n\nOther Events"
        strrepdata+=getoutput(otherevents)

        return strrepdata

    except Exception as err:
        logger.error("Error in Storage pool",exc_info=True)
        print("STATUS UNKNOWN - Error in storage pool")
        sys.exit(3)

'''
    This method is used to prepare output for mel events
'''
def getoutput(eventmap):
    global oldesttime
    lstsorted = sorted(eventmap.keys())
    strrepdata=""
    size= len(lstsorted) -1
    while size >=0:
            ele= eventmap[lstsorted[size]]

            logger.info(ele[0])
            for lstitem in ele:

                strrepdata+="\n\nLocation : "+lstitem["location"] +", Category : "+lstitem["category"] +", Priority : "+lstitem["priority"] +", Time : "+str(datetime.datetime.fromtimestamp(int(lstitem["timeStamp"])).strftime("%m/%d/%y"))
                strrepdata+="\nDescription : "+lstitem["description"]
            size -=1

    if len(lstsorted)> 0 and oldesttime > lstsorted[0]:

        oldesttime = lstsorted[0]

    return strrepdata

'''
This method will read array information from the controller.csv file.
If the file is older than the time window, array information will be reloaded.
'''
def getMelEventInformation():
    sessionid= SANtricityStorage.login(loginUrl,username,password)
    SANtricityStorage.getStorageSystemDetails(urlToServer,sessionid)
    filename = SANtricityStorage.getStoragePath() + "/controller.csv"
    fileforread=open(filename,"r")
    csvreader=csv.reader(fileforread,delimiter=",")
    firstline=True
    arrayInfo={}
    strResultData=""
    contcount=0
    currentarrayid=""
    firstArray =True
    arrayid=""
    for row in csvreader:
        if firstline:
            headerlist=row
            firstline =False
        else:
            if hostipaddress and (row[headerlist.index("ip1")] == hostipaddress or row[headerlist.index("ip2")] == hostipaddress):
                arrayid=row[headerlist.index("arrayId")]
                lstEle= {"arrayName":row[headerlist.index("arrayName")],"arrayId":arrayid}
                contcount+=1
                if contcount ==2:
                    break
            elif  hostipaddress == "":
                arrayid=row[headerlist.index("arrayId")]
                arrayInfo[arrayid]={"arrayName":row[headerlist.index("arrayName")]}
                if currentarrayid != arrayid and firstArray ==False:
                        lstEle= {"arrayName":currentArrayName,"arrayId":currentarrayid}
                        strResultData+=getMelEvents(lstEle,sessionid)
                else:
                     firstArray =False

                currentarrayid =arrayid
                currentArrayName= row[headerlist.index("arrayName")]

    if arrayid :
         strResultData+=getMelEvents(lstEle,sessionid)
    else:
         global stat
         stat =3
         return "STATUS UNKNOWN - Host ip is not configured with webproxy"

    if stat ==0:
       strRepData = "OK - Total "+ str(othercount + criticalcount)+" mel events found ||"+strResultData
    elif stat ==2:
       strRepData = "Critical - Total "+ str(othercount + criticalcount)+" mel events found including "+ str(criticalcount) +" critical events  ||"+strResultData
    logging.info("dataa="+ strRepData)
    return strRepData

try:
    if len(sys.argv) < 4:
        print("STATUS UNKNOWN - Required parameters not set")
        sys.exit(3)
    else:
        nextelearg=False
        argmap={"hostIp":"","proxyUrl":"","username":"","password":""}
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

            elif element =="-h":
                nextelearg=True
                argname="hostIp"
            elif element =="-webproxy":
                nextelearg=True
                argname="proxyUrl"
            elif element =="-username":
                nextelearg=True
                argname="username"
            elif element =="-password":
                nextelearg=True
                argname="password"
            elif element =="-debug":

                #logging.basicConfig(format='%(asctime)s - %(name)s : %(message)s',filename='/tmp/nagios-python.log',level=logging.DEBUG)
                logger = logging.getLogger("VOLUMESTATBYCONT")
                '''file_handler = logging.handlers.RotatingFileHandler('/tmp/nagios-python.log', maxBytes=2500000, backupCount=5)
                formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
                file_handler.setFormatter(formatter)

                logger.addHandler(file_handler)'''
                logger.setLevel(logging.DEBUG)
            else:
                print("Invalid arguments passed")
                sys.exit(3)



        serverUrl="https://"+argmap["proxyUrl"];

        urlToServer=serverUrl+"/devmgr/v2"

        loginUrl=serverUrl +"/devmgr/utils"


        hostipaddress = argmap["hostIp"]

        if argmap["username"] !="":

            username = argmap["username"]

        if argmap["password"] !="":

            password = argmap["password"]

    logger.debug("Server URL:"+serverUrl)
    logger.debug("Host Add"+hostipaddress)


    str=getMelEventInformation()
    print(str)
    sys.exit(stat)
except Exception as err:
        print("STATUS UNKNOWN")
        logger.error("Error in Mel events",exc_info=True)
        sys.exit(3)
