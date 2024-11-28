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

possibleCommands = ["init", "initialize","idle","fault","charge","reg","regulate", "end", "rf", "resetFlash"]

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
    print(f"******** DPMU VARS {ts} ********")
    print(f"\tState:[{dpmuState}]")
    print(f"\tOutputCurrent:[{outputCurrent}]")
    print(f"\tBusVoltage:[{dpmuBusVoltage}]")
    print(f"\tSupercapVoltage:[{supercapVoltage}]")
    print(f"\tInputCurrent:[{inputCurrent}], InputPower:[{inputPower}]")
    print(f"\t{switches}")
    print("******** DPMU VARS END ********")
    
def ReadCmdLineSequence():
    print(f"Received args:[{sys.argv}]")
    nrOfargs = len(sys.argv)
    if( nrOfargs < 2 ):
        return ["end", 0]
    else:
        commandList=list()
        argList = sys.argv[1:]
        idx=0
        while ( idx < len(argList) ):
            command = argList[idx]
            print(f"Validating arg[{idx}]:{command}")
            if( command in possibleCommands ):
                match command:
                    case  "end":
                        commandList.append([command, 0])
                    case "resetFlash" | "rf":
                        commandList.append([command, 16])
                    case "init" | "initialize"  | "fault" | "charge" | "reg" | "regulate" | "idle":
                        if( (idx+1) < len(argList) ):
                            idx = idx + 1
                            try: 
                                print(f"Convert {argList[idx]} to int")
                                timeCommand = int( argList[idx] )
                                commandList.append( [command, timeCommand] )
                            except Exception as e:
                                print(f"Erro converting {argList[idx]} to integer. {e}")
                                commandList.append( [command, 0] )
                                continue
                    case _:
                        print(f"Argument[{idx}] = {command} invalid")
            idx = idx + 1
        commandList.append(["end", 0])
        return commandList

def abend():
    print(f"Command {command} not valid. Aborting.\r\nValid commands are")
    print("init [time] | initialize [time] | fault [time] | end | charge [time] | reg [time] | regulate [time] | idle [time] | resetFlash")
    print("time in seconds eg: 2.1 secs ")
    sys.exit(0)

def selectSMStateFromCommand(command):
    commandStr=str(command)
    match commandStr.lower():
        case "init" | "initialize":
            return "Initialize"
        case "idle":
            return "Idle"
        case "fault":
            return "Fault"        
        case "charge" | "chg":
            return "Charge"
        case "reg" | "regulate":
            return "RegulateInit"
        case "end":
            return "EndSM"
        case "resetflash" | "rf":
            return "ResetFlash"
        case _:
            return "EndSM"


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
    
    for i in range(0, 10):
        print(f"Trying init DPMU Class:[{i}]")
        dpmu = Class_Dpmu.Dpmu(CanOpenMaster, 125, script_directory+"/EDS_DPMU_001.eds")
        print(f"dpmu.initialized={dpmu.initialized}")
        if( dpmu.initialized == True):
            break
    
    dpmuSerialNumberStr = dpmu.GetSerialNumber()
    print( f"DPMU SN: {dpmuSerialNumberStr}" )

    dpmu.getState()
    prState = "InitSM"
    nxState = "InitSM"
    endProcess = False
    listOfCommands = ReadCmdLineSequence()
    print(f"listOfCommands:\r\n{listOfCommands}")
    commandIndex = 0

    while( endProcess == False ):
        
        dpmu_state = dpmu.getState()
        
        match prState:
            case "InitSM":
                dpmu.printVariables()
                nxState = "ForceFault"
                
            case "ForceFault":
                dpmu.setState("Fault")
                countTime=2 
                expectedDPMUStateList=["Idle", "PreInitialized"]            
                nxStateAfterWaitDPMUState="ProcessCommandLine"
                nxState="WaitDPMUState"

            case "ProcessCommandLine":
                if( commandIndex < len(listOfCommands) ): 
                    command = listOfCommands[commandIndex][0]
                    commandTime = listOfCommands[commandIndex][1]
                    commandIndex = commandIndex + 1
                    nxState = selectSMStateFromCommand( command )
                else:
                    nxState = "EndSM"
                print(f"========== ProcessCommandLine ===========")
                print(f"\t\tcommandindex:[{commandIndex}] len(listOfCommands){len(listOfCommands)}")
                print(f"\t\tcommand:[{command}] commandTime:{commandTime}")
                print(f"\t\tnxState:[{nxState}]")
                
            case "Initialize":
                dpmu.InitialConfig()
                countTime = 5
                nxStateAfterWaitDPMUState="RequestInitializeDPMU"
                nxState="WaitDPMUState"

            case "RequestInitializeDPMU":    
                dpmu.setState( "Initialize")
                countTime = commandTime * 10
                expectedDPMUStateList=["Idle", "PreInitialized"]            
                nxStateAfterWaitDPMUState="ProcessCommandLine"
                nxState="WaitDPMUState"

            case "Charge":
                dpmu.setState("TrickleChargeInit")
                countTime = commandTime * 10
                if( commandTime > 0):
                    expectedDPMUStateList=["Charge", "Idle", "PreInitialized"]
                else:
                    expectedDPMUStateList=["Idle", "PreInitialized"]
                nxStateAfterWaitDPMUState="ProcessCommandLine"
                nxState="WaitDPMUState"

            case "Regulate":
                dpmu.setState("RegulateInit")
                countTime = commandTime * 10
                if( commandTime > 0):
                    expectedDPMUStateList=["Regulate", "RegulateVoltage"]
                else:
                    expectedDPMUStateList=["Idle", "PreInitialized"]
                nxStateAfterWaitDPMUState="ProcessCommandLine"
                nxState="WaitDPMUState"

            case "Idle":
                dpmu.setState("Idle")
                countTime = commandTime * 10
                expectedDPMUStateList=["Idle", "PreInitialized"]
                nxStateAfterWaitDPMUState="ProcessCommandLine"
                nxState="WaitDPMUState"

            case "Fault":
                dpmu.setState("Fault")
                countTime = commandTime * 10
                expectedDPMUStateList=["PreInitialized"]
                nxStateAfterWaitDPMUState="ProcessCommandLine"
                nxState="WaitDPMUState"

            case "ResetFlash":
                dpmu.ResetFlashCanLog()
                print("Stop state machine for wait 8 seconds")
                time.sleep(8)
                countTime = commandTime * 10
                expectedDPMUStateList=["Idle", "PreInitialized"]
                nxStateAfterWaitDPMUState="ProcessCommandLine"
                nxState="WaitDPMUState"

            case "WaitDPMUState":
                if( countTime > 0): 
                    countTime = countTime - 1
                else:
                    if( dpmu_state in expectedDPMUStateList ):                   
                        nxState=nxStateAfterWaitDPMUState

            case "EndSM":
                if( countTime > 0):
                    countTime = countTime - 1
                else:
                    dpmu.printVariables()
                    endProcess = True
    
            case _:
                nxState = "InitSM"
    
        time.sleep(0.1)
        if( prState != nxState ):
            print(f"========= present state[{prState}]")
            logVars()
            print(f"========= next state[{nxState}]\r\n")
        prState = nxState

    print("====== DPMU internal log download")
    dateTimeNow = dt.datetime.now()
    root_file_name = "DPMU_CAN_LOG_" + dpmuSerialNumberStr+ "_" + dateTimeNow.strftime("%Y%m%d_%H%M%S") 
    dpmu_log_hex_file_name = root_file_name + ".hex"
    dpmu.CanLogTransfer( dpmu_log_hex_file_name )

    sys.exit()
