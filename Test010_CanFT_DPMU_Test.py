# This script is intent to communicate to DMPU using FT2
# so externaly, FT2 shall be connected to FT1, which is 
# connected to DPMU. So communicating FT2 to DPMU, will test 
# FT2, FT1 and DPMU interface.

from ast import Bytes
import os
import subprocess
import sys
import socket
import struct
import threading
import time
import canopen

import Class_Dpmu
#import Class_SimpleCanOpen
#import Class_HostAuxDevices
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

SUPERCAPLOWVOLTAGE = 60

DC_LOAD_BENCH = 8522

can_interface = "can11" #FT1

#Result codes
RES_OK = 0
RES_ERR = 255
RES_DLG = 254
RES_NOTIMPL = 253
RES_CANERR = 252
RES_USBTOMUCH = 251
RES_USBNOTFOUND = 250

def TurnOnTestBoxResistor(plc):
    plc.setOutput(0,1)

def TurnOffTestBoxResistor(plc):
    plc.setOutput(0,0)

def TurnOnTestBox48V(plc):
    plc.setOutput(1,1)

def TurnOffTestBox48V(plc):
    plc.setOutput(1,0)

def chargeSupercap(dpmu,plc=None,bkprecision=None, ):
    try:
            
        #Charge the SuperCap
        print(">> REM >> DPMU Initiate Supercapacitor Bank Charge process")
        
        print(">> REM >> ################################################################")
        print(">> REM >> ################################################################")
        print(">> REM >> ")
        print(">> REM >>     Attention, this test takes around 90 minutes to be completed")
        print(">> REM >> ")
        print(">> REM >> ################################################################")
        print(">> REM >> ################################################################")
        time.sleep(5)
        state=dpmu.getState()
        
        if state == "PreInitialized":
            return False

        if state != "TrickleCharge":
            dpmu.setState("TrickleChargeInit")
        
        time.sleep(1)
        
        state="Charge"
        supercapVoltage=0
        stateBefore="Charge"
        supercapVoltageBefore=0
        
        while (supercapVoltage<30 or state != "Idle"):
            try:
                supercapVoltage = dpmu.GetSupercapBankVoltage()
                state=dpmu.getState()
                if supercapVoltage == None or isinstance(supercapVoltage,str):
                   supercapVoltage=supercapVoltageBefore
                if ("Exception" in state) or ("Unknown" in state):
                   state=stateBefore
                if supercapVoltageBefore != supercapVoltage or stateBefore != state:
                    supercapVoltageBefore = supercapVoltage
                    stateBefore = state
                    print(f">> REM >> Supercap Bank Voltage = {supercapVoltage}")
                    print(f">> REM >> State = {state}")   
                time.sleep(2)                
            except Exception as e:
                print(f">> REM >> Exception = {e}")
      
        print(">> REM >> DPMU Supercapacitor Bank Charge completed")
        
        return True      
    except:
        return False
    
if __name__ == "__main__":
    script_path = os.path.abspath(__file__)    
    script_directory = os.path.dirname(script_path)        
    script_name = os.path.basename(script_path)
    print(f">> REM >> Executing the {script_name} ")
    
    ret = RES_ERR    
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
        
        bk=None
        if DC_LOAD_BENCH == 8622:
            bk = Class_PLC_Devices.bk8622(0,plc,0) #(bkaddr, plc, uart number)
        elif DC_LOAD_BENCH == 8522:
            bk = Class_PLC_Devices.bk8522(0,plc,0) #(bkaddr, plc, uart number)
        else:
            bk=None

        if bk != None:
            print('>> REM >> Configuring DC LOAD BENCH')
            bk.initialize()

        TurnOffTestBoxResistor(plc)
        
        DriveVolt=adc2.getInVolt()
        print(f">> REM >> Drive Voltage = {DriveVolt}V")
        
        iop = Class_IOP.IOP_IO()             
        
        CanOpenMaster = canopen.Network()
        CanOpenMaster.connect(bustype='socketcan', channel=can_interface, bitrate=125000)
        CanOpenMaster.check()
        dpmu = Class_Dpmu.Dpmu(CanOpenMaster, 125, script_directory+"/EDS_DPMU_001.eds")
              
        
        state=dpmu.getState()
        print(f">> REM >> DPMU State = {state}")
 
        if state == "PreInitialized":
            dpmu.setState("Initialize")
            print(">> REM >> DPMU Initialized Start")
            time.sleep(5)
            state=dpmu.getState()
            print(f">> REM >> DPMU State = {state}")
            state="null"
            outVoltage = 0
            outVoltageBefore = outVoltage
            stateBefore = state
            while (outVoltage<175 or state != "Idle"):
                try:
                    if state == "TrickleCharge":
                        break
                    DriveVolt=adc2.getInVolt()
                    print(f">> REM >> Drive Voltage = {DriveVolt}V")           
                    outVoltage = dpmu.GetOutputVoltage()
                    state=dpmu.getState()
                    if ("Exception" in state):
                        state=stateBefore
                    if outVoltage == None or isinstance(outVoltage,str):
                       outVoltage=outVoltageBefore
                    elif outVoltageBefore != outVoltage or stateBefore != state:
                        print(f">> REM >> Output Voltage = {outVoltage}")
                        print(f">> REM >> DPMU State = {state}")
                        outVoltageBefore = outVoltage                  
                        stateBefore = state                          
                    time.sleep(0.5)
                except Exception as e:
                    print(f">> REM >> Exception = {e}")
        
        #the test000 initialize the DPMU and start the charge process, so check if charge has finished;
        while state != "Idle":
            state=dpmu.getState()
            time.sleep(1)

        print(">> REM >> DPMU is Initialized")
        
        if state == "Idle":
            supercapVoltage = dpmu.GetSupercapBankVoltage()
            if supercapVoltage < 74:
                if chargeSupercap(dpmu,plc,bk):
                    ret=RES_OK
                else:
                    ret=RES_CANERR
                                    
        print(">> REM >> Supercap is charged")
        
        print(">> REM >> put DPMU in regulate")
        
        dpmu.setState("RegulateInit")
        time.sleep(4)

        print('>> REM >> Reseting Configuring PLC')
        plc.ResetServer()
        plc.createCanOpenSocket()
        plc.createSocket()        
        adc1 = Class_PLC_Devices.adc(1,150000,10000,plc)
        adc2 = Class_PLC_Devices.adc(2,150000,2610,plc)
        adc3 = Class_PLC_Devices.adc(3,0,'open',plc)
        plc.setupBaud(38400,4800,500000) # uart0, uart1, CAN
        plc.setupRen(1,1)#if using LVTTL, mandatory set REN to 1  

        if bk != None:
            print('>> REM >> Configuring DC LOAD BENCH')
            bk.enableRemote()
            bk.setCcValue(6.0) #300W AC + 700W supercap
            bk.enableInput()
        else:
            TurnOnTestBoxResistor(plc) #1000W 33ohm resistor RCU Test BOX
        
        supercapVoltage = dpmu.GetSupercapBankVoltage()
        
        while supercapVoltage > SUPERCAPLOWVOLTAGE:
            try:
                supercapVoltage = dpmu.GetSupercapBankVoltage()
                outVoltage = dpmu.GetOutputVoltage()
                outCurrent = dpmu.GetOutputCurrent()
                outPower = dpmu.GetOutputPower()
                state=dpmu.getState()
                print(f">> REM >> VoltageDPMU = {outVoltage}V")
                print(f">> REM >> CurrentDPMU = {outCurrent}A")
                print(f">> REM >> PowerDPMU   = {outPower}W")
                print(f">> REM >> Supercap Voltage   = {supercapVoltage}V")
                print(f">> REM >> State = {state}")
                if bk != None:
                    try:
                        disp=bk.readInput()
                        print(f">> REM >> VoltageBK = {disp[0]}V")
                        print(f">> REM >> CurrentBK = {disp[1]}A")
                        print(f">> REM >> PowerBK   = {disp[2]}W")
                    except Exception as e:
                         print(f">> REM >> BK Exception {e}")
                supercapVoltage = dpmu.GetSupercapBankVoltage()
                time.sleep(1)                
            except Exception as e:
                print(f">> REM >> BK Exception {e}")
        
        if bk != None:
            bk.disableInput()
            bk.setCcValue(3)

        TurnOffTestBoxResistor(plc)   

        dpmu.setState("Idle")

        plc.closeSocket()
        plc.closeSocketCanOpen()
        ret = RES_OK
        
    except Exception as e:
        print(f">> REM >> An error occurred: {str(e)}" )
        ret=RES_CANERR

    finally:
        if CanOpenMaster:
            CanOpenMaster.disconnect()
            del CanOpenMaster
        dpmu = None
        print(f">> REM >> Finished exceuting the {script_name} " )
        sys.exit(ret)