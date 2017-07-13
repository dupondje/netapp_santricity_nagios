# netapp_santricity_nagios
NetApp SANtricity Nagios Plugin

The plugin is taken from [Nagios Exchange](https://exchange.nagios.org/directory/Plugins/Hardware/Storage-Systems/SAN-and-NAS/NetApp/NetApp-SANtricity-Plug-2Din-for-Nagios/details)
But some adjustments were made.

Feel free to open issues or pull requests!

## Install Howto

These are plugins to monitor NetApp's SANtricity e-Series storage. To use this plugins, you require SANtricity webproxy. We have developed wizard which considerably reduces configuration efforts.
There are total of 14 plugins.

These plugins requires SANtricity webproxy. It performs following tasks:
-->Connect to NetApp SANtricity web proxy through REST end points
-->Prepare csv files to track pairs for arrays and controllers
-->Read csv files to fetch array information
-->Call REST end point to fetch required statistics for each array
-->Calculate service status based on threshold values
-->Prepare performance data ro display in graph
-->Return status along with performance data

Following is the list for plugin names along with command for each plugin:
1) Host Configuration
Configure Arrays as a host in Nagios.
Command:$USER1$/HostConfiguration.py -webproxy $ARG1$ -ip1 $ARG2$ -ip2 $ARG3$ -username $ARG4$ -password $ARG5$

2) Track and Report Performance information for Volume by Controller

$USER1$/Check_SANtricity_Volume_Status_BYCON.py -h $HOSTADDRESS$ -mode $ARG2$ -low $ARG3$ -high $ARG4$ -webproxy $ARG1$ -r $ARG5$ -username $ARG4$ -password $ARG5$

3) Track and Report Performance information for Volume by Volume Group
$USER1$/Check_SANtricity_Volume_Status_BYVG.py -h $HOSTADDRESS$ -mode $ARG2$ -low $ARG3$ -high $ARG4$ -webproxy $ARG1$ -username $ARG4$ -password $ARG5$

4) Track and Report Performance information by Volume
$USER1$/Check_SANtricity_Volume_Status.py -h $HOSTADDRESS$ -mode $ARG2$ -low $ARG3$ -high $ARG4$ -webproxy $ARG1$ -username $ARG4$ -password $ARG5$

5) Track and Report Performance information for Drive
$USER1$/Check_SANtricity_Drive_Stat.py -h $HOSTADDRESS$ -mode $ARG2$ -low $ARG3$ -high $ARG4$ -webproxy $ARG1$ -username $ARG4$ -password $ARG5$


Possible values for Mode for above five services are:
1)RIOP --Read IOPS 2) WIOP --Write IOPS
3)RTHP - Read Throughput 3) WTHP --Write Throughput
5)RLAT - Read Latency 6) WLAT - Write Latency

Possible values for Range (r) are : low /high

6) Monitor and Report Physical Component Status
-->This plugins helps in monitoring various physical component of the SANtricity storage.
Command: $USER1$/Check_Physical_Comp_Status.py -h $HOSTADDRESS$ -webproxy $ARG1$ -mode $ARG2$ -username $ARG4$ -password $ARG5$

The mode can have one of the following value:
1) ARRY : To monitor array 2) RBCON : RBOD Controllers
3) EBIOM : To monitor EBOD IOMS 3)TRAY : To monitor Trays
5) FAN: To monitor Fans 6) BATT : To monitor batteries
7) PSU : Power Supply 8)DDS : Disk Drives

7) Monitor and Report Physical Component Temperature
Command: $USER1$/Check_Physical_Comp_Temp.py -h $HOSTADDRESS$ -webproxy $ARG1$ -warning $ARG2$ -critical $ARG3$ -username $ARG4$ -password $ARG5$

8) Track and Report Storage Capacity Information
Command: $USER1$/Check_SANtricity_Storage_Pool_Status.py -h $HOSTADDRESS$ -webproxy $ARG1$ -warning $ARG2$ -critical $ARG3$

9) System Availability
Command: $USER1$/Check_Array_Availibility.py -h $HOSTADDRESS$ -webproxy $ARG1$ -username $ARG4$ -password $ARG5$

10) Monitor and Report Cache Hit Statistics By Volume
Command: $USER1$/Check_SANtricity_Volume_Cache_Status.py -h $HOSTADDRESS$ -mode $ARG2$ -webproxy $ARG1$ -username $ARG4$ -password $ARG5$

11) Monitor and Report Cache Hit Statistics By Volume Group
Command: $USER1$/Check_SANtricity_Volume_Group_Cache_Status.py -h $HOSTADDRESS$ -mode $ARG2$ -webproxy $ARG1$ -username $ARG4$ -password $ARG5$

The mode can have one of the two values for Cache Hit statistics by Volume and Volume Group
--> SSD -To monitor SSD Cache
--> PRC - To monitor Primary Cache

12) Thin Provisioned Volumes
Command:$USER1$/Check_SANtricity_thin_volumes.py -h $HOSTADDRESS$ -webproxy $ARG1$ -warning $ARG2$ -critical $ARG3$

13) Mel Events:
Command: $USER1$/Check_SANtricity_Mel_Events.py -h $HOSTADDRESS$ -webproxy $ARG1$

14) Monitor and track Logical Components:
Command:$USER1$/Check_SANtricity_Logical_Component.py -h $HOSTADDRESS$ -webproxy $ARG1$ -mode $ARG2$ -username $ARG4$ -password $ARG5$

The mode Value can have one of the following values:
1)DPOOL -Data Pools 2) CON: Consistency Groups
3) VOL : Volumes 4) SNP : Legacy Snapshots and PIT snap shot volumes
5) MIRV : Mirror Volumes and Asynch Mirror Volumes
6) RPR : PIT repository

All the plugins have following common parameters:
webproxy: It's IP Address:Port Number where webproxy is running
username: Username for the webproxy
password: Password for the webproxy
