## This class is the PLC 'Client' and is used to set all 
## PLC resources and devices connected to PLC
import logging
import os
import subprocess
import sys
import time
import struct
import socket
import Class_WebSocket
import can

script_path = os.path.abspath(__file__)
script_name = os.path.basename(script_path)
dir_name = os.path.dirname(script_path)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
# Create a file handler
file_handler = logging.FileHandler(f'{script_name}.log')
file_handler.setLevel(logging.DEBUG)
# Create a console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)
logger.addHandler(file_handler)
logger.addHandler(console_handler)
logger.info('>> REM >> Class_PLC_devices.py - Replacing logger.info by logger.info')

#PLC data default
#HOST IP SHALL BE 10.11.201.2
PLC_IP = "10.11.201.7"
PLC_PORT = 1234
CAN_GATEWAY_PORT = 2345
PLC_PORT_WEBSOCKET = 8266
PASSWORD = "admin" #websocket password

RVC_FE_ADDR = 0x4c
EXT_I2C_BUS = 1
ADC_I2C_BUS = 0
ADC_DATA_ADDR = 0x0
ADC_CONFIG_ADDR = 0x2
I2C_WRITE = 0
I2C_READ  = 1
ADC_COUNT2VOLT = (4.096 / 2**12)

#Result codes
RES_OK = 0
RES_ERR = 255
RES_DLG = 254
RES_NOTIMPL = 253
RES_CANERR = 252
RES_USBTOMUCH = 251
RES_USBNOTFOUND = 250

class plc:
    ws = None
    client_canopen_socket = None
    client_socket = None
    def __init__(self,host=PLC_IP,port=PLC_PORT, canPort = CAN_GATEWAY_PORT,passWord=PASSWORD):
        try:
            self.host = host
            self.port = port
            self.canPort = canPort
            self.passWord = passWord
        except Exception as e:
            logger.info(f">> REM >> Error: {str(e)}")
            print(f">> REM >> Error: {str(e)}")
        finally:
            self.createSocket()
            self.createCanOpenSocket()
            return

    def createSocket(self):
        print(">> REM >> Creating Socket")
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.settimeout(10)
        response = ''
        try:
            self.client_socket.connect((self.host, self.port))
        except socket.timeout:
            logger.info(">> REM >> Connection timed out. Could not connect to the PLC.")
            response = 'Exception - Timeout'
            self.client_socket.close()
        except Exception as e:
            logger.info(">> REM >>" + f"Error: {str(e)}")
            response = f'Exception - {str(e)}'
            self.client_socket.close()
        finally:
            return response

    def createCanOpenSocket(self):
        print(">> REM >> Creating Canopen Socket")        
        self.client_canopen_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_canopen_socket.settimeout(10)
        response = ''
        try:
            self.client_canopen_socket.connect((self.host, self.canPort))
        except socket.timeout:
            logger.info(">> REM >> Connection timed out. Could not connect to the PLC.")
            response = 'Exception - Timeout'
            self.client_canopen_socket.close()
        except Exception as e:
            logger.info(">> REM >>" + f"Error: {str(e)}")
            response = f'Exception - {str(e)}'
            self.client_canopen_socket.close()
        finally:            
            return response
 
    def closeSocket(self):
        #self.client_socket.shutdown(socket.SHUT_RD)
        if self.client_socket != None:
            self.client_socket.close()
            del self.client_socket        
            self.client_socket = None        
        return 

    def closeSocketCanOpen(self):
        #self.client_canopen_socket.shutdown(socket.SHUT_RD)
        if self.client_canopen_socket != None : 
            self.client_canopen_socket.close()
            del self.client_canopen_socket
            self.client_canopen_socket = None
        return           

    def Close_WS(self):
        try:
            if self.ws != None:
                self.ws.close()
                del self.ws
                self.ws = None
        except Exception as e:
            logger.info(f">> REM >> Error: {str(e)}")
            print(f">> REM >> Error: {str(e)}")                     
  
    def ResetServer(self):
        try:
            print(">> REM >> PLC option reset selected")
            logger.info(">> REM >> PLC option reset selected")
            if self.client_socket == None:
                self.createSocket()
            if self.sendMsg("RESET_PLC").startswith('Exception'):
                print(">> REM >> PLC Reset via server failed, trying via websocket")
                logger.info(">> REM >> PLC Reset via server failed, trying via websocket")
                if self.ws == None:
                    print(">> REM >> Connecting PLC via websocket")
                    logger.info(">> REM >> Connecting PLC via websocket")                
                    self.ws = Class_WebSocket.websocket(self.host,PLC_PORT_WEBSOCKET,self.passWord)
                    time.sleep(1.0)
                self.ws.sendString("import machine")
                self.ws.sendString("machine.reset()")
            print(">> REM >> Waiting PLC to reset")
            logger.info('Waiting 5 seconds: PLC to reset')
            self.closeSocket()
            self.closeSocketCanOpen()
            self.Close_WS()
            time.sleep(5.0)
            print(">> REM >> PLC has reseted")
            logger.info('PLC has reseted') 
        except Exception as e:
            logger.info(f">> REM >> Error: {str(e)}")
            print(f">> REM >> Error: {str(e)}")
                 
    def RunCmd(self,cmdList):
        try:
            if self.client_socket == None:
                print(">> REM >> Connecting PLC via socket")
                logger.info(">> REM >> Connecting PLC via socket")                  
                self.createSocket()
            if self.ws == None:
                print(">> REM >> Connecting PLC via websocket")
                logger.info(">> REM >> Connecting PLC via websocket")                
                self.ws = Class_WebSocket.websocket(self.host,PLC_PORT_WEBSOCKET,self.passWord)
                time.sleep(1.0)
            print(f">> REM >> RunCmd {cmdList}")
            logger.info(f">> REM >> RunCmd {cmdList}")
            for cmd in cmdList:
                self.ws.sendString(cmd)
            time.sleep(1.0)
        except Exception as e:
            logger.info(f">> REM >> Error: {str(e)}")
            print(f">> REM >> Error: {str(e)}")  

    def SendFile(self,fileNameSrc, fileNameDest):
        try:
            if self.client_socket == None:
                print(">> REM >> Connecting PLC via socket")
                logger.info(">> REM >> Connecting PLC via socket")                  
                self.createSocket()
            if self.ws == None:
                print(">> REM >> Connecting PLC via websocket")
                logger.info(">> REM >> Connecting PLC via websocket")                
                self.ws = Class_WebSocket.websocket(self.host,PLC_PORT_WEBSOCKET,self.passWord)
                time.sleep(1.0)
            print(f">> REM >> Sending file {fileNameSrc}")
            logger.info(f">> REM >> Sending file {fileNameSrc}")
            self.ws.put_file(fileNameSrc, fileNameDest)
            time.sleep(1.0)     
        except Exception as e:
            logger.info(f">> REM >> Error: {str(e)}")
            print(f">> REM >> Error: {str(e)}")      

    def sendCanGateway(self,data):
        try:
            if self.client_canopen_socket == None:
                self.createCanOpenSocket()
            self.client_canopen_socket.sendall(data)
        except Exception as e:
            return e
    
    def getCanGateway(self,buffer_size):
        try:
            if self.client_canopen_socket == None:
                self.createCanOpenSocket()            
            data = self.client_canopen_socket.recv(buffer_size)
            return data
        except Exception as e:
            return e
              
    def sendMsg(self,commandStr):
        response = ''
        try:
            if self.client_socket == None:
                self.createSocket()
            #logger.info(f">> REM >> SEND COMMAND TO PLC: {commandStr}")
            self.client_socket.sendall(bytes(commandStr + "\n", "utf-8"))
            #logger.info(">> REM >> WAITING ANSWER FROM PLC")
            response = self.client_socket.recv(1024).decode()
            #logger.info(f">> REM >> RECEIVED = {response} FROM PLC")
        except socket.timeout:
            logger.info(">> REM >> Connection timed out. Could not connect to the PLC.")
            response = 'Exception - Timeout'
            #sys.exit(RES_ERR)
        except Exception as e:
            logger.info(">> REM >>" + f"Error: {str(e)}")
            response = f'Exception - {str(e)}'
            #sys.exit(RES_ERR)
        finally:
            #self.client_socket.close()
            return response
    
    #bus (0/1) opt (ASC/BIN)
    def queryUart(self,bus,opt,data):
        tmpStr = ""
        if type(data) == str:
            tmpStr = data
        else:
            for tmp in data:
                tmpStr += (f"{tmp},")
        ret = self.sendMsg(f"QUERY_UART;{bus};{opt};{tmpStr}")
        if opt == "ASC":
            resp = ret
        else:
            resp = self.getByteArrayfromString(ret)
        return resp
    
    def queryCan(self,bus,nodeid,data):
        tmpStr = ""
        if type(data) == str:
            tmpStr = data
        else:
            for tmp in data:
                tmpStr += (f"{tmp},")        
        ret = self.sendMsg(f"QUERY_CAN;{bus};{nodeid};{tmpStr}")
        return self.getByteArrayfromString(ret)        
    
    def queryI2c(self,bus,eightAddr,regAddr,data):
        tmpStr = ""
        if type(data) == str:
            tmpStr = data
        else:
            for tmp in data:
                tmpStr += (f"{tmp},") 
        ret =  self.sendMsg(f"QUERY_I2C;{bus};{eightAddr};{regAddr};{tmpStr}")      
        return self.getByteArrayfromString(ret)

    def getMcuTemperature(self):
        try:            
            return float(self.sendMsg(f"GET_MCU_TEMP").replace('"',''))
        except Exception as e:
            print(str(e))
            return str(e)
    
    def setOutput(self,outIndex,value):
        return self.sendMsg(f"SET_OUTPUT;{outIndex};{value}")

    def getInput(self,inIndex):
        return self.sendMsg(f"GET_INPUT;{inIndex}")
    
    def setupBaud(self,baudUart1,baudUart2,baudCan):
        return self.sendMsg(f"SETUP_BAUD;{baudUart1};{baudUart2};{baudCan}")
   
    def setupHalf(self,half1,half2):
        return self.sendMsg(f"SETUP_HALF;{half1};{half2}")

    def setupRen(self,ren1,ren2):
        return self.sendMsg(f"SETUP_REN;{ren1};{ren2}")

    def getByteArrayfromString(self,strIn):
        try:            
            if strIn:
                if strIn.count('EMPTY RX BUFFER'):
                    return None                
                hex_values = strIn.replace('"','').split(',')
                int_values = []
                for val in hex_values:
                    if val:
                        int_values.append(int(val, 16))
                byte_array = bytes(int_values)
                return byte_array
            else:
                return strIn
        except Exception as e:
            return str(e)

# this is the internal ADC of PLC
class adc:
    def __init__(self,adcNum,resUp,resDown,plc):
        try:
            self.plc = plc
            self.bus = ADC_I2C_BUS
            self.resUp = resUp
            self.resDown = resDown
            addr = 0
            if adcNum == 1:
                addr = 0
            elif adcNum == 2:
                addr = 2
            elif adcNum == 3:
                addr = 1
            self.sevenAddr = 80 + addr
            self.eightAddr = (self.sevenAddr * 2)
            self.config()
        except Exception as e:
            logger.info(str(e))        

    def config(self):
        try:
            eightAddr = self.eightAddr + I2C_WRITE
            ret = self.plc.queryI2c(self.bus,eightAddr,ADC_CONFIG_ADDR,[0xc0]) #1 BYTES
            #logger.info(ret)
        except Exception as e:
            logger.info(str(e))        

    def getCount(self):
        try:
            eightAddr = self.eightAddr + I2C_READ
            ret = self.plc.queryI2c(self.bus,eightAddr,ADC_DATA_ADDR,[2]) #2 BYTES            
            retInt = int.from_bytes(ret, byteorder='big', signed=False)
            return retInt
        except Exception as e:
            logger.info(str(e))        

    def getVoltage(self):
        try:
            volt = self.getCount() * ADC_COUNT2VOLT
            return volt
        except Exception as e:
            logger.info(str(e))
    
    def getInVolt(self):
        try:
            inVolt=0
            volt=self.getVoltage()
            if self.resDown == 'open':
                inVolt=volt
            else:
                curr=(volt/self.resDown)
                inVolt = volt + curr*self.resUp
            return inVolt
        except Exception as e:
            logger.info(str(e))

#This is a Custom CAN BUS to connect to a gateway using socket/TCPIP
class CustomRemoteBus(can.BusABC):
    def __init__(self, plc, *args, **kwargs):
        try:   
            self.plc = plc
            self.plc.createCanOpenSocket()
            time.sleep(5)
            super().__init__(channel='remote',bustype='remote',*args, **kwargs)
        except Exception as e:
            logger.info(str(e))

    def send(self, msg, timeout=None):
        try:
            header = "CAN_GATEWAY;".encode()
            message_data = msg.arbitration_id.to_bytes(4, 'big') + bytes(msg.data)
            self.plc.sendCanGateway(header + message_data)
        except Exception as e:
            logger.info(str(e))

    def recv(self, timeout=None):
        try:
            buffer_size = len("CAN_GATEWAY;") + 12  # 4 bytes ID + 8 bytes data
            data = self.plc.getCanGateway(buffer_size)
            if not data:
                return None
            header_length = len("CAN_GATEWAY;")
            header = data[:header_length].decode()
            if header != "CAN_GATEWAY;":
                raise ValueError("Invalid header received")

            message_data = data[header_length:]
            arbitration_id = int.from_bytes(message_data[:4], 'big')
            data = message_data[4:]

            # Create and return a CAN message
            msg = can.Message(arbitration_id=arbitration_id, data=data, is_extended_id=False)
            #logger.info(msg)
            return msg
        except Exception as e:
            logger.info(str(e))
            return None

    def shutdown(self):
        self.plc.closeSocketCanOpen()
        return

# https://bkpmedia.s3.us-west-1.amazonaws.com/downloads/programming_manuals/en-us/8600_Series_programming_manual.pdf
class bk8622:
    def __init__(self,address,plc, uartNum):
        self.plc = plc
        self.addr = address #NOT used in 8622
        self.uartNum = uartNum
        self.cmdStr = (f"")

    def initialize(self):                
        self.enableremote()
        self.disableInput()
        self.setVoltageLimit(210)
        self.setCurrentLimit(10)
        self.setPowerLimit(2100)
        self.setMode("cc")
        self.setCcValue(3)
 
    def query(self,data2transmit):
        cmdStr = f'{self.cmdStr}{data2transmit}'
        return self.plc.queryUart(self.uartNum,"ASC",cmdStr)

    def enableremote(self):   
        return self.query('SYST:REM')
    
    #voltage is a float in voltage
    def setVoltageLimit(self,voltage):
        return self.query(f'VOLT:HIGH {voltage}')
    
    def setCurrentLimit(self,current):        
        return self.query(f'CURR:PROT {current}')
    
    def setPowerLimit(self,power):
        return self.query(f'POW:PROT {power}')
    
    def readIdn(self):
        return self.query('*IDN?')
        
    # Set CC, CV, CW, or CR mode
    def setMode(self,mode):
        opt='CURR'
        if mode=='cc' or mode=='CC':
            opt='CURR'
        elif mode=='cv' or mode=='CV':
            opt='VOLT'
        elif mode=='cw' or mode=='CW':
            opt='POW'
        elif mode=='cr' or mode=='CR':
            opt='RES'
        return self.query(f'FUNC {opt}')

    def setCcValue(self,value):
        return self.query(f'CURR {value}')

    def setCvValue(self,value):
        return self.query(f'VOLT {value}')
    
    def setCwValue(self,value):
        return self.query(f'POW {value}')
    
    def setCrValue(self,value):
        return self.query(f'RES {value}')

    def readInput(self):
        try:
            volt = self.query(f'MEAS:VOLT?')
            current = self.query(f'MEAS:CURR?')
            volt = float(volt.replace('"','').replace('\\n','').strip())
            current = float(current.replace('"','').replace('\\n','').strip())
            return [volt,current,volt*current]
        except Exception as e:
            logger.info(str(e))
            return [None, None, None]
    
    def disableInput(self):
        return self.query(f'INP 0')
    
    def enableInput(self):
        return self.query(f'INP 1')

# https://bkpmedia.s3.us-west-1.amazonaws.com/downloads/manuals/en-us/85xx_manual.pdf
class bk8522:
    def __init__(self,address,plc, uartNum):
        self.plc = plc
        self.addr = address
        self.uartNum = uartNum
        self.firstByte = 0xaa
        self.lsize = 26
        self.prefix = (f"BIN{self.lsize}")
        self.cmdStr = (f"")       

    def initialize(self):
        self.enableremote()
        self.disableInput()
        self.setVoltageLimit(210)
        self.setCurrentLimit(10)
        self.setPowerLimit(2100)
        self.setMode("cc")
        self.setCcValue(3)
 
    def query(self,data2transmit):
        cmdStr = self.cmdStr + data2transmit
        return self.plc.queryUart(self.uartNum,self.prefix,cmdStr)

    def cmd8500(self,opCmd,value):
        cmd=bytearray(self.lsize)
        cmd[0]=self.firstByte
        cmd[1]=self.addr
        cmd[2]=opCmd
        raw = int(value*1000)
        tmp = raw.to_bytes(4,'little')
        cmd[3]=tmp[0]
        cmd[4]=tmp[1]
        cmd[5]=tmp[2]
        cmd[6]=tmp[3]
        cmd[25]=self.csum(cmd)
        out=""
        for i in cmd:
            out+=f"{hex(i)},"
        out=out[:-1]
        out+=";"
        return out[:-1]
    
    def csum(self,thing):
        sum = 0
        for i in range(len(thing)):
            sum+=thing[i]
        return 0xFF&sum

    def enableremote(self):
        #print(f">> REM >> BK8522 enableremote")
        return self.query(self.cmd8500(0x20,1/1000))
    
    #voltage is a float in voltage
    def setVoltageLimit(self,voltage):
        #print(f">> REM >> BK8522 setVoltageLimit")
        return self.query( self.cmd8500(0x22,voltage))
    
    def setCurrentLimit(self,current):
        #print(f">> REM >> BK8522 setCurrentLimit")
        return self.query( self.cmd8500(0x24,current*10))
    
    def setPowerLimit(self,power):
        #print(f">> REM >> BK8522 setPowerLimit")
        return self.query( self.cmd8500(0x26,power))
    
    def readIdn(self):
        #print(f">> REM >> BK8522 readIdn")
        resp = self.query( self.cmd8500(0x6a,0))
        #print(f">> REM >> BK8522 readIdn {resp}")
        if resp:
            #if '0x38,0x35,0x32,0x32' in str(resp):
            if '8522' in str(resp):
                resp = "IDN IS BK PRECISION 8522"
            else:
                resp = "IDN IS NOT BK PRECISION 8522"
            return resp
        else:
            return 'ERROR reading IDN'
    
    def readInput(self):
        try:
            #print(f">> REM >> BK8522 readInput")
            arrayByt=self.query(self.cmd8500(0x5f,0))
            volt=(int.from_bytes(arrayByt[3:7],'little'))/1000.0
            current=(int.from_bytes(arrayByt[7:11],'little'))/10000.0
            power=(int.from_bytes(arrayByt[11:15],'little'))/1000.0        
            return [volt,current,power]
        except Exception as e:
            logger.info(str(e))
        
    # Set CC, CV, CW, or CR mode    
    def setMode(self,mode):
        #print(f">> REM >> BK8522 setMode")
        opt=0
        if mode=='cc' or mode=='CC':
            opt=0
        elif mode=='cv' or mode=='CV':
            opt=1
        elif mode=='cw' or mode=='CW':
            opt=2
        elif mode=='cr' or mode=='CR':
            opt=3
        return self.query( self.cmd8500(0x28,opt/1000))

    def setCcValue(self,value):
        #print(f">> REM >> BK8522 setCcValue")
        return self.query( self.cmd8500(0x2a,value*10))

    def setCvValue(self,value):
        #print(f">> REM >> BK8522 setCvValue")
        return self.query( self.cmd8500(0x2c,value))
    
    def setCwValue(self,value):
        #print(f">> REM >> BK8522 setCwValue")
        return self.query( self.cmd8500(0x2e,value))
    
    def setCrValue(self,value):
        #print(f">> REM >> BK8522 setCrValue")
        return self.query( self.cmd8500(0x30,value))

    def readInputValues(self):
        #print(f">> REM >> BK8522 readInputValues")
        return self.query( self.cmd8500(0x5F,0))
    
    def disableInput(self):
        #print(f">> REM >> BK8522 disableInput")
        return self.query( self.cmd8500(0x21,0))
    
    def enableInput(self):
        #print(f">> REM >> BK8522 enableInput")
        return self.query( self.cmd8500(0x21,1/1000))

    #only used to extract the frame of idn to be sent to windows to recognize the 8522 instrument in the COM Port
    def readIDNMsg(self):
        return self.cmd8500(0x6a,0)    

#https://www.xppower.com/products/series/resources/HDL_User_Manual.pdf
class xpPower:  
    #Config Constants
    REMOTEMODE      = "REMS 1"    
    ENABLE          = "POWER 1"
    DISABLE         = "POWER 0"
    SETVOLTAGE      = "SV "
    SETCURRENT      = "SI "

    #query
    queryobj = {
    "ENABLE_STATE"   : "POWER 2",
    "SETVOLTAGE"     : "SV?",
    "SETCURRENT"     : "SI?",
    "OUTPUTVOLTAGE"  : "RV?",
    "OUTPUTCURRENT"  : "RI?",
    "INTERNALTEMP"   : "RT?",
    "STATUS0"        : "STUS 0",
    "STATUS1"        : "STUS 1",
    "MANUFACTURE"    : "INFO 0",
    "MODEL"          : "INFO 1",
    "MAXVOLTAGE"     : "INFO 2",
    "REVISION"       : "INFO 3",
    "MANUFDATE"      : "INFO 4",
    "SN"             : "INFO 5",
    "COUNTRY"        : "INFO 6",
    "RATE"           : "RATE?",
    "NAME"           : "DEVI?",
    "IDENTITY"       : "*IDN?",
                }    
    #address must be None or 0~7
    def __init__(self,address,plc, uartNum):
        try:
            self.plc = plc
            self.addr = address #NOT used in 8622
            self.uartNum = uartNum
            self.cmdStr = (f"")
        except Exception as e:
            print(str(e))
            return
        
    def query(self,data2transmit):
        try:
            if self.addr:
                if self.addr in [0,1,2,3,4,5,6,7]:
                    cmdStr = f'ADDS {self.addr}\n\r'
                    self.plc.queryUart(self.uartNum,"ASC",cmdStr)
            cmdStr = f'{self.cmdStr}{data2transmit}\n\r'
            return self.plc.queryUart(self.uartNum,"ASC",cmdStr)
        except Exception as e:
            print(str(e))
            return str(e)
        
    def enableremote(self):   
        try:
            return self.query(self.REMOTEMODE)
        except Exception as e:
            print(str(e))
            return str(e)
    
    def setVoltage(self,voltage):
        try:
            return self.query(f'{self.SETVOLTAGE}{voltage}')
        except Exception as e:
            print(str(e))
            return str(e)
            
    def setCurrent(self,current):        
        try:
            return self.query(f'{self.SETCURRENT}{current}')
        except Exception as e:
            print(str(e))
            return str(e)
           
    def readIdn(self):
        try:
            return self.query(self.queryobj["IDENTITY"])
        except Exception as e:
            print(str(e))
            return str(e)
        
    def readSetup(self):
        try:
            enb=self.query(self.queryobj["ENABLE_STATE"])
            volt=self.query(self.queryobj["SETVOLTAGE"])
            curr=self.query(self.queryobj["SETCURRENT"])
            return [volt,curr,enb]
        except Exception as e:
            logger.info(str(e))
            return [None, None,None]

    def readOutputs(self):
        try:
            volt = self.query(self.queryobj["OUTPUTVOLTAGE"])
            current = self.query(self.queryobj["OUTPUTCURRENT"])
            volt = float(volt.replace('"','').replace('V\\r\\n','').strip())
            current = float(current.replace('"','').replace('A\\r\\n','').strip())
            return [volt,current,volt*current]
        except Exception as e:
            logger.info(str(e))
            return [None, None, None]
    
    def disable(self):
        try:        
            return self.query(self.DISABLE)
        except Exception as e:
            print(str(e))
            return
            
    def enable(self):
        return self.query(self.ENABLE)

#RVC ACDC PSU FrontEnd connected to PLC I2C #1
class psuFrontEnd:
    def __init__(self,plc):
        try:
            self.plc = plc
            self.bus = EXT_I2C_BUS
            self.sevenAddr = RVC_FE_ADDR
            self.eightAddr = (self.sevenAddr * 2)
            self.config()
        except Exception as e:
            logger.info(str(e))        

    def config(self):
        try:
            eightAddr = self.eightAddr + I2C_WRITE
            self.plc.queryI2c(self.bus,eightAddr,0x1,[0xf8])
            self.plc.queryI2c(self.bus,eightAddr,0x6,[0x0])
            self.plc.queryI2c(self.bus,eightAddr,0x7,[0x0])
            self.plc.queryI2c(self.bus,eightAddr,0x8,[0x10])
        except Exception as e:
            logger.info(str(e))        

    def ReadSE(self,lsbAdd,msbAdd):
        try:
            eightAddr = self.eightAddr + I2C_READ
            lsb = self.plc.queryI2c(self.bus,eightAddr,lsbAdd,[1])[0]&0xff   
            msb = self.plc.queryI2c(self.bus,eightAddr,msbAdd,[1])[0]&0x7f
            v = (msb*(2**8) + lsb)&0x7fff
            if (v>0x4000):#detect if negative
                #print("NegativeNumber")
                v = ((~v + 1)&0x3fff * - 1)
            v = v * (2.5/(2**13))
            return v
        except Exception as e:
            logger.info(str(e))        

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
        try:
            tmp= self.ReadSE(0x1d,0x1c) + 2.5
            return tmp
        except Exception as e:
            logger.info(str(e)) 
           
    def GetIntTemp(self):
        try:
            eightAddr = self.eightAddr + I2C_READ
            lsb = self.plc.queryI2c(self.bus,eightAddr,0x1b,[1])[0]&0xff   
            msb = self.plc.queryI2c(self.bus,eightAddr,0x1a,[1])[0]&0x1f           
            t = (msb*(2**8) + lsb)&0x1fff
            t = t * 0.0625
            return t
        except Exception as e:
            logger.info(str(e))        

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
    logger.info(">> REM >> This is a class file, execution could be performed, but no effect for FAT")
    sys.exit(0)