import os
import argparse
import subprocess
import sys
import time

class I2CMem:
    def __init__(self, bus_number, addr):
        self.bus_number = bus_number
        self.devAddr = addr

    def read(self, regName):
        try:
            command = f"/mnt/scripts/fmcFramI2cRead {self.bus_number} {self.devAddr} {regName}"
            print(f">> REM >> {command}")
            result = os.popen(command).read()
            return result
        except Exception as e:
            return(f"Error reading data: {str(e)}")
            

    def write(self, regName, data):
        try:
            command = f"/mnt/scripts/fmcFramI2cWrite {self.bus_number} {self.devAddr} {regName} {data}  >> cout.txt"
            print(f">> REM >> {command}")
            os.system(command)
        except Exception as e:
            print(f"Error writing data: {str(e)}")
            
if __name__ == "__main__":
    print(">> REM >> This is a class file, execution could be performed, but no effect for FAT")
    sys.exit(0)