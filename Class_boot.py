from machine import Pin,SPI
import network
import esp
import webrepl

#ethernet configuration
ipAddr = '10.11.201.7'
netmask = '255.255.255.0'
gateway = '10.11.201.2'
dns = '8.8.8.8'

# WiFi configuration
WIFI_SSID = 'NewVenecy'
WIFI_PASSWORD = '2172862991'
AP_SSID = 'MicroPython-AP'
AP_PASSWORD = '123456789'

esp.osdebug(None)

#ETHERNET
def configEthernet():
    try:
        eth_spi = SPI(1, 10000000, sck=Pin(14), mosi=Pin(13), miso=Pin(12))
        eth_int = Pin(39, Pin.IN)
        eth_cs = Pin(11, Pin.OUT)
        eth0 = network.LAN(phy_type=network.PHY_W5500, phy_addr=0, spi=eth_spi, int=eth_int, cs=eth_cs)
        eth0StaticIp=(ipAddr,netmask,gateway,dns)
        eth0.active(1)
        eth0.ifconfig(eth0StaticIp)
    except:
        pass
        
def connectWifi():
    try:
        wlan0 = network.WLAN(network.STA_IF)
        wlan0.active(True)
        wlan0.connect(WIFI_SSID, WIFI_PASSWORD)
    except:
        pass

def startAccessPoint():
    try:
        ap = network.WLAN(network.AP_IF)
        ap.active(True)
        ap.config(essid=AP_SSID, authmode=network.AUTH_WPA_WPA2_PSK, password=AP_PASSWORD)
        
        while ap.active() == False:
            pass       
        print('Connection successful')
        print(ap.ifconfig())
    except:
        pass

configEthernet()
startAccessPoint()
#connectWifi()
webrepl.start(password='admin')

