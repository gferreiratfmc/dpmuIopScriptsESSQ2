import os
import subprocess
import sys
import time
import struct
import socket

import Class_IOP

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
        
        iop = Class_IOP.IOP_IO()

        #TX interface
        cantx = Class_IOP.SocketCan("can13")

        
        #RX interface
        canrx = Class_IOP.SocketCan("can9")

        cob_id = 0x618
        data2transmit = bytes([0x01, 0x02, 0x03, 0x04])
        
        cantx.write(cob_id,data2transmit)
        cob_idRx, dataRx = canrx.read()
        if ((cob_idRx==cob_id) and (dataRx==data2transmit)):
            print(">> REM >> CAN Test - OK")
            ret=RES_OK
        
    except Exception as e:
        ret=RES_CANERR

##### Finish your code
    print(">> REM >> Finished exceuting the : ", script_name)
    sys.exit(ret)