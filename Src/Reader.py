import threading
import time
import serial

class SerialReader():
    def __init__(self, parser):
        self.sync_count = 200
        self.msghead1 = b'S'
        self.msghead2 = b'Y'
        self.msgtrail1 = b'T'
        self.msgtrail2 = b'C'
        self.newline = b'\n'
        self.newdata = False
        self.starttime = -1
        self.fintime = -1
        self.threading = False

        self.parser = parser

    def SerialOpen(self, comport, baudrate):
        try:
            if self.ser.is_open:
                self.ser.status = True
        except:
            self.ser = serial.Serial()
            self.ser.baudrate = int(baudrate)
            self.ser.port = comport
            self.ser.timeout = 0.01
            self.ser.open()
            self.ser.status = True

    def SerialClose(self):
        try:
            if self.ser.is_open:
                self.ser.close()
                self.ser.status = False
        except:
            self.ser.status = False

    def SerialReceiveStream(self):
        while True:
            try:             
                if self.ser.read() == self.msghead1:
                    self.msg = []        
                    if self.ser.read() == self.msghead2:
                        while True:
                            self.char = self.ser.read()                                                      
                            if self.char == self.msgtrail1:                               
                                if self.ser.read() == self.msgtrail2:
                                    break
                                else:
                                    print("Error")
                                    break
                            if self.char != self.newline:
                                self.msg.append(self.char)
                        self.fintime = time.time()
                        self.newdata = True
                if self.newdata:
                    self.parser.msgq.put({'msg':self.msg, 'time':self.fintime-self.starttime})
                    self.newdata = False
            except Exception as e:
                print(e)