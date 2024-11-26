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
import datetime as dt


def logVars():
    dateTimeNow = dt.datetime.now()
    ts = dateTimeNow.strftime("%Y%m%d_%H%M%S.%f")
    outputCurrent = dpmu.GetOutputCurrent()
    dpmuBusVoltage = dpmu.GetOutputVoltage()
    supercapVoltage = dpmu.GetSupercapBankVoltage()
    inputPower = dpmu.GetInputPower() 
    #inputCurrent = float(inputPower) / dpmuBusVoltage
    inputCurrent = float(inputPower)
    dpmuState = dpmu.getState()
    switches=dpmu.GetSwitchesState()
    print(f"\r\n******** DPMU VARS {ts} ********")
    print(f"\tState:[{dpmuState}]")
    print(f"\tOutputCurrent:[{outputCurrent}]")
    print(f"\tBusVoltage:[{dpmuBusVoltage}]")
    print(f"\tSupercapVoltage:[{supercapVoltage}]")
    print(f"\tInputCurrent:[{inputCurrent}], InputPower:[{inputPower}]")
    print(f"\t{switches}")
    print("******** DPMU VARS END ********\r\n")
    
def ReadCmdLineSequence():
    if( len(sys.argv) < 1 ):
        pass


if __name__ == "__main__":
    script_path = os.path.abspath(__file__)    
    script_directory = os.path.dirname(script_path)        
    script_name = os.path.basename(script_path)
    print(f">> REM >> Executing the {script_name} ")

    can_interface = "can11" #FT1

    CanOpenMaster = canopen.Network()
    
    pc_can_number = "0"
    iop_can_interface_number1 = "can11" #FT1
    iop_can_interface_number2 = "can12" #FT2

    for canInfo in [['kvaser', pc_can_number], ['socketcan', iop_can_interface_number2]]:
        try:
            canInterfaceFound="None"
            busDriver=canInfo[0]
            can_interface = canInfo[1]    
            print(f"Try to connect to CAN bus driver {busDriver} fnterface:{can_interface}")
            CanOpenMaster.connect(bustype=busDriver, channel=can_interface, bitrate=125000)
            #CanOpenMaster.connect(bustype=busDriver, channel=can_interface, bitrate=250000)
            CanOpenMaster.check()
            canInterfaceFound=busDriver
            print(f"CAN bus driver {busDriver} found!")
            break
        except Exception as ex:
            print(f"Could not find {busDriver} driver. Excepiton {ex}")
    # CanOpenMaster.connect(bustype='socketcan', channel='can12', bitrate=125000)
    # CanOpenMaster.check()
    # canInterfaceFound = "socketcan"
    if( canInterfaceFound=="None" ):
            print(f"Could not find any can bus driver exiting script.")
            sys.exit(-1)
    
    for i in range(0, 10000):
        print(f"Trying init DPMU Class:[{i}]")
        dpmu = Class_Dpmu.Dpmu(CanOpenMaster, 125, script_directory+"/EDS_DPMU_001.eds")
        print(f"dpmu.initialized={dpmu.initialized}")
        if( dpmu.initialized == True):
            break
        time.sleep(0.1)

    listOfStatesSequence = ReadCmdLineSequence()

    dpmu.getState()
    prState = "InitSM"
    nxState = "InitSM"
    endProcess = False
    while( endProcess == False ):
        
        dpmu_state = dpmu.getState()
        logVars()
        match prState:
            case "InitSM":
                dpmu.printVariables()
                dpmu.setState("Fault")
                nxState = "WaitDPMUPreInitialized"
                    
            case "WaitDPMUPreInitialized":
                if( dpmu_state == "PreInitialized" ):
                    dpmu.InitialConfig()
                    dpmu.setState("Initialize")
                    countTime = 0
                    nxState = "PrintDPMUVars"
            
            case "PrintDPMUVars":
                if( countTime < 5): 
                    countTime = countTime + 1
                else:
                    countTime=0
                    if( dpmu_state == "Idle" or dpmu_state == "PreInitialized"):                   
                        nxState="ForceFault"
            
            case "ForceFault":
                dpmu.setState("Fault")
                nxState="EndSM"
                countTime=0

            case "EndSM":
                if( countTime < 5):
                    countTime = countTime + 1
                else:
                    dpmu.printVariables()
                    endProcess = True
            case _:
                nxState = "InitSM"
    
        time.sleep(0.5)
        if( prState != nxState ):
            print(f"========= prState[{prState}] => nxState[{nxState}]")
        prState = nxState

    print("====== DPMU internal log download")
    dateTimeNow = dt.datetime.now()
    root_file_name = "DPMU_CAN_LOG_" + dateTimeNow.strftime("%Y%m%d_%H%M%S") 
    dpmu_log_hex_file_name = root_file_name + ".hex"
    dpmu.CanLogTransfer( dpmu_log_hex_file_name )

    sys.exit()
