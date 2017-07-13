#!/usr/bin/python
# Copyright 2015 NetApp Inc.  All rights reserved.
__author__ = 'hardikJsheth'
import os
import sys
import csv
import datetime
import time
import logging
import traceback
import json

import requests
from logging.handlers import RotatingFileHandler


filestoragepath="/tmp"

timewindow=30
crtnewfile=True
maxbytes=2000000

logging.basicConfig(format='%(asctime)s - %(name)s : %(message)s',filename='nagios-python.log',level=logging.DEBUG)
handler = RotatingFileHandler('nagios-python.log', maxBytes=maxbytes,
                                  backupCount=20)
logger =logging.getLogger("SANST")
logger.setLevel(logging.INFO)
logger.addHandler(handler)

def setTime(time):
    global timewindow
    timewindow =time

def getTime():
    return timewindow

def setStoragePath(storagepath):
    global  filestoragepath
    filestoragepath=storagepath

def getStoragePath():
    return filestoragepath

def login(loginurl,username="rw",password="rw"):
        try:
                logging.info(" In login")
                url=loginurl+ "/login?uid="+username+"&pwd="+password+"&onlycheck=false"
                #print url
                r=requests.get(url,verify=False, headers={'Content-Type': 'application/json'})
                #print r.cookies['JSESSIONID']
                return r.cookies['JSESSIONID']

        except Exception,err:
                logging.error("Error in login",exc_info=True)
                print "STATUS UNKNOWN-In valid web proxy IP or Web proxy is not responding."
                sys.exit(3)

def getStorageSystem(urltoserver,sessionId):
        try:
                logging.info("In getStorageSystem")
                url=urltoserver+'/storage-systems'

                r=requests.get(url,verify=False, headers={'Content-Type': 'application/json','Cookie':'JSESSIONID='+sessionId})


                lstOfArraySys=r.json()
                logging.info(len(lstOfArraySys))
                lst=[]

                for listEle in lstOfArraySys:
                        dataMap={}
                        dataMap["arrayId"]=listEle["id"]
                        dataMap["arrayName"]=listEle["name"]
                        dataMap["ip1"] = listEle["ip1"]
                        dataMap["ip2"] = listEle["ip2"]
                        if listEle["name"] <> "" and listEle["status"] <> "offline":
                                lst.append(dataMap)
                return lst
        except Exception,err:
                logger.error("Error in getStorageSystem",exc_info=True)
                print "STATUS UNKNOWN"
                sys.exit(3)


def getStorageSystemDetails(urltoserver,sessionid,timewindow =5):

         file =filestoragepath + "/controller.csv"
         getData=True
         logger.info("File Path:::"+file)
         logger.info("File status:::"+str(os.path.isfile(file)))
         if os.path.isfile(file):
                 fileCtime=os.path.getmtime(file)
                 d=(time.time() - fileCtime)/60
                 logging.info(d)
                 if d >timewindow:
                         logging.info("getting storage system details")
                         getData=True
                 else:
                         getData=False
         if getData:
                lst=getStorageSystem(urltoserver,sessionid)
                i=0
                for ele in lst:
                    ele["sessionId"]=sessionid
                    data=getStroageSystemGraph(urltoserver,ele)
                    #print data

                    if data:
                            ele["controllerRef"]=data["controllerRef"]
                            ele["driveMap"]=data["driveMap"]
                            ele["volumeGroup"]=data["volumeGroup"]
                            ele["volume"]=data["volume"]
                crtnewfile = True
                if len(lst) >0:
                    try:
                        fhandleCon=open(filestoragepath+"/controller.csv",'wb')
                        fhandleDrv=open(filestoragepath+"/driverMap.csv",'wb')
                        fhandlevg=open(filestoragepath+"/VolumeGroup.csv",'wb')
                        fhandlevl=open(filestoragepath+"/Volume.csv",'wb')

                        for ele in lst:
                                logging.info(list(ele.keys()))
                                writeDataToCSV(fhandleCon,ele["controllerRef"],crtnewfile)
                                writeDataToCSV(fhandleDrv,ele["driveMap"],crtnewfile)
                                writeDataToCSV(fhandlevg,ele["volumeGroup"],crtnewfile)
                                writeDataToCSV(fhandlevl,ele["volume"],crtnewfile)
                                crtnewfile=False
                    except:
                        logger.error("Error in writing file ",exc_info=True)
                    finally:
                        fhandleCon.close()
                        fhandleDrv.close()
                        fhandlevl.close()
                        fhandlevg.close()


def writeDataToCSV(filehandle,data,crtnewfile):
        logging.debug("In writeData to CSV")
        try:

            writer=csv.writer(filehandle,delimiter=",")
            i=0
            for lstEle in data:
                    #Add Header line  only once.
                    if i ==0 and crtnewfile:
                        writer.writerow(lstEle)
                    elif i>0:
                        writer.writerow(lstEle)
                    i+=1
        except Exception,err:
                logging.error("Error in writing file ",exc_info=True)


def getStroageSystemGraph(urltoserver,eleMap):

        try:

                arrayId=eleMap["arrayId"]
                arrayName=eleMap["arrayName"]
                ip1=eleMap["ip1"]
                ip2=eleMap["ip2"]
                sessionId=eleMap["sessionId"]
                lstOfArraySys=get_data_from_REST(urltoserver,sessionId,arrayId,"graph")

                if lstOfArraySys:


                    lst=[]
                    listEle=["arrayId","arrayName","controllerRef","controllerLabel","ip1","ip2"]
                    lst.append(listEle)

                    dirData={}
                    for lstEle in lstOfArraySys["controller"]:
                            controllerLabel=hex((lstEle["physicalLocation"])["slot"]+9)[2:]
                            listEle=[arrayId,arrayName,lstEle["controllerRef"],arrayName+controllerLabel,ip1,ip2]
                            lst.append(listEle)

                    ###To Get information about Drive
                    dirData["controllerRef"]=lst;
                    lst=[]
                    lstTraySlot=[]
                    lstTrayRef=[]
                    for eleTray in lstOfArraySys["tray"]:
                            lstTraySlot.append(eleTray["trayId"])
                            lstTrayRef.append(eleTray["trayRef"])

                    listEle=["arrayId","arrayName","diskId","volumeGroupRef","driveLabel"]
                    lst.append(listEle)


                    for lstEle in lstOfArraySys["drive"]:

                            driveLabel = lstEle["physicalLocation"]["trayRef"]


                            if driveLabel<> None and driveLabel in lstTrayRef:

                               #import ipdb;ipdb.set_trace()

                               driveLabelData = str(lstTraySlot[lstTrayRef.index(driveLabel)]) +"."+str((lstEle["physicalLocation"])["locationPosition"])+"."+str((lstEle["physicalLocation"])["slot"])
                            else:
                               driveLabelData = "unassigned"
                            listEle=[arrayId,arrayName,lstEle["id"], lstEle["currentVolumeGroupRef"],driveLabelData]

                            lst.append(listEle)
                    dirData["driveMap"] = lst;

                    #To get information about Volume Group
                    lst=[]
                    listEle=["arrayId","arrayName","volumeGroupRef","volumeGroup","ip1","ip2"]
                    lst.append(listEle)
                    for lstEle in lstOfArraySys["volumeGroup"]:
                        listEle=[arrayId,arrayName,lstEle["id"],lstEle["label"],ip1,ip2]
                        lst.append(listEle)
                    dirData["volumeGroup"]=lst

                    #To get details of volumes
                    lst=[]
                    listEle=["arrayId","arrayName","volumeName","volumeGroupRef","controllerRef","volumeRef"]
                    lst.append(listEle)
                    for lstEle in lstOfArraySys["volume"]:

                            listEle=[arrayId,arrayName,lstEle["name"], lstEle["volumeGroupRef"],lstEle["currentManager"],lstEle["volumeRef"]]
                            lst.append(listEle)
                    dirData["volume"]=lst

                    return dirData


        except Exception,err:
               logger.error("Error in getStroageSystemGraph",exc_info=True)

               return False


def getVolumeStates(urltoserver,sessionid,timewindow,arrayid):

         file =filestoragepath + "/"+arrayid + ".txt"
         getData=True
         try:
             if os.path.isfile(file):
                 fileCtime=os.path.getmtime(file)
                 d=(time.time() - fileCtime)/60
                 logging.info(d)
                 if d >timewindow:
                         logging.info("getting storage system details")
                         getData=True
                 else:
                         getData=False

             if getData:
               getVolumeFile(urltoserver,sessionid,arrayid)

             fileforread=open(file,"r")
             lst=json.load(fileforread)
             return lst
             fileforread.close()
         except Exception,err:
               logging.error("Error in getVolumeStates", exc_info=True)
               getVolumeFile(urltoserver,sessionid,arrayid)


def writeDirDataToCSV(filename,lstofarrays):
         fileForData=open(filename,'w')
         try:
             for lstele in lstofarrays:
                 fileForData.write(str(lstele)+"\n")

         except Exception,err:
                print Exception,err
         finally:
             fileForData.close()


def getVolumeFile(urltoserver,sessionid,arrayid):
          url=urltoserver+'/storage-systems/'+arrayid+'/analysed-volume-statistics'
          dirData={}
          r=requests.get(url,verify=False, headers={'Content-Type': 'application/json','Cookie':'JSESSIONID='+sessionid})
          if r.status_code ==200:
              lstOfArraySys=r.json()
              filename=filestoragepath + "/"+arrayid+".txt"
              fileforread=open(filename,"w")
              json.dump(lstOfArraySys,fileforread)
              #writeDirDataToCSV(filename,lstOfArraySys)
              fileforread.close()
          else:
              print "Unknown - REST end point returned "+str(r.status_code) + "- "+r.reason
              sys.exit(3)


def get_data_from_REST(urltoserver,sessionid,arrayid,restendpoint =""):
          lstOfArraySys=[]
          if arrayid :
            url=urltoserver+'/storage-systems/'+arrayid+'/'+restendpoint

          else:
             url=urltoserver+'/'+restendpoint
          r=requests.get(url,verify=False, headers={'Content-Type': 'application/json','Cookie':'JSESSIONID='+sessionid})
          if r.status_code == 200 :
              lstOfArraySys=r.json()
          elif r.status_code ==404:
              logging.info("Error in get_data_from_REST",exc_info=True)
              print "Status UNKNOWN-Storage device not found"

          elif r.status_code == 424:
              logging.info("Error in get_data_from_REST",exc_info=True)
              print "Status UNKNOWN -Storage device offline"

          else:
              print "Unknown - REST end point returned "+str(r.status_code) + "- "+r.reason

          return lstOfArraySys


def read_csv_file(fileName,key1,key2):
         file= filestoragepath +"/"+fileName
         fileForRead=open(file,"rb")
         csvReader=csv.reader(fileForRead,delimiter=",")
         firstLine=True
         datalist={}
         for data in csvReader:
             if firstLine :
                 firstLine =False
                 headerList=data
             else:
                 newrow={}
                 for col in headerList:
                     newrow[col]=data[headerList.index(col)]
                 if key2:
                    datalist[data[headerList.index(key1)]+"~"+data[headerList.index(key2)]]=newrow
                 else:
                    datalist[data[headerList.index(key1)]]=newrow
         fileForRead.close()
         return datalist

def deleteArray(sessionid,urlToServer,id):
     try:
                logging.info("In configureArray")
                url=urlToServer+'/storage-systems/'+id
                data = "{ \"id\": [\""+id+"\"]}"
                r=requests.delete(url,verify=False, headers={'Content-Type': 'application/json','Cookie':'JSESSIONID='+sessionid})

                print r.status_code


     except Exception,err:
                logger.error("Error in configure array",exc_info=True)
                print "STATUS UNKNOWN"
                sys.exit(3)

if __name__=='__main__' :
        #sessionid=login("https://172.16.1.49:8443/devmgr/utils","rw","rw")
        #deleteArray(sessionid,"https://172.16.1.49:8443/devmgr/v2","9e8b33fa-e00a-423a-9a78-b1744322246e")
        print ""+datetime.datetime.strftime(datetime.datetime.now() - datetime.timedelta(days= 8),"%s")
