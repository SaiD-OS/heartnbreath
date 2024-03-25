import tkinter as tk
import time
import serial.tools.list_ports as lp
import threading
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

class RootGUI():
    def __init__(self, parser, reader):
        self.parser = parser
        self.reader = reader
        self.root = tk.Tk()
        self.root.title("Heart and Breath")
        self.root.geometry("1000x700")
        self.root.config(bg="white")

        self.root.protocol("VM_DELETE_WINDOW", self.closeGUI)

    def closeGUI(self):
        self.root.destroy()


class SelectionGUI():
    def __init__(self, parser, reader, root):
        self.root = root
        self.parser = parser
        self.reader = reader
        self.frame = tk.LabelFrame(self.root, text="Com Manager", bg="white", padx=5, pady=5)
        self.lcom = tk.Label(self.frame, text="Port: ", bg="white", width=15, anchor="w")
        self.lbaud = tk.Label(self.frame, text="Baud Rate: ", bg="white", width=15, anchor="w")
        self.lradar = tk.Label(self.frame, text="Radar: ", bg="white", width=15, anchor="w")

        ports = lp.comports()
        self.comlist = [com[0] for com in ports]
        self.comlist.insert(0, "-")
        self.fcom = tk.StringVar()
        self.fcom.set(self.comlist[0])
        self.ddcom = tk.OptionMenu(self.frame, self.fcom, *self.comlist, command=self.enableconn)
        self.ddcom.config(width=20)

        self.baudlist = ["-", "9600", "115200"]
        self.fbaud = tk.StringVar()
        self.fbaud.set(self.baudlist[0])
        self.ddbaud = tk.OptionMenu(self.frame, self.fbaud, *self.baudlist, command=self.enableconn)
        self.ddbaud.config(width=20)

        self.radarlist = ["-", "24GHz MR24HPC1", "60GHz MR60BHA1"]
        self.fradar = tk.StringVar()
        self.fradar.set(self.radarlist[0])
        self.ddradar = tk.OptionMenu(self.frame, self.fradar, *self.radarlist, command=self.enableconn)
        self.ddradar.config(width=20)

        self.btnref = tk.Button(self.frame, text="Refresh", width=10,  command=self.comref)
        self.btnconn = tk.Button(self.frame, text="Connect", width=10, state="disabled", command=self.serconnect)

        self.frame.grid(row=0, column=0, rowspan=3, columnspan=3, padx=5, pady=5)
        self.lcom.grid(row=2, column=1)
        self.lbaud.grid(row=3, column=1)
        self.lradar.grid(row=4, column=1)
        self.ddcom.grid(row=2, column=2, padx=10, pady=5)
        self.ddbaud.grid(row=3, column=2, padx=10, pady=5)
        self.ddradar.grid(row=4, column=2, padx=10, pady=5)
        self.btnref.grid(row=2, column=3, padx=5)
        self.btnconn.grid(row=3, column=3, padx=5)

        
        self.plotter = PlotGUI(self.root, self.fradar)

    def comref(self):
        self.ddcom.destroy()
        ports = lp.comports()
        self.comlist = [com[0] for com in ports]
        self.comlist.insert(0, "-")
        self.fcom = tk.StringVar()
        self.fcom.set(self.comlist[0])
        self.ddcom = tk.OptionMenu(self.frame, self.fcom, *self.comlist, command=self.enableconn)
        self.ddcom.config(width=20)
        self.ddcom.grid(row=2, column=2, padx=10, pady=5)
        self.btnconn["state"] = "disabled"

    def enableconn(self, *args):
        if "-" in self.fbaud.get() or "-" in self.fcom.get() or "-" in self.fradar.get():
            self.btnconn["state"] = "disabled"
        else:
            self.btnconn["state"] = "active"

    def serconnect(self):
        if self.btnconn["text"] in "Connect":
            self.reader.SerialOpen(self.fcom.get(), self.fbaud.get())
            if self.reader.ser.status:
                self.btnconn["text"] = "Disconnect"
                self.btnref["state"] = "disabled"
                self.ddcom["state"] = "disabled"
                self.ddbaud["state"] = "disabled"
                self.reader.starttime = time.time()
                self.reader.t1 = threading.Thread(target=self.reader.SerialReceiveStream, daemon=True)
                self.reader.t1.start()    
                self.parser.t1 = threading.Thread(target=self.parser.decodeMsg, args=(self, self.fradar, 0, ), daemon=True)       
                self.parser.t1.start()  
        else:
            self.reader.SerialClose()
            self.btnconn["text"] = "Connect"
            self.reader.threading = False
            self.parser.threading = False
            

    def updateplots(self):
        try:
            for p in range(self.plotter.pltcnt):
                self.plotter.axis[p].clear()
                processingfn = self.parser.fnlist[self.plotter.fplt.get()]
                self.xd, self.yd = processingfn()
                self.plotter.axis[p].set_ylim(-10, 300)
                self.plotter.axis[p].plot(self.xd, self.yd)
                self.plotter.plots[p].draw()
        except Exception as e:
            print(e)

        if self.reader.threading:
            self.root.after(40, self.updateplots)

    def destroyplots(self):
        try:
            self.plotter.destroyGraphs()
        except:
            pass

class PlotGUI():
    def __init__(self, root, radartype):
        self.root = root
        self.radartype = radartype
        self.pltcnt = 0
        self.frames = []
        self.figs = []
        self.axis = []
        self.plots = []
        self.plotSelector()

    def plotSelector(self):
        self.pltframe = tk.LabelFrame(self.root, text="Plots", bg="white", padx=5, pady=5)
        self.lplttype = tk.Label(self.pltframe, text="Plot Type: ", bg="white", width=15, anchor="w")
        
        self.plotlist = ["-", "Fourier Transform", "Normal", "Heart"]
        self.fplt = tk.StringVar()
        self.fplt.set(self.plotlist[0])
        self.ddplt = tk.OptionMenu(self.pltframe, self.fplt, *self.plotlist, command=self.enableplt)
        self.ddplt.config(width=20)

        self.btnplt = tk.Button(self.pltframe, text="Select", width=10, state="disabled", command=self.plotGraph)

        self.pltframe.grid(row=0, column=4, rowspan=3, columnspan=3, padx=5, pady=5)
        self.lplttype.grid(row=2, column=1)
        self.ddplt.grid(row=2, column=2, padx=10, pady=5)
        self.btnplt.grid(row=2, column=3, padx=5)

    def enableplt(self, *args):
        if "-" in self.fplt.get():
            self.btnplt["state"] = "disabled"
        else:
            self.btnplt["state"] = "active"

    def plotGraph(self):
        self.destroyGraphs()
        if self.radartype.get() in "24GHz MR24HPC1":
            self.addGraph("Heart and Breath")
        else:
            self.addGraph("Heart")
            self.addGraph("Breath")

    def addGraph(self, name):
        self.frames.append(tk.LabelFrame(self.root, text=name, bg="white", padx=5, pady=5))
        self.figs.append(plt.Figure(figsize=(7,5), dpi=80))
        self.axis.append(self.figs[self.pltcnt].add_subplot())        
        self.plots.append(FigureCanvasTkAgg(self.figs[self.pltcnt], master=self.frames[self.pltcnt]))
        self.frames[self.pltcnt].grid(column=self.pltcnt*20, row=4, padx=5, pady=5, columnspan=20, rowspan=20)
        self.plots[self.pltcnt].get_tk_widget().grid(column=0, row=0)
        self.pltcnt = self.pltcnt + 1

    def destroyGraphs(self):
        while self.pltcnt > 0:
            self.pltcnt = self.pltcnt - 1
            self.figs[self.pltcnt].clear()
            self.axis[self.pltcnt].clear()
            plt.close(self.figs[self.pltcnt])
            self.frames[self.pltcnt].destroy()

        self.figs = []
        self.axis = []
        self.plots = []
        self.frames = []


if __name__ == "__main__":
    RootGUI()
    SelectionGUI()
    PlotGUI()
