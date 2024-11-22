import os
from pickle import FALSE
import subprocess
import sys
import time

import Class_IOP
import Class_FE_Psu

if len(sys.argv) != 3:
    print("Usage: python client.py <server_ip> <server_port> <serNumber> <side>")
    sys.exit(1)

# Get command-line arguments
host = sys.argv[1]
#print(">> REM >> arg host ip=" + host)
port = int(sys.argv[2])
#print(">> REM >> arg port=" + str(port))

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
    dir_name = os.path.dirname(script_path)
    print(">> REM >> Executing the : ", script_name)
    ret = RES_ERR
    ##### Start your code
    try:
        iopIo = Class_IOP.IOP_IO()
        # Create an I2CBus instance
        i2c_bus = Class_IOP.I2CBus(3)
        #create a PSU instance
        print(">> REM >> Creating PSU instance")
        psu = Class_FE_Psu.FrontEndPSU(i2c_bus,0x4c)
        print(">> REM >> Configure PSU ADC") 
        psu.Configure()
        psu.Configure()
        psu.Configure()
        print(">> REM >> Waiting 8 seconds to get the ADC ready")
        time.sleep(8)
        print(f">> REM >> Reading ADC...") 
        print(f">> REM >> Output Current(A) = {str(psu.GetIOut())}")
        print(f">> REM >> Output Voltage(V) = {str(psu.GetVOut())}")
        print(f">> REM >> NTC Temperature(Celsius) = {str(psu.GetNtcTemp())}")
        print(f">> REM >> Internal Temperature(Celsius) = {str(psu.GetIntTemp())}")
        print(f">> REM >> Internal 5Vcc(V) = {str(psu.GetVcc())}")
        print(f">> REM >> IOG = {psu.GetIOG()}")
        print(f">> REM >> Output Status = {psu.GetVoutStatus()}")
        ioIOG = iopIo.GetIOG()
        strIOP_IOG=""
        if ioIOG==1:
            strIOP_IOG="Good"
        else:
            strIOP_IOG="Bad"
        print(f">> REM >> IOG read via IOP IO = {strIOP_IOG}")
        if strIOP_IOG==psu.GetIOG():
            ret=RES_OK
            print(f">> REM >> IOG Test finished OK")
        ret=RES_CANERR        
        if (psu.GetVOut()> 44) and (psu.GetVoutStatus()=="Good"):
            ret=RES_OK

    except Exception as e:
        ret=RES_CANERR
        
    finally:
        ##### Finish your code
        print(">> REM >> Finished exceuting the : ", script_name)
        sys.exit(ret)


