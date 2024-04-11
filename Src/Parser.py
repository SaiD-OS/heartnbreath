import threading
import time
import json
from queue import Queue
import numpy as np

class Parser():
    def __init__(self):
        self.msgq = Queue()
        self.xd = []
        self.yd = []
        self.len = 0
        self.fs = 5
        self.hlp = 1
        self.hhp = 1.3
        self.bhp = 0.3
        self.blp = 0.36
        self.lenthresh = 200
        self.threading1 = False

        # contains functions used to manipulate data for plotting
        self.fnlist = {
            "Normal": self.plainData,
            "Heart": self.heartData,
            "FFT": self.fouriertransform
        }

        # contains setter functions for your variable
        self.varlist = {
            'Threshold': self.setlenthresh,
            'Heart HPF': self.sethhp,
            'Heart LPF': self.sethlp,
            'Sample': self.fs,
            'Breath LPF': self.setblp,
        }

        self.settings24 = json.load(open('Config/settings24GHz.json'))

        self.settings60 = json.load(open('Config/settings60GHz.json'))

    def setsampleval(self, val):
        self.fs = int(val)

    def setlenthresh(self, val):
        self.lenthresh = int(val)

    def sethhp(self, val):
        self.hhp = float(val)

    def sethlp(self, val):
        self.hlp = float(val)

    def setbhp(self, val):
        self.bhp = float(val)

    def setblp(self, val):
        self.blp = float(val)

    def decodeMsg1(self, radartype, fn):
        self.threading1 = True
        while self.threading1:
            try:
                currmsg = self.msgq.get()

                if currmsg is None:
                    break

                if radartype == "24GHz MR24HPC1":
                    self.decodeEnergySignals(currmsg)
                else:
                    self.decodeHeartSignals(currmsg)

                fn()
            except Exception as e:
                print(e)

    def decodeMsg2(self, radartype, fn):
        self.threading2 = True
        while self.threading2:
            try:
                if not self.threading1:
                    currmsg = self.msgq.get()

                    if currmsg is None:
                        break

                    if radartype == "24GHz MR24HPC1":
                        self.decodeEnergySignals(currmsg)
                    else:
                        self.decodeHeartSignals(currmsg)
                fn()
            except Exception as e:
                print(e)

    def decodeEnergySignals(self, msg):
        cntent = msg['msg']
        if cntent != None and len(cntent) >= 5 and ord(cntent[0]) == 8 and ord(cntent[1]) == 1:
            self.yd.append(ord(cntent[4]))
            self.xd.append(msg['time'])
            self.len += 1

            if self.len > self.lenthresh:
                self.yd.pop(0)
                self.xd.pop(0)
                self.len-=1

    def decodeHeartSignals(self, msg):
        curr = msg['msg']
        ti = msg['time'] + 1     
        if curr != None and len(curr) >= 9 and ord(curr[0]) == 133 and (ord(curr[1]) == 5 or ord(curr[1]) == 133):
            self.yd.append(ord(curr[4]))
            self.yd.append(ord(curr[5]))
            self.yd.append(ord(curr[6]))
            self.yd.append(ord(curr[7]))
            self.yd.append(ord(curr[8]))
            self.xd.append(ti - 0.8)
            self.xd.append(ti - 0.6)            
            self.xd.append(ti - 0.4)
            self.xd.append(ti - 0.2)
            self.xd.append(ti)
            self.len+=5

            templ = sorted(zip(self.xd, self.yd))
            self.xd = [x for x, y in templ]
            self.yd = [y for x, y in templ]


            while self.len > self.lenthresh:
                self.yd.pop(0)
                self.xd.pop(0)
                self.len-=1
        elif curr != None and len(curr) >= 5 and ord(curr[0]) == 132 and ord(curr[1]) == 140:
            print(curr[4])

    def plainData(self):
        return self.xd, self.yd

    def heartData(self):
        ti = self.xd
        hWave = self.allPass(np.array(self.yd), self.hhp, self.fs, highP=True)
        hWave = self.allPass(hWave, self.hlp, self.fs)
        return ti, hWave

    def breathData(self):
        ti = self.xd
        bWave = self.allPass(np.array(self.yd), self.bhp, self.fs, highP=True)
        bWave = self.allPass(bWave, self.blp, self.fs)
        return ti, bWave

    def fouriertransform(self):
        fft = np.fft.fft(self.yd)/20
        freqdomain = np.fft.fftfreq(len(self.yd), 1/self.fs)
        return freqdomain, np.abs(fft)

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