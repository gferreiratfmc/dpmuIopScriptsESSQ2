import os
import subprocess
import sys
import time
import struct
import socket
import Class_Dpmu
import canopen
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
    script_path = os.path.abspath(__file__)    
    script_name = os.path.basename(script_path)
    script_directory = os.path.dirname(script_path) 
    print(">> REM >> Executing the : ", script_name)
    ret = RES_OK
    can_interface = "can11" #FT1
           

    
##### Start your code
    try:
        #os.system("ifconfig eth1 10.11.201.2 netmask 255.255.255.0 up")
        #os.system("ethtool -s eth1 autoneg off speed 10 duplex full")
        #time.sleep(3)    

        #CanOpenMaster = Class_SimpleCanOpen.CANopenMaster(can_interface)
        #dpmu = Class_Dpmu.Dpmu(CanOpenMaster, 125, script_directory+"/EDS_DPMU_001_mod.eds")
        
        CanOpenMaster = canopen.Network()
        CanOpenMaster.connect(bustype='socketcan', channel=can_interface, bitrate=125000)
        CanOpenMaster.check()
        
        dpmu = Class_Dpmu.Dpmu(CanOpenMaster, 125, script_directory+"/EDS_DPMU_001.eds")      
        del dpmu
        if CanOpenMaster:
            CanOpenMaster.disconnect()
            del CanOpenMaster
                
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
                
        iop = Class_IOP.IOP_IO()

        #TX interface
        cantx = Class_IOP.SocketCan("can12")
        #RX interface
        canrx = Class_IOP.SocketCan("can11")
        cob_id = 0x618
        data2transmit = bytes([0x01, 0x02, 0x03, 0x04])
        print('>> REM >> Forcing Fault on CAN FT')
        plc.setOutput(2,0)           
        print('>> REM >> Cmd IOP to transmit via CAN11')
        cantx.write(cob_id,data2transmit)
        print('>> REM >> Cmd IOP to receive via CAN12')
        cob_idRx, dataRx = canrx.read()
        errorFlag1_0=iop.GetCan11err()
        errorFlag2_0=iop.GetCan12err()
        if ((cob_idRx==cob_id) and (dataRx==data2transmit)):
            print(">> REM >> CAN Test - OK")
            print(f">> REM >> Error Flag FT1 = {errorFlag1_0}")
            print(f">> REM >> Error Flag FT2 = {errorFlag2_0}")
        else:
            ret=RES_ERR
        print('>> REM >> Removing Fault on CAN FT')
        plc.setOutput(2,1)   
        print('>> REM >> Cmd IOP to transmit via CAN11')
        cantx.write(cob_id,data2transmit)
        print('>> REM >> Cmd IOP to receive via CAN12')
        cob_idRx, dataRx = canrx.read()
        errorFlag1_1=iop.GetCan11err()
        errorFlag2_1=iop.GetCan12err()
        if ((cob_idRx==cob_id) and (dataRx==data2transmit)):
            print(">> REM >> CAN Test - OK")
            print(f">> REM >> Error Flag FT1 = {errorFlag1_1}")
            print(f">> REM >> Error Flag FT2 = {errorFlag2_1}")
        else:
            ret=RES_ERR
            
        if (errorFlag1_0 + errorFlag2_0)!=(errorFlag1_1 + errorFlag2_1):
            print(">> REM >> CAN Fault Flag - OK")
        else:
            ret=RES_ERR
            
        plc.closeSocket()
        plc.closeSocketCanOpen()   
        
    except Exception as e:
        ret=RES_CANERR

##### Finish your code
    print(">> REM >> Finished exceuting the : ", script_name)
    sys.exit(ret)
