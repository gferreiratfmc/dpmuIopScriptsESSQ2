#!/usr/bin/env python
from __future__ import print_function
#from lib2to3.pgen2.pgen import DFAState
import sys
import os
import struct
import time
import socket
from typing import Self

#PLC data default
# PASSWORD = "admin"
# PLC_IP = "192.168.4.5"
# PLC_PORT = 8266


HANDSHAKE = b"""\
GET / HTTP/1.1\r
Host: echo.websocket.org\r
Connection: Upgrade\r
Upgrade: websocket\r
Sec-WebSocket-Key: foo\r
\r
"""
# Treat this remote directory as a root for file transfers
SANDBOX = ""
#SANDBOX = "/tmp/webrepl/"
DEBUG = 1

WEBREPL_REQ_S = "<2sBBQLH64s"
WEBREPL_PUT_FILE = 1
WEBREPL_GET_FILE = 2
WEBREPL_GET_VER  = 3
WEBREPL_FRAME_TXT = 0x81
WEBREPL_FRAME_BIN = 0x82


class websocket:

    def __init__(self,host,port, passWord):
        try:
            self.buf = b"" 
            self.s = socket.socket()
            ai = socket.getaddrinfo(host, port)
            addr = ai[0][4]
            self.s.connect(addr)
            self.s.settimeout(10)
            #self.s = s.makefile("rwb")
            self.client_handshake()
            self.login(passWord)
            ver = self.get_ver()
            self.debugmsg(f"Remote WebREPL version:{ver}")
            self.ioctl(9, 2)
        except Exception as e:
            return str(e)


    def debugmsg(self,msg):
        if DEBUG:
            print(msg)

    def write(self, data, frame=WEBREPL_FRAME_BIN):
        try:
            l = len(data)
            if l < 126:
                hdr = struct.pack(">BB", frame, l)
            else:
                hdr = struct.pack(">BBH", frame, 126, l)
            self.s.send(hdr)
            self.s.send(data)
        except Exception as e:
            return str(e) 

    def recvexactly(self, sz):
        try:
            res = b""
            while sz:
                data = self.s.recv(sz)
                if not data:
                    break
                res += data
                sz -= len(data)
            return res
        except Exception as e:
            return str(e)         


    def read(self, size, text_ok=False):
        try:
            if not self.buf:
                while True:
                    hdr = self.recvexactly(2)
                    assert len(hdr) == 2
                    fl, sz = struct.unpack(">BB", hdr)
                    if sz == 126:
                        hdr = self.recvexactly(2)
                        assert len(hdr) == 2
                        (sz,) = struct.unpack(">H", hdr)
                    if fl == 0x82:
                        break
                    if text_ok and fl == 0x81:
                        break
                    self.debugmsg("Got unexpected websocket record of type %x, skipping it" % fl)
                    while sz:
                        skip = self.s.recv(sz)
                        self.debugmsg("Skip data: %s" % skip)
                        sz -= len(skip)
                data = self.recvexactly(sz)
                assert len(data) == sz
                self.buf = data

            d = self.buf[:size]
            self.buf = self.buf[size:]
            assert len(d) == size, len(d)
            return d
        except Exception as e:
            return str(e) 

    def ioctl(self, req, val):
        assert req == 9 and val == 2


    def login(self, passwd):
        try:
            while True:
                c = self.read(1, text_ok=True)
                if c == b":":
                    assert self.read(1, text_ok=True) == b" "
                    break
            self.write(passwd.encode("utf-8") + b"\r")
        except Exception as e:
            return str(e)       

    
    def read_resp(self):
        try:
            data = self.read(4)
            sig, code = struct.unpack("<2sH", data)
            assert sig == b"WB"
            return code
        except Exception as e:
            return str(e)

    
    
    def send_req(self, op, sz=0, fname=b""):
        try:
            rec = struct.pack(WEBREPL_REQ_S, b"WA", op, 0, 0, sz, len(fname), fname)
            self.debugmsg("%r %d" % (rec, len(rec)))
            self.write(rec)
        except Exception as e:
            return str(e)         
    
    def get_ver(self):
        try:
            self.send_req(WEBREPL_GET_VER)
            d = self.read(3)
            d = struct.unpack("<BBB", d)
            return d
        except Exception as e:
            return str(e)        
    
    def put_file(self, local_file, remote_file):
        try:
            script_path = os.path.abspath(__file__)
            dir_name = os.path.dirname(script_path)
            if local_file.count('\\') or local_file.count('/'):
                pass
            else:
                if dir_name.count('\\'):
                    local_file = f"{dir_name}\\{local_file}"
                else:
                    local_file = f"{dir_name}/{local_file}"
            sz = os.stat(local_file)[6]
            dest_fname = (SANDBOX + remote_file).encode("utf-8")
            rec = struct.pack(WEBREPL_REQ_S, b"WA", WEBREPL_PUT_FILE, 0, 0, sz, len(dest_fname), dest_fname)
            self.debugmsg("%r %d" % (rec, len(rec)))
            self.write(rec[:10])
            self.write(rec[10:])
            assert self.read_resp() == 0
            cnt = 0
            with open(local_file, "rb") as f:
                while True:
                    sys.stdout.write("Sent %d of %d bytes\r" % (cnt, sz))
                    sys.stdout.flush()
                    buf = f.read(1024)
                    if not buf:
                        break
                    self.write(buf)
                    cnt += len(buf)
            print()
            assert self.read_resp() == 0
        except Exception as e:
            return str(e)         

    
    def get_file(self, local_file, remote_file):
        try:
            src_fname = (SANDBOX + remote_file).encode("utf-8")
            rec = struct.pack(WEBREPL_REQ_S, b"WA", WEBREPL_GET_FILE, 0, 0, 0, len(src_fname), src_fname)
            self.debugmsg("%r %d" % (rec, len(rec)))
            self.write(rec)
            assert self.read_resp() == 0
            with open(local_file, "wb") as f:
                cnt = 0
                while True:
                    self.write(b"\0")
                    (sz,) = struct.unpack("<H", self.read(2))
                    if sz == 0:
                        break
                    while sz:
                        buf = self.read(sz)
                        if not buf:
                            raise OSError()
                        cnt += len(buf)
                        f.write(buf)
                        sz -= len(buf)
                        sys.stdout.write("Received %d bytes\r" % cnt)
                        sys.stdout.flush()
            print()
            assert self.read_resp() == 0
        except Exception as e:
            return str(e)

    
    
    # Very simplified client handshake, works for MicroPython's
    # websocket server implementation, but probably not for other
    # servers.
    def client_handshake(self):
        try:
            cl = self.s.makefile("rwb", 0)
            t = cl.write(HANDSHAKE)
            l = cl.readline()
            while 1:
                l = cl.readline()
                if l == b"\r\n":
                    break
        except Exception as e:
            return str(e)         
    
    def sendString(self,strIn):
        try:
            tmp = strIn + "\r\n"
            bytesArray = tmp.encode("utf-8")    
            self.write(bytesArray,frame=WEBREPL_FRAME_TXT)
        except Exception as e:
            return str(e)
    
    def sendCtrlC(self):
        try:
            ctrl_c = ord('\x03')
            ctrl_c_byte = bytes([ctrl_c])
            self.write(ctrl_c_byte,frame=WEBREPL_FRAME_TXT)
        except Exception as e:
            return str(e)
        
    def close(self):
        self.s.close()
