import os
import subprocess
import sys
import time
import Class_I2C_Mem

if len(sys.argv) != 3:
    print("Usage: python client.py <server_ip> <server_port> <serNumber> <side>")
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

    dir_name = os.path.dirname(script_path)
    
    print(">> REM >> Executing the : ", script_name)

##### Start your code

    # Create an I2CBus Memory
    mem = Class_I2C_Mem.I2CMem(1,50)
    
    ret=RES_ERR
    parRead = mem.read("name").replace('\r','').replace('\n','')
    parNo = mem.read("partno").replace('\r','').replace('\n','')
    parRev = mem.read("partrev").replace('\r','').replace('\n','')
    serNumber = mem.read("serialno").replace('\r','').replace('\n','')
    side = mem.read("side").replace('\r','').replace('\n','')
    print(f">> REM >> PN={parNo}")
    print(f">> REM >> REV={parRev}")
    print(f">> REM >> SN={serNumber}")
    print(f">> REM >> SIDE={side}")

   
    print(f">> REM >> Write name BPRVC and read {parRead}")
    if (("BPRVC") in (parRead)):
        ret=RES_OK
    else:
        ret=RES_ERR
 
##### End your code

    print(f">> REM >> Finished exceuting the {script_name} with code {ret}")
    sys.exit(ret)