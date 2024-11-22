from ast import Bytes
import os
import subprocess
import sys
import socket
import struct
import threading
import time
import math
import canopen

#import Class_SimpleCanOpen

class Dpmu:
    
    statesStr2Int={
"Idle"						: 0,
"Initialize"				: 1,
"SoftstartInitDefault"		: 2,
"Softstart"					: 3,
"TrickleChargeInit"			: 4,
"TrickleChargeDelay"		: 5,
"TrickleCharge"				: 6,
"ChargeInit"				: 7,
"Charge"					: 8,
"ChargeStop"				: 9,
"ChargeConstantVoltageInit"	: 10,
"ChargeConstantVoltage"		: 11,
"RegulateInit"				: 12,
"Regulate"					: 13,
"RegulateStop"				: 14,
"RegulateVoltageInit"		: 140,
"RegulateVoltage"			: 141,
"RegulateVoltageStop"		: 142,
"Fault"						: 15,
"FaultDelay"				: 16,
"BalancingInit"				: 18,
"Balancing"					: 19,
"BalancingStop"				: 191,
"CC_Charge"					: 20,
"SoftstartInitRedundant"	: 201,
"StopEPWMs"					: 21,
"ChargeRamp"				: 22,
"PreInitialized"			: 255
        }
    
    statesInt2Str={
0   :   "Idle",			
1   :   "Initialize",
2   :   "SoftstartInitDefault",
3   :   "Softstart",
4   :   "TrickleChargeInit",
5   :   "TrickleChargeDelay",
6   :   "TrickleCharge",
7   :   "ChargeInit",
8   :   "Charge",
9   :   "ChargeStop",
10  :   "ChargeConstantVoltageInit",
11  :   "ChargeConstantVoltage",
12  :   "RegulateInit",
13  :   "Regulate",
14  :   "RegulateStop",
140 :   "RegulateVoltageInit",
141 :   "RegulateVoltage",
142 :   "RegulateVoltageStop",
15  :   "Fault",
16  :   "FaultDelay",
18  :   "BalancingInit",
19  :   "Balancing",
191 :   "BalancingStop",
20  :   "CC_Charge",
201 :   "SoftstartInitRedundant",
21  :   "StopEPWMs",
22  :   "ChargeRamp",
255 :   "PreInitialized"			     
        }

    node = None
    network = None
    
    def __init__(self,canMaster,canId, edsFile):
        try:
            self.network = canMaster
            self.node = canopen.BaseNode402(canId, edsFile)
            self.network.add_node(self.node)
            
            #self.node = canopen.Node(canMaster, canId, edsFile)
            self.node.sdo["Consumer Heartbeat Time"]["Consumer Heartbeat Time"].raw=0
            self.node.sdo["Producer Heartbeat Time"].raw=0
            self.InitialConfig()
        except Exception as e:
            print(f">> REM >> Exception creating DPMU instance {e}")
    
    def InitialConfig(self):
        try:
            node = self.node
            print(">> REM >> DPMU - Seting Initial Configuration variables")     
            node.sdo["Date_And_Time"].raw=int( time.time() ) #0x66576fae
            node.sdo["DPMU_Power_Source_Type"].raw=0 #set default mode
            node.sdo["Power_Budget_DC_Input"]["Available_Power_Budget_DC_Input"].raw=300
            node.sdo["Maximum_Allowed_Load_Power"].raw=1000
            node.sdo["ESS_Current"].raw=0x20
            node.sdo["Energy_Cell_Summary"]["Max_Voltage_Energy_Cell"].raw=0x30
            node.sdo["Energy_Cell_Summary"]["Min_Voltage_Energy_Cell"].raw=0x10        
            node.sdo["Energy_Bank_Summary"]["Max_Voltage_Applied_To_Energy_Bank"].raw=88
            node.sdo["Energy_Bank_Summary"]["Constant Voltage Threshold"].raw=90
            node.sdo["Energy_Bank_Summary"]["Min_Voltage_Applied_To_Energy_Bank"].raw=60
            node.sdo["Energy_Bank_Summary"]["Preconditional Threshold"].raw=30
            node.sdo["Energy_Bank_Summary"]["Safety_Threshold_State_of_Charge"].raw=30
            node.sdo["DC_Bus_Voltage"]["Max_Allowed_DC_Bus_Voltage"].raw=193
            node.sdo["DC_Bus_Voltage"]["Target_Voltage_At_DC_Bus"].raw=180
            node.sdo["DC_Bus_Voltage"]["Min_Allowed_DC_Bus_Voltage"].raw=167
            node.sdo["DC_Bus_Voltage"]["VDC_Bus_Short_Circuit_Limit"].raw=30      
            node.sdo["Temperature"]["DPMU_Temperature_Max_Limit"].raw=85
            node.sdo["Temperature"]["DPMU_Temperature_High_Limit"].raw=70
            #self.printVariables()            
        except Exception as e:
            return f">> REM >> Exception Initial Configuration {e}"   
        
    # def ResetFlashCanLog(self):
    #     node.sdo["CAN_LOG"]["CAN_LOG_RESET"].raw=1
    #     print("Reseting CAN log - waiting 16 seconds")
    #     time.sleep(16.0)

    def CanLogTransfer(self, outputFileName):
        try:
           
            node = self.node
            print("START DPMU LOG DOWNLOADING")
            
            #node.sdo["CAN_LOG"]["CAN_LOG_READ"].raw
            print("OPEN SDO DOMAIN TRANSFER CAN_LOG - READ SDO DOMAIN TRANSFER")
            I_CAN_LOG=0x4011
            S_CAN_LOG_READ=1
            dpmuCanLogReader = node.sdo.open(I_CAN_LOG, subindex=S_CAN_LOG_READ, 
                                             mode='rb', encoding='ascii', 
                                             buffering=1024, size=None, 
                                             block_transfer=True, force_segment=True, 
                                             request_crc_support=False)
            print("Open output file " + outputFileName )
            outfile = open(outputFileName, mode= 'wb')
            count=0
            print("Downloading data from DPMU")
            progressCount = 0
            while (True):
                data = dpmuCanLogReader.read(7)
                count=count+1
                if( count == 700):
                    progressCount=progressCount+1
                    print( f"{progressCount} ", end='')
                    sys.stdout.flush() 
                    count=0
                if not data:
                    print("\r\nDone")
                    break
                outfile.write(data)
            print("Closing file " + outputFileName)
            outfile.flush()
            outfile.close()
            dpmuCanLogReader.close()
        except Exception as e:
            print(f">> REM >> Exception raised while in transfering DPMU Log: {e}")
            return e
        
    

    def printVariables(self):
        try:
            node = self.node
            print(">> REM >> Printing Variables:")
            temp = node.sdo["DPMU_Power_Source_Type"].raw
            print(f"DPMU_Power_Source_Type={temp}")
            temp = node.sdo["Power_Budget_DC_Input"]["Available_Power_Budget_DC_Input"].raw
            print(f"Available_Power_Budget_DC_Input={temp}")
            temp = node.sdo["Maximum_Allowed_Load_Power"].raw
            print(f"Maximum_Allowed_Load_Power={temp}")        
            temp = node.sdo["ESS_Current"].raw
            print(f"ESS_Current={temp}")
            temp = node.sdo["Energy_Cell_Summary"]["Max_Voltage_Energy_Cell"].raw
            print(f"Max_Voltage_Energy_Cell={temp}")
            temp = node.sdo["Energy_Cell_Summary"]["Min_Voltage_Energy_Cell"].raw
            print(f"Min_Voltage_Energy_Cell={temp}")
            temp = node.sdo["Energy_Bank_Summary"]["Max_Voltage_Applied_To_Energy_Bank"].raw
            print(f"Max_Voltage_Applied_To_Energy_Bank={temp}")
            temp = node.sdo["Energy_Bank_Summary"]["Constant Voltage Threshold"].raw
            print(f"Constant Voltage Threshold={temp}")
            temp = node.sdo["Energy_Bank_Summary"]["Min_Voltage_Applied_To_Energy_Bank"].raw
            print(f"Min_Voltage_Applied_To_Energy_Bank={temp}")
            temp = node.sdo["Energy_Bank_Summary"]["Preconditional Threshold"].raw
            print(f"Preconditional Threshold={temp}")
            temp = node.sdo["Energy_Bank_Summary"]["Safety_Threshold_State_of_Charge"].raw
            print(f"Safety_Threshold_State_of_Charge={temp}")
            temp = node.sdo["DC_Bus_Voltage"]["Max_Allowed_DC_Bus_Voltage"].raw
            print(f"Max_Allowed_DC_Bus_Voltage={temp}")
            temp = node.sdo["DC_Bus_Voltage"]["Target_Voltage_At_DC_Bus"].raw
            print(f"Target_Voltage_At_DC_Bus={temp}",)
            temp = node.sdo["DC_Bus_Voltage"]["Min_Allowed_DC_Bus_Voltage"].raw
            print(f"Min_Allowed_DC_Bus_Voltage={temp}")
            temp = node.sdo["DC_Bus_Voltage"]["VDC_Bus_Short_Circuit_Limit"].raw
            print(f"VDC_Bus_Short_Circuit_Limit={temp}")
            temp=node.sdo["Temperature"]["DPMU_Temperature_Max_Limit"].raw
            print(f"DPMU_Temperature_Max_Limit={temp}")
            temp=node.sdo["Temperature"]["DPMU_Temperature_High_Limit"].raw     
            print(f"DPMU_Temperature_High_Limit={temp}")
        except Exception as e:
            return f">> REM >> Exception print DPMU variables {e}"   

        
    def setState(self,stateStr):
        try:
            print(f">> REM >> DPMU Set State {stateStr}")
            node=self.node
            node.sdo["DPMU_State"]["DPMU Operation Request State"].raw=self.statesStr2Int[stateStr]
        except Exception as e:
            return f">> REM >> DPMU Exception Set State {e}"   

    
    def getState(self):
        stateStr = "Unknown State"
        state = 0
        try:
            state = self.node.sdo["DPMU_State"]["DPMU Operation Current State"].raw
            stateStr = self.statesInt2Str[state]
            return stateStr
        except:
            return f"Exception getState {stateStr}={state}"

    def getDeviceType(self):
        try:
            return self.node.sdo["Device Type"].raw
        except Exception as e:
            return f"Exception getDeviceType {e}"          
        
    def getIdentity(self):
        try:
            return self.node.sdo["Identity Object"]["Product Code"].raw
        except Exception as e:
            return f"Exception getIdentity {e}"          
        
    def GetSupercapBankVoltage(self):
        try:
            maxVoltageEnergyBank = self.node.sdo["Energy_Bank_Summary"]["Max_Voltage_Applied_To_Energy_Bank"].raw
            value = self.node.sdo["Energy_Bank_Summary"]["State_of_Charge_of_Energy_Bank"].raw
            value = value / 2
            currentVStoreRatio = math.sqrt(value/100.0)
            calcSupercapVoltage = 0.8733 * maxVoltageEnergyBank *  currentVStoreRatio
            return calcSupercapVoltage
        except Exception as e:
            return f"Exception GetSupercapBankVoltage {e}"
            
    def GetOutputVoltage(self):
        try:
            return self.node.sdo["Read_Power"]["Read_Voltage_At_DC_Bus"].raw
        except Exception as e:
            return f"Exception GetOutputVoltage {e}"

    def GetOutputVoltage(self):
        try:
            return self.node.sdo["Read_Power"]["Read_Voltage_At_DC_Bus"].raw
        except Exception as e:
            return f"Exception GetOutputVoltage {e}"        

    def GetOutputCurrent(self):
        try:
            count = self.node.sdo["Read_Power"]["Read_Load_Current"].raw
            if (count & (1 << (7))) != 0: # if sign bit is set e.g., 8bit: 128-255
                count = count - (1 << 8)        # compute negative value
            loadCurrent = float(count) / 16.0        
            return loadCurrent
        except Exception as e:
            return f"Exception GetOutputCurrent {e}"   
        
    def GetOutputPower(self):
        try:
            return self.node.sdo["Read_Power"]["Power_From_DC_Input"].raw
        except Exception as e:
            return f"Exception GetOutputPower {e}"
        
    def GetSwitchesState(self):
        switchList=[]
        try:
            switchList.append(["QSB", self.node.sdo["Switch_State"]["SW_Qsb_State"].raw])
            switchList.append(["QLB", self.node.sdo["Switch_State"]["SW_Qlb_State"].raw])
            switchList.append(["QINB", self.node.sdo["Switch_State"]["SW_Qinb_State"].raw])
            switchList.append(["Qinrush", self.node.sdo["Switch_State"]["SW_Qinrush_State"].raw])
        except Exception as e:
            pass
        return switchList
        
if __name__ == "__main__":
    print(">> REM >> This is a class file, execution could be performed, but no effect for FAT")
    sys.exit(0)