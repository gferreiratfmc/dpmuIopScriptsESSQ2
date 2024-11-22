## This class is the PLC 'Server' to accept Clients commands
import network
import socket
import machine
import ustruct
import utime
import ujson
from machine import Pin
from machine import I2C
from machine import UART
import webrepl
import _thread
import esp
import esp32
esp.osdebug(esp.LOG_INFO)
#import uasyncio as asyncio
import CAN
can_lock = _thread.allocate_lock()

PLC_ADDR='10.11.201.7'
PLC_PORT=1234
CANOPEN_GATEWAY_PORT=2345

def setupCan(baud):
	try:
		print(f'Setup can with baud {baud}')
		can1 = CAN(0, extframe=False, tx=8, rx=3, mode=CAN.NORMAL, baudrate=baud, auto_restart=False)
		global canbus
		canbus = [can1]
	except Exception as e:
		print(str(e))
		return str(e)
	
def setupOut():
	try:
		print('Setup Output pins')
		o1 = Pin(45, Pin.OUT) #relay
		o2 = Pin(48, Pin.OUT) #relay
		o3 = Pin(4, Pin.OUT) #lvttl
		o4 = Pin(5, Pin.OUT) #lvttl
		o5 = Pin(21, Pin.OUT) #ext 5v relay
		o6 = Pin(47, Pin.OUT) #ext 5v relay
		global output_pins
		output_pins = [o1,o2,o3,o4,o5,o6]
	except Exception as e:
		print(str(e))     
		return str(e)		
	
def setupIn():
	try:
		print('Setup Input pins')
		i0 = None
		i1 = None
		i2 = None
		i3 = None
		i4 = None
		i5 = None
		global input_pins
		input_pins = [i0,i1,i2,i3,i4,i5]
	except Exception as e:
		print(str(e))     
		return str(e)
	
def setupI2c():
	try:
		print('Setup I2C bus')
		i2c1 = I2C(0, scl=Pin(01), sda=Pin(02), freq=400000)
		i2c2 = I2C(1, scl=Pin(09), sda=Pin(10), freq=400000)
		global i2c
		i2c = [i2c1,i2c2]
	except Exception as e:
		print(str(e))
		return str(e)
	
def setupUart(baud1,baud2):
	try:
		print(f'Setup Uart with baud {baud1} and {baud2}')
		uart1 = UART(1, baudrate=baud1, tx=7, rx=6, timeout = 2000)  # Modify TX and RX pins as needed
		uart2 = UART(2, baudrate=baud2, tx=18, rx=17, timeout = 2000)  # Modify TX and RX pins as needed
		global uart
		uart = [uart1,uart2]
		re1 = Pin(15, Pin.OUT) # if using 485 half, shall be 1 if transmitting, otherwise, always 0
		re1.on() #Disables receiver
		re2 = Pin(16, Pin.OUT) # if using 485 half, shall be 1 if transmitting, otherwise, always 0
		re2.on() #
		global re
		re = [re1,re2]
	except Exception as e:
		print(str(e))     
		return str(e)		
	
# Initialize the socket server
def start_server(plcaddr,plcport):
	try:
		addr = socket.getaddrinfo(plcaddr,plcport)[0][-1]
		s = socket.socket()
		s.bind(addr)
		s.listen(5)
		print(f'Server listening on {addr}')
		return s
	except Exception as e:
		print(str(e))     
		return str(e)
	
# Function to send query and read from I2C
def query_i2c(bus,eightAddr, regAddr, data):
	try:
		global i2c	
		response = 'OK'
		sevenAddr = (eightAddr // 2)
		if eightAddr & 0x1:
			response = i2c[bus].readfrom_mem(sevenAddr, regAddr, data[0])  # Modify as per expected response length
			print(f'value read from i2c = {response}')
		else:
			print('writing i2c')
			i2c[bus].writeto_mem(sevenAddr, regAddr, data)
		return response
	except Exception as e:
		print(str(e))     
		return str(e)

# Function to send query and read from CAN
def query_can(bus, can_id, query):
	try:
		global canbus
		canbus[bus].send(list(query), can_id, timeout = 400, rtr = False, extframe = False)
		msg = canbus[bus].recv(timeout=400)
		return msg
	except Exception as e:
		print(str(e))
		return str(e)

# Function to send query and read from CAN
def getMcuTemp():
	try:
		return esp32.mcu_temperature()
	except Exception as e:
		print(str(e))
		return str(e)

# Function to send query and read from UART
def query_uart(bus, query,isAsc=True,size=None):
	try:
		global Uarthalf
		global uart
		while uart[bus].any():
			uart[bus].read(1) #to empty the buffer
		print(f'query uart bus{bus} = {query}')
		if Uarthalf[bus]==1:
			re[bus].on()
			utime.sleep(0.05)  # time to swith transceivers from rx to tx
		uart[bus].write(query)
		while not uart[bus].txdone():
			pass #do nothing
		if Uarthalf[bus]==1:
			re[bus].off()
		utime.sleep(0.01)  # Wait for response
		if isAsc:
			print('readline')
			response = uart[bus].readline()
		else:
			print('read bytes')
			response = uart[bus].read(size)
		if response:
			print(response)
			pass
		else:
			print('EMPTY RX BUFFER')			
		return response
	except Exception as e:
		print(str(e))     
		return str(e)

# Handle incoming commands
def handle_command(data):
	response = ''
	command = ''
	try:     
		if data.startswith(b'CAN_GATEWAY;'):
			response = f'INVALID_PORT_CAN_GATEWAY_USE_{CANOPEN_GATEWAY_PORT}'
			response = response.encode('ascii')
			return ujson.dumps(response)
		else:
			command = data.decode('ascii').strip()
			#print(f'Received command {command}')
		parts = command.split(';')
		if command.startswith('QUERY_I2C'):
			if len(parts) == 5:
				print("Processing QUERY_I2C")
				bus = int(parts[1])
				eightAddr = int(parts[2])
				regAddr = int(parts[3])
				dataArray = parts[4].split(',')
				data=[]
				for dat in dataArray:
					if dat!='':
						data.append(int(dat))
				dataByte=bytearray(data)
				responseByteArray = query_i2c(bus,eightAddr, regAddr, dataByte)
				if responseByteArray == None:
					response = 'EMPTY RX BUFFER'
				else:
					if type(responseByteArray) == str:
						response=responseByteArray
					else:
						for dat in responseByteArray:
							digit = "0x{:02x}".format(dat)
							response = f'{response}{digit},'
				print(f'response i2c = {response}')
			else:
				response = 'INVALID_COMMAND_I2C'
		elif command.startswith('QUERY_CAN'):
			global baudInit
			if baudInit:      
				if len(parts) == 4:
					bus = int(parts[1])
					can_id = int(parts[2])
					dataArray = parts[3].split(',')
					data=[]
					for dat in dataArray:
						if dat!='':
							data.append(int(dat))
					dataByte=bytearray(data)
					with can_lock:
						responseByteArray = query_can(bus,can_id, dataByte)
						if responseByteArray == None:
							response = 'EMPTY RX BUFFER'
						else:
							if type(responseByteArray) == str:
								response=responseByteArray
							else:
								for dat in responseByteArray:
									digit = "0x{:02x}".format(dat)
									response = f'{response}{digit},'
				else:
					response = 'INVALID_COMMAND_CAN'
			else:
				response = 'ERROR_RUN_SETUP_BAUD'	
		elif command.startswith('QUERY_UART'):
			global baudInit
			if baudInit:
				if len(parts) == 4:
					bus = int(parts[1])
					typ = parts[2]
					if typ=="ASC":
						dataByteTmp=f'{parts[3]}\r\n'
						dataByte=dataByteTmp.encode('utf-8')
						responseByteArray = query_uart(bus, dataByte)
						if responseByteArray == None:
							response = 'EMPTY RX BUFFER'
						else:
							response = responseByteArray.decode('utf-8')
					else:
						sizeStr = (typ.replace('BIN',''))
						if sizeStr:
							size = int(sizeStr)
						dataArray = parts[3].split(',')
						data=[]
						for dat in dataArray:
							if dat!='':
								data.append(int(dat))
						dataByte=bytearray(data)
						responseByteArray = query_uart(bus=bus, query=dataByte,isAsc=False,size=size)
						if responseByteArray == None:
							response = 'EMPTY RX BUFFER'
						else:
							if type(responseByteArray) == str:
								response=responseByteArray
							else:
								for dat in responseByteArray:
									digit = "0x{:02x}".format(dat)
									response = f'{response}{digit},'         
				else:
					response = 'INVALID_COMMAND_UART'
			else:
				response = 'ERROR_RUN_SETUP_BAUD'
		elif command.startswith('SET_OUTPUT'):
			if len(parts) == 3:
				pin_index = int(parts[1])
				state = int(parts[2])
				if 0 <= pin_index < len(output_pins):
					if output_pins[pin_index] != None:
						output_pins[pin_index].value(state)
						response = 'OK'
					else:
						response = 'PIN IS NOT OUTPUT'
				else:
					response = 'INVALID_PIN'
			else:
				response = 'INVALID_COMMAND_OUTPUT'
		elif command.startswith('GET_INPUT'):
			if len(parts) == 2:
				pin_index = int(parts[1])
				if 0 <= pin_index < len(input_pins):
					if input_pins[pin_index] != None:						
						response = input_pins[pin_index].value()
					else:
						response = 'PIN IS NOT INPUT'
				else:
					response = 'INVALID_PIN'
			else:
				response = 'INVALID_COMMAND_INPUT'   
		elif command.startswith('SETUP_BAUD'):#baudUart1,baudUart2,baudCan
			global baudInit
			if len(parts) == 4:
				baudCan = int(parts[3])
				baudUart1 = int(parts[1])
				baudUart2 = int(parts[2])    
				setupCan(baudCan)
				setupUart(baud1=baudUart1,baud2=baudUart2)
				baudInit = True
				response = 'ACK'	
			else:
				response = 'INVALID_COMMAND_SETUP_BAUD'
				baudInit = False				
		elif command.startswith('SETUP_HALF'):#UART1HALF,UART2HALF
			if len(parts) == 3:
				Uart1half = int(parts[1])
				Uart2half = int(parts[2])
				global Uarthalf
				Uarthalf = [Uart1half,Uart2half]
			else:
				response = 'INVALID_COMMAND_SETUP_HALF'
		elif command.startswith('GET_MCU_TEMP'):#UART1HALF,UART2HALF
			if len(parts) == 1:
				response = f'{getMcuTemp()}'
			else:
				response = 'INVALID_COMMAND_GET_MCU_TEMP'    
		elif command.startswith('SETUP_REN'):#UART1HALF,UART2HALF
			if len(parts) == 3:
				re1 = int(parts[1])
				re2 = int(parts[2])
				global re
				re[0].value(re1)
				re[1].value(re2)
			else:
				response = 'INVALID_COMMANDSETUP_REN'    
		elif command.startswith('RESET_PLC'):
			print("reseting 1 ...")
			#machine.reset()
			raise SystemExit
		else:
			response = 'UNKNOWN_COMMAND'
		response = response.encode('ascii')
		return ujson.dumps(response)
	except SystemExit:
		print("reseting 2 ...")
		response = 'RESET_PLC_ACK'
		return ujson.dumps(response)  
	except Exception as e:
		response = str(e)
		return ujson.dumps(response)

# Main function to run the server and process commands
def plc_server_thread():
	print('Starting PLC Server...')
	setupCan(500000)
	setupIn()
	setupOut()
	setupI2c()
	global Uarthalf
	Uarthalf = [0,0]# half disabled by default
	s=None
	try:
		print("Start Server")
		s = start_server(PLC_ADDR,PLC_PORT)     
		while True:
			conn, addr = s.accept()
			print(f'Client connected from {addr}')
			try:
				while True:
					data = conn.recv(1024)
					if not data:
						break
					response = handle_command(data)
					conn.send(response)
					if response.count('RESET_PLC'):
						raise SystemExit
			except SystemExit:
				print("reseting 3 ...")
				conn.close()
				del conn
				del addr
				break
			except Exception as e:
				print(str(e))
			finally:
				conn.close()
				del conn
				del addr
	except Exception as e:
		print(str(e))
	finally:
		s.close()
		del s
		print('Exiting PLC Server ...')
		machine.reset()

# Handle can gateway
def handle_can_gateway(data):
	response = ''
	try:
		if data.startswith(b'CAN_GATEWAY;'):
			#print("Can Gateway message")
			#print(f'data={data}')	
			global baudInit
			if baudInit:
				data = data[len('CAN_GATEWAY;'):]
				# Parse CAN frame
				arbitration_id = int.from_bytes(data[:4], 'big')
				can_data = data[4:]
				# Send CAN frame
				msg=None
				with can_lock:
					print(f"Sent CAN frame: ID={arbitration_id}, Data={can_data}")
					msg = query_can(0,arbitration_id,can_data)
				if msg:
					print(msg)
					id=msg[0]
					#ex=msg[1]
					#rtr=msg[2]			
					dt=msg[3]	
					response = b'CAN_GATEWAY;' + id.to_bytes(4,'big') + (dt)	
				else:
					print('No answer from CAN Node')
					response = b'CAN_GATEWAY;' + b'\0\0\0\0' + b'\0\0\0\0\0\0\0\0' # empty response
				return (response)
		response = f'INVALID_PORT_PLC_COMMANDS_USE_{PLC_PORT}'
		response = response.encode('ascii')
		return ujson.dumps(response)
	except Exception as e:
		response = str(e)
		return ujson.dumps(response)

#to run as a thread
def can_gateway_thread():
	print('Starting Can Gateway Thread...')
	s=None
	try:
		print("Start Can Gateway Server")
		s = start_server(PLC_ADDR,CANOPEN_GATEWAY_PORT)     
		while True:
			conn, addr = s.accept()
			print(f'Client cangateway connected from {addr}')
			try:
				while True:
					response = 'no response'
					try:
						data = conn.recv(64)
						if data:
							response = handle_can_gateway(data)
							conn.send(response)
					except Exception as e:
						print(str(e))
			except Exception as e:
				print(str(e))
			finally:
				conn.close()
				del conn
				del addr
	except Exception as e:
		print(str(e))
	finally:
		s.close()
		del s
		print('Exiting can gateway ...')

############ MAIN ############
#print('Stoping WEBREPL...')
#webrepl.stop()
_thread.start_new_thread(can_gateway_thread,list())
_thread.start_new_thread(plc_server_thread,list())
