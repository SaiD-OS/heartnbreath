import threading
import time
from queue import Queue
import numpy as np

class Parser():
    def __init__(self):
        self.msgq = Queue()
        self.xd = []
        self.yd = []
        self.len = 0
        self.lenthresh = 500
        self.threading = False

        self.fnlist = {
            "Normal": self.plainData,
            "Heart": self.heartData
        }

    def decodeMsg(self, plotter, radartype, datatype):
        while True:
            self.currmsg = self.msgq.get()

            if self.currmsg is None:
                break

            # if self.radartype == "24GHz":
            self.decodeEnergySignals(datatype)
            plotter.updateplots()


    def decodeEnergySignals(self, datatype):
        self.currcontent = self.currmsg['msg']
        if len(self.currcontent) >= (datatype + 5) and ord(self.currcontent[0]) == 8 and ord(self.currcontent[1]) == 1:
            self.yd.append(ord(self.currcontent[4+datatype]))
            self.xd.append(self.currmsg['time'])
            self.len += 1

            if self.len > self.lenthresh:
                self.yd.pop(0)
                self.xd.pop(0)
                self.len-=1

    def plainData(self):
        return self.xd, self.yd

    def heartData(self):
        fs = 7
        ti = self.xd
        hWave = self.allPass(np.array(self.yd), 0.1, fs, highP=True)
        hWave = self.allPass(hWave, 0.4, fs)
        return ti, hWave

    def allPass(self, inputSig, cutOffF, fs, highP = False, ampScale = 1):
        leng = len(inputSig)
        dn1 = 0
        allPassOut = []
        for it in inputSig:
            tan = np.tan(np.pi*cutOffF/fs)
            a1 = (tan-1)/(tan+1)
            currOut = a1*it + dn1
            allPassOut.append(currOut)
            dn1 = it - a1*currOut

        if highP:
            return np.abs((inputSig - allPassOut)*0.5*ampScale)

        return np.abs((inputSig + allPassOut)*0.5*ampScale)