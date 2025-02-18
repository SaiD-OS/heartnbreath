import threading
import time
import serial
import csv
import datetime

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
        self.threadingr = False

        self.parser = parser

    def SerialOpen(self, comport, baudrate):
        try:
            if self.ser.is_open:
                self.ser.status = True
        except Exception as e:
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
                self.ser = None
        except Exception as e:
            self.ser.status = False

    def SerialReceiveStream(self):
        self.threadingr = True
        filename = "Logs/radarddata-" + "{:%Y%m%d-%H%M%S}".format(datetime.datetime.now()) + ".csv"
        while self.threadingr:
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
                                    # print("Packet discarded")
                                    break
                            if self.char != self.newline:
                                self.msg.append(self.char)
                        self.fintime = time.time()
                        self.newdata = True
                if self.newdata:
                    timeval = self.fintime-self.starttime
                    self.t4 = threading.Thread(
                            target=self.SaveRawData, args=(self.msg, timeval, filename, ), daemon=True)
                    self.t4.start()
                    self.parser.msgq.put({'msg':self.msg, 'time':timeval})
                    self.newdata = False
            except Exception as e:
                pass
    
    def SerialWriteStream(self, msg = [], period=1, cyclic=False):
        self.threadingw=True
        while self.threadingw:
            try:
                for it in msg:
                    self.ser.write(it.to_bytes(1, 'little'))

                if cyclic:
                    time.sleep(period)
                else:
                    self.threadingw = False
            except Exception as e:
                print(e)


    def SaveRawData(self, msgval, timeval, filename):
        data = msgval.copy()
        data.insert(0, timeval)
        with open(filename, 'a') as csvfile:  
            csvwriter = csv.writer(csvfile)
            csvwriter.writerow(data)  