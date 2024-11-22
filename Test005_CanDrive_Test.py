import os
import subprocess
import sys
import time
import struct
import socket

import Class_IOP
import Class_PLC_Devices


if len(sys.argv) != 3:
    print("Usage: python client.py <server_ip> <server_port>")
    sys.exit(1)

# Get command-line arguments
host = sys.argv[1]
print(">> REM >> arg host ip=" + host)
port = int(sys.argv[2])
print(">> REM >> arg port=" + str(port))

#Result codes
RES_OK = 0
RES_ERR = 255
RES_DLG = 254
RES_NOTIMPL = 253
RES_CANERR = 252
RES_USBTOMUCH = 251
RES_USBNOTFOUND = 250


if __name__ == "__main__": 
    # Get the full path to the current script
    script_path = os.path.abspath(__file__)
    
    # Extract just the filename from the path
    script_name = os.path.basename(script_path)
    
    print(">> REM >> Executing the : ", script_name)
    ret = RES_ERR
    
##### Start your code
    try:        
        #os.system("ifconfig eth1 10.11.201.2 netmask 255.255.255.0 up")
        #os.system("ethtool -s eth1 autoneg off speed 10 duplex full")
        #time.sleep(3)
        print('>> REM >> Initializing and Configuring PLC')
        plc = Class_PLC_Devices.plc()
        #plc.SendFile("Class_PLC_Server.py","Class_PLC_Server.py")
        #plc.SendFile("Class_boot_withImportServer.py","boot.py")
        plc.ResetServer()
        plc.createCanOpenSocket()
        plc.createSocket()        
        adc1 = Class_PLC_Devices.adc(1,150000,10000,plc)
        adc2 = Class_PLC_Devices.adc(2,150000,2610,plc)
        adc3 = Class_PLC_Devices.adc(3,0,'open',plc)
        plc.setupBaud(38400,4800,500000) # uart0, uart1, CAN
        plc.setupRen(1,1)#if using LVTTL, mandatory set REN to 1  
        

        canIop = Class_IOP.SocketCan("can13")
        data2transmit = bytes([0x01, 0x02, 0x03, 0x04])
        cob_id = 0x618
        print('>> REM >> Send cmd to PLC to Send CAN Data')
        plc.queryCan(0,0x618,data2transmit)
        ret=RES_CANERR
        print('>> REM >> Receiving CAN Data from IOP')
        cob_idRx, dataRx = canIop.read()
        
        if ((cob_idRx==cob_id) and (dataRx==data2transmit)):
            print(">> REM >> CAN Test - OK")
            ret=RES_OK
        else:
            ret=RES_CANERR
            
        plc.closeSocket()
        plc.closeSocketCanOpen()
        
    except Exception as e:
        ret=RES_CANERR  

##### Finish your code
    print(">> REM >> Finished exceuting the : ", script_name)
    sys.exit(ret)
