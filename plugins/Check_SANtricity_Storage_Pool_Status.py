#!/usr/bin/python
# Copyright 2015 NetApp Inc.  All rights reserved.
import sys
import csv
import logging

import SANtricityStorage
from logging.handlers import RotatingFileHandler

serverUrl='https://10.0.1.30:8443'
critical="95.0"
warning="75.0"
urlToServer=serverUrl+"/devmgr/v2"
loginUrl=serverUrl +"/devmgr/utils"
stat=0
noofoutput=-1
dirdiskdata={}
hostipaddress=""
logging.basicConfig(format='%(asctime)s - %(name)s : %(message)s',filename='nagios-python.log',level=logging.DEBUG)
handler = RotatingFileHandler('nagios-python.log', maxBytes=SANtricityStorage.maxbytes,
                                  backupCount=20)
logger = logging.getLogger("STORAGEPOOL")
logger.setLevel(logging.INFO)
logger.addHandler(handler)
username="rw"
password="rw"

'''
    Fetch storage pool information from REST endpoint /storage-pools
'''
def getstoragepoolinfo(eleMap,sessionid):
    try:
        global stat
        logging.info("In StoragePool INFO")
        arrayid=eleMap["arrayId"]
        arrayname=eleMap["arrayName"]
        lstofarraysys= SANtricityStorage.get_data_from_REST(urlToServer,sessionid,arrayid,"storage-pools")
        lst=[]
        logging.info(len(lstofarraysys))
        strdata=""
        strrepdata=""
        strfirstperfdata=""

        for lst in lstofarraysys:
            if lst["usedSpace"]:
                totalspace=round(float(lst["totalRaidedSpace"])/(1024*1024*1024),2)
                usedspace = round(float(lst["usedSpace"])/(1024*1024*1024),2)
                calwarning= round((float(warning) * totalspace/100),2)
                calcritical=round((float(critical) *totalspace /100),2)
                usedpercentage=round(((usedspace * 100)/totalspace),2)

                poolname=lst["label"]
                stStatus='Ok'
                if usedspace >= calwarning and usedspace < calcritical and stat < 1:

                    stat=1
                    stStatus="Warning"
                elif usedspace >=calcritical:

                    stStatus="Critical"
                    stat=2
                if lst["diskPool"]:
                    type= "Disk Pool"
                else:
                    type = "Volume Group"

                logger.debug("Pool Id : "+lst["id"] + " Label : "+poolname + " diskPool : "+str(lst["diskPool"])+"usedSpace : "+str(lst["usedSpace"]) +" Free Space : "+str(lst["freeSpace"])+ "raidedSpace : "+str(lst["totalRaidedSpace"]))
                if hostipaddress :
                    strrepdata="\nlabel : "+poolname +", Pool Type : "+type +", Raided Space : "+str(totalspace)+ "GB, Used Space : "+str(usedspace) +"GB, Used Space(%) : "+str(usedpercentage)

                else:
                    strrepdata="\nArray Name : "+arrayname +", label : "+poolname +", Pool Type : "+type  +", Raided Space : "+str(totalspace)+ "GB, Used Space : "+str(usedspace) +"GB, Used Space(%) : "+str(usedpercentage)

                reslistdata = {"strData":poolname+"="+str(usedspace)+"GB;"
                                                         +str(calwarning)+";"+str(calcritical)+";0;"+str(totalspace)+" ",
                                               "strRepData":strrepdata}

                if dirdiskdata.get(usedpercentage):
                    listFromDir=dirdiskdata.get(usedpercentage)
                    listFromDir.append(reslistdata)
                    dirdiskdata[usedpercentage] = listFromDir
                else:
                    dirdiskdata[usedpercentage] = [reslistdata]


        return {"strPerfData":strdata,"reportData":strrepdata}

    except Exception,err:
        logger.error("Error in Storage pool",exc_info=True)
        print "STATUS UNKNOWN - Error in storage pool"
        sys.exit(3)

'''
    Read controller.csv file to get the array information.
'''
def getstoragepoolinformation():
    sessionid= SANtricityStorage.login(loginUrl,username,password)
    SANtricityStorage.getStorageSystemDetails(urlToServer,sessionid)
    file = SANtricityStorage.getStoragePath() + "/controller.csv"
    fileforread=open(file,"rb")
    csvreader=csv.reader(fileforread,delimiter=",")
    firstline=True
    arrayinfo={}
    strperfdata =""
    strrepdata=""
    contcount=0
    currentarrayid=""
    firstarray =True
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
             elif hostipaddress == "":
                 arrayid=row[headerlist.index("arrayId")]
                 arrayinfo[arrayid]={"arrayName":row[headerlist.index("arrayName")]}
                 if currentarrayid <> arrayid and firstarray ==False:
                         lstEle= {"arrayName":currentArrayName,"arrayId":currentarrayid}
                         getstoragepoolinfo(lstEle,sessionid)
                 else:
                      firstarray =False
                 currentarrayid =arrayid
                 currentArrayName= row[headerlist.index("arrayName")]

    if arrayid :
         getstoragepoolinfo(lstEle,sessionid)
    else:
         global stat
         stat =3
         return "STATUS UNKNOWN - Host ip is not configured with webproxy"

    lstsorted=sorted(dirdiskdata.keys())
    size =len(lstsorted)-1
    totalcnt=0
    if hostipaddress != '':
        strrepdata = "\n\nArray Name:"+lstEle["arrayName"]

    '''
        No of disks displayed in output can be limited based on input parameter.
    '''
    while size >=0 :
        data= dirdiskdata[lstsorted[size]]
        if len(data) ==1 and (noofoutput ==-1 or (noofoutput !=-1 and totalcnt < noofoutput)):
            datafromdir=data[0]
            strperfdata += datafromdir["strData"]
            strrepdata +=datafromdir["strRepData"]
            totalcnt +=1
        else:
            for lstitem in data:
                if noofoutput ==-1 or (noofoutput !=-1 and totalcnt < noofoutput):
                    strperfdata += lstitem["strData"]
                    strrepdata +=lstitem["strRepData"]
                    totalcnt +=1
                else:
                    break
        size-=1

    if stat == 0:
               stResult="OK - All storage pools have used space within threshold range."
    elif stat == 1:
               stResult="Warning - Some storage pools have used more space than warning threshold"
    elif stat ==2:
               stResult ="Critical - Some storage pools have used more space than critical space"

    strFirstPerfData=strperfdata[0:strperfdata.index(" ")]
    strperfdata=strperfdata[strperfdata.index(" ")+1:]

    strrepdata = "\nThreshold Values -   Warning : "+str(warning) +"%,  Critical : "+str(critical) + "%" +strrepdata
    stResult+= "|" +strFirstPerfData +strrepdata +"|"+strperfdata
    logging.info("dataa="+ stResult)
    return stResult

try:
    if len(sys.argv) < 7:
        print "STATUS UNKNOWN - Required parameters not set"
        sys.exit(3)
    else:
        nextelearg=False
        argmap={"hostIp":"","proxyUrl":"","warning":"","critical":"", "oplimit":"-1","username":"","password":""}
        argname=""
        for element in sys.argv:
            if element.endswith(".py"):
               continue
            elif nextelearg :
                if element !="":
                    argmap[argname] =element
                    nextelearg=False
                else:
                    print "STATUS UNKNOWN - Incorrect value passed for"+argname

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
            elif element == "-debug":

                logger = logging.getLogger("VOLUMESTATBYCONT")
                logger.setLevel(logging.DEBUG)
                logger.addHandler(handler)
            elif element =="-username":
                nextelearg=True
                argname="username"
            elif element =="-password":
                nextelearg=True
                argname="password"
            elif element == "-oplimit":
                nextelearg=True
                argname="oplimit"
            else:
                print "Invalid arguments passed"
                sys.exit(3)


        serverUrl="https://"+argmap["proxyUrl"];

        urlToServer=serverUrl+"/devmgr/v2"

        loginUrl=serverUrl +"/devmgr/utils"


        try:
            warning=float(argmap["warning"])
        except Exception,err:
            print "STATUS UNKNOWN - Warning threshold must be numeric"
            sys.exit(3)



        try:
            critical=float(argmap["critical"])
        except Exception,err:
            print "STATUS UNKNOWN - Critical threshold must be numeric"
            sys.exit(3)

        if warning >= critical:
            print 'STATUS UNKNOWN - Incorrect value for low and high threshold'
            sys.exit(3)

        if argmap["username"] !="":

            username = argmap["username"]

        if argmap["password"] !="":

            password = argmap["password"]


        hostipaddress = argmap["hostIp"]


        try:
            noofoutput=int(argmap["oplimit"])
        except Exception,err:
            print "STATUS UNKNOWN - Output limit must be integer"
            sys.exit(3)

    logger.debug("Low Threshold:"+str(warning))
    logger.debug("High Threshold:"+str(critical))
    logger.debug("Server URL:"+serverUrl)
    logger.debug("Host Add"+hostipaddress)

    str = getstoragepoolinformation()
    print str
    sys.exit(stat)
except Exception,err:
        print "STATUS UNKNOWN"
        logger.error("Error in Storage Pool Status",exc_info=True)
        sys.exit(3)



