import os
from pickle import FALSE
import subprocess
import sys
import time

import Class_IOP

#if len(sys.argv) < 3:
#    print("Usage: python client.py <server_ip> <server_port> <serNumber> <side>")
#    sys.exit(1)

# Get command-line arguments
#host = sys.argv[1]
#print(">> REM >> arg host ip=" + host)
#port = int(sys.argv[2])
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
        # iop = Class_IOP.IOP_IO()
        # iop.SetBe(1)
        # print(str(iop.GetIOG()))
        
        # Create an I2CBus instance
        i2c_bus = Class_IOP.I2CBus(0)
        #print(">> REM >> Created the I2C bus instance")        
        #create Housekeeping IOP
        hkIop = Class_IOP.IOP_Housekeeping(i2c_bus,0x28)
        #print(">> REM >> Created the iop housekeeping")
        #create Temperature IOP
        TempIop = Class_IOP.IOP_Temperature(i2c_bus,0x48)
        #print(">> REM >> Created the iop temperature")
        
        hkIop.Configure()
        TempIop.Configure()
        
        print(">> REM >> 24V In1 (V) = " + str(hkIop.get24V1()))
        print(">> REM >> 24V In2 (V) = " + str(hkIop.get24V2()))
        print(">> REM >> Current (A) = " + str(hkIop.getCurrent()))
        print(">> REM >> 1.1V    (V) = " + str(hkIop.get1V1()))
        print(">> REM >> 1.35V   (V) = " + str(hkIop.get1V35()))
        print(">> REM >> 2.5V    (V) = " + str(hkIop.get2V5()))
        print(">> REM >> 3.3V    (V) = " + str(hkIop.get3V3()))
        print(">> REM >> 5.0V    (V) = " + str(hkIop.get5V0()))

        print(">> REM >> Temperature(Celsius) = " + str(TempIop.GetTemp()))

        ret=RES_OK

    except Exception as e:
        ret=RES_CANERR
        
    finally:
        ##### Finish your code
        print(">> REM >> Finished exceuting the : ", script_name)
        sys.exit(ret)