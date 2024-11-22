from ast import Bytes
import os
import subprocess
import sys
import socket
import struct
import threading
import time



class IOP_IO:
    def __init__(self):
        return

    def SetBe(self,inInt):
        try:
            command = f"gpioCtrlApp -x wgs IOP_BPRVC_BE_DISABLE {inInt}"
            os.system(command)
        except Exception as e:
            print(f"Error writing data: {str(e)}")

    def GetIOG(self):
        try:
            command = "gpioCtrlApp -x rgs IOP_BPRVC_FE_IOG"
            result = os.popen(command).read()
            data = int(result[21:22], 10)  # Convert hexadecimal result to an integer
            return data
        except Exception as e:
            print(f"Error reading data: {str(e)}")
            return None

    #FT1
    def GetCan11err(self):
        try:
            command = "gpioCtrlApp -x rgs IOP_BPRVC_CAN_ERR"
            result = os.popen(command).read()
            data = int(result[21:22], 10)  # Convert hexadecimal result to an integer
            return data
        except Exception as e:
            print(f"Error reading data: {str(e)}")
            return None

    #FT2
    def GetCan12err(self):
        try:
            command = "gpioCtrlApp -x rgs IOP_BPRVC_CAN_ERR_4"
            result = os.popen(command).read()
            data = int(result[21:22], 10)  # Convert hexadecimal result to an integer
            return data
        except Exception as e:
            print(f"Error reading data: {str(e)}")
            return None       

class I2CBus:
    def __init__(self, bus_number):
        self.bus_number = bus_number

    def read_byte(self, device_address, register_address, option='b'):
        try:
            command = f"i2cget -yf {self.bus_number} {hex(device_address)} {hex(register_address)} {option}"            
            result = (os.popen(command).read())
            data = int(result, 16)  # Convert hexadecimal result to an integer
            if option=='w':
                data = ((data&0xff)<<8) + ((data&0xff00)>>8)
            return data
        except Exception as e:
            print(f"Error reading data: {str(e)}")
            return None

    def write_byte(self, device_address, register_address, data, option='b'):
        try:
            
            if option=='b':
                command = f"i2cset -yf {self.bus_number} {hex(device_address)} {hex(register_address)} {hex(data)} {option}"
            else:
                command = f"i2cset -yf {self.bus_number} {hex(device_address)} {hex(register_address)} {hex(data&0xff)} {hex((data>>8)&0xff)} {option}"
            #print(command)
            os.system(command)
        except Exception as e:
            print(f"Error writing data: {str(e)}")

    def interpret_i2cdetect_exit_code(self, exit_code):
        """
        Interprets the exit code of the i2cdetect command and provides a description.
        """
        if exit_code == 0:
            return "Success: Devices detected on the I2C bus."
        elif exit_code == 1:
            return "No devices found on the I2C bus."
        elif exit_code == 2:
            return "Bus not available or cannot be accessed."
        elif exit_code == 3:
            return "Invalid arguments provided to i2cdetect."
        elif exit_code == 4:
            return "I/O error occurred while communicating with the I2C bus."
        else:
            return f"Unknown exit code: {exit_code}"

    def I2Cdetect(self):
        print(f">> REM >>Scanning I2C bus {self.bus_number} for devices...")
        errorCode=1           
        for address in range(0x03, 0x77):
            command = f"i2cdetect -yaf -r {self.bus_number} {address:02X} {address:02X}"
            result = os.popen(command).read()
            #print(result)
            try:
                if (("--") in (result)):
                    ret = "Not Detected"
                else:
                    ret = "Detected"
                    errorCode = 0
                    print(f">> REM >> Address 0x{address:02X}: {ret}")
            except Exception as e:
                print(f">> REM >> Error scanning address 0x{address:02X}: {str(e)}")
        print(">> REM >>Finished Scanning")  
        return errorCode

class IOP_Housekeeping:
    def __init__(self, Bus_I2C,device_number):
        self.BusI2C = Bus_I2C
        self.devNumber = device_number
         
    def Configure(self):
        return

    def is_even(self,number):
        return number % 2 == 0

    def SetChannel(self,Channel):
        if self.is_even(Channel):
            Config=0x8
        else:
            Config=0xc
        Config += Channel//2
        self.BusI2C.write_byte(self.devNumber,(Config<<4)+0x8,0x0,'b')

    def ReadConversion(self):
        data = self.BusI2C.read_byte(self.devNumber,0,'w')
        return data>>4
    
    def ReadAnalog_mv(self,ch):
        self.SetChannel(ch)
        return self.ReadConversion()
    
    def get24V1(self):
        Ain_mv = self.ReadAnalog_mv(0)        
        return (Ain_mv/0.0893)/1000

    def get24V2(self):
        Ain_mv = self.ReadAnalog_mv(1)        
        return (Ain_mv/0.0893)/1000
    
    def getCurrent(self):
        Ain_mv = self.ReadAnalog_mv(2)        
        return (Ain_mv/2.5)/1000

    def get1V1(self):
        Ain_mv = self.ReadAnalog_mv(3)        
        return (Ain_mv/1)/1000

    def get1V35(self):
        Ain_mv = self.ReadAnalog_mv(4)        
        return (Ain_mv/1)/1000

    def get2V5(self):
        Ain_mv = self.ReadAnalog_mv(5)        
        return (Ain_mv/1)/1000
    
    def get3V3(self):
        Ain_mv = self.ReadAnalog_mv(6)        
        return (Ain_mv/1)/1000
    
    def get5V0(self):
        Ain_mv = self.ReadAnalog_mv(7)        
        return (Ain_mv/0.595)/1000
    
class IOP_Temperature:
    def __init__(self, Bus_I2C,device_number):
        self.BusI2C = Bus_I2C
        self.devNumber = device_number

    def Configure(self):
        #self.BusI2C.write_byte(self.devNumber,0x1,0xf8) #config - default 12bits
        #self.BusI2C.write_byte(self.devNumber,0x2,+70) #TLOW
        #self.BusI2C.write_byte(self.devNumber,0x3,+85) #THIGHT
        return

    def ReadSE(self,addr,opt):
        data = self.BusI2C.read_byte(self.devNumber,addr,opt)
        return data

    def GetTemp(self):
        tempDig = self.ReadSE(0,'w')
        if (tempDig>0x8000):
            tempDig=1+~tempDig
            y = -1*(tempDig>>4)*0.0625
        else:
            y = (tempDig>>4)*0.0625
        return y

class SocketCan():
    
    def __init__(self,canItf):
        self.canbus = socket.socket(socket.PF_CAN, socket.SOCK_RAW, socket.CAN_RAW)
        self.canbus.bind((canItf,))
        self.canbus.settimeout(0.4)  # Set the socket timeout in seconds

    def write(self,cobid,data):
        try:
            can_frame = self.create_can_frame(cobid,data)
            self.canbus.send(can_frame)
            return True
        except:
            return False
    
    def read(self):
        try:
            cob_idRx, dataRx = self.parse_can_frame(self.canbus.recv(16))
            return [cob_idRx,dataRx]
        except:
            return [0,bytes([0x0, 0x00, 0x00, 0x00])]

    def create_can_frame(self,cob_id, data):
        try:
            if not (0 <= cob_id <= 0x7FF):
                raise ValueError("COB-ID must be a valid 11-bit identifier (0-0x7FF)")
    
            cob_id_bytes = cob_id.to_bytes(2, byteorder='little')
            Dummy2 = bytes([0x00,0x00])
            Dummy3 = bytes([0x00,0x00, 0x00])
            data_length = len(data).to_bytes(1, byteorder='little')
            
            # Combine COB-ID, Data Length, and Data
            can_frame = cob_id_bytes + Dummy2 + data_length + Dummy3 + data
            zero_bytes = bytearray(16-len(can_frame))
            return can_frame + zero_bytes
        except:
            None
    
    def parse_can_frame(self,can_frame):
        try:
            if len(can_frame) != 16:
                raise ValueError("Invalid CAN frame length (8 bytes expected)")    
            cob_id = int.from_bytes(can_frame[0:2], byteorder='little')
            data_length = int.from_bytes(can_frame[4:5], byteorder='little')
            data = can_frame[8:8 + data_length]
            return cob_id, data
        except:
            return None
        
if __name__ == "__main__":
    print(">> REM >> This is a class file, execution could be performed, but no effect for FAT")
    sys.exit(0)