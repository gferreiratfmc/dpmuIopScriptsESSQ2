import os
from pickle import FALSE

import subprocess
import sys
import time


class FrontEndPSU:
    def __init__(self, Bus_I2C,device_number):
        self.BusI2C = Bus_I2C
        self.devNumber = device_number

    def Configure(self):
        self.BusI2C.write_byte(self.devNumber,0x1,0xf8)
        self.BusI2C.write_byte(self.devNumber,0x6,0x0)
        self.BusI2C.write_byte(self.devNumber,0x7,0x0)
        self.BusI2C.write_byte(self.devNumber,0x8,0x10)

    def ReadSE(self,lsbAdd,msbAdd):
        lsb = self.BusI2C.read_byte(self.devNumber,lsbAdd)&0xff
        msb = self.BusI2C.read_byte(self.devNumber,msbAdd)&0x7f
        v = (msb*(2**8) + lsb)&0x7fff
        if (v>0x4000):#detect if negative
            #print("NegativeNumber")
            v = ((~v + 1)&0x3fff * - 1)
        v = v * (2.5/(2**13))
        return v

    def ReadV1(self):
        return self.ReadSE(0xb,0xa)

    def ReadV2(self):
        return self.ReadSE(0xd,0xc)

    def ReadV3(self):
        return self.ReadSE(0xf,0xe)

    def ReadV4(self):
        return self.ReadSE(0x11,0x10)

    def ReadV5(self):
        return self.ReadSE(0x13,0x12)

    def GetVcc(self):
        return self.ReadSE(0x1d,0x1c)+2.5

    def GetIntTemp(self):
        lsb = self.BusI2C.read_byte(self.devNumber,0x1b)&0xff
        msb = self.BusI2C.read_byte(self.devNumber,0x1a)&0x1f
        t = (msb*(2**8) + lsb)&0x1fff
        t = t * 0.0625
        return t

    def GetIOut(self):
        v1 = self.ReadV1()
        Iout = (v1 - 0.5 ) * 10
        return Iout

    def GetVOut(self):
        v2 = self.ReadV2()
        Vout = (v2 ) * 10
        return Vout

    def GetIOG(self):
        v3 = self.ReadV3()
        if v3 > 2:
            return "Bad"
        else:
            return "Good"

    def GetVoutStatus(self):
        v4 = self.ReadV4()
        if v4 > 2:
            return "Bad"
        else:
            return "Good"

    def GetNtcTemp(self):
        v5 = self.ReadV5()
        y = -3.5535*v5**3 + 27.198*v5**2 - 86.811*v5**1 + 127.8
        return y
    
if __name__ == "__main__":
    print(">> REM >> This is a class file, execution could be performed, but no effect for FAT")
    sys.exit(0)