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
        self.root.geometry("%dx%d+0+0" % (self.root.winfo_screenwidth(), self.root.winfo_screenheight()))
        self.root.columnconfigure((0, 1, 2, 3, 4, 5, 6, 7, 8, 9), weight=1)
        self.root.rowconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=5)
        self.root.config(bg="white")

        self.root.protocol("VM_DELETE_WINDOW", self.closeGUI)

    def closeGUI(self):
        self.root.destroy()

class SelectionGUI():
    def __init__(self, parser, reader, root):
        self.root = root
        self.parser = parser
        self.reader = reader
        self.colorscheme = ['blue', 'red', 'green', 'cyan', 'magenta', 'yellow']
        self.createMainFrame()
        self.variableEditor()
        self.radarSettings()
        self.plotSettings()
        self.plotter = PlotGUI(self.root, self.fradar)    

    def mainFrameComponent(self, parent, ltext, ddarr, strvar, fncmd):
        frame = tk.Frame(master=parent, bg='white')
        tk.Label(frame, text=ltext, bg="white", width=10, anchor="w").grid(row=0, column=0)
        strvar.set(ddarr[0])
        dd = tk.OptionMenu(frame, strvar, *ddarr, command=fncmd)
        dd.config(width=15)
        dd.grid(row=0, column=1)
        return dd, frame

    def createMainFrame(self):
        self.frame = tk.LabelFrame(self.root, text="Com Manager", bg="white", padx=5, pady=5)

        ports = lp.comports()
        self.comlist = [com[0] for com in ports]
        self.comlist.insert(0, "-")
        self.fcom = tk.StringVar()

        self.baudlist = ["-", "9600", "115200"]
        self.fbaud = tk.StringVar()

        self.radarlist = ["-", "24GHz MR24HPC1", "60GHz MR60BHA1"]
        self.fradar = tk.StringVar()

        self.btnref = tk.Button(self.frame, text="Refresh", width=10,  command=self.comref)
        self.btnconn = tk.Button(self.frame, text="Connect", width=10, state="disabled", command=self.serreceive)
        self.btnreqdata = tk.Button(self.frame, text="Request", width=10, state="disabled", command=self.serrequestdata)

        self.ddcom, self.conframe = self.mainFrameComponent(self.frame, "Port", self.comlist, self.fcom, self.enableconn)

        self.frame.grid(row=0, column=0, columnspan=2, padx=5, sticky='nsew')
        self.conframe.grid(row=0, column=0)
        self.ddbaud, self.baudframe = self.mainFrameComponent(self.frame, "Baud Rate", self.baudlist, self.fbaud, self.enableconn)
        self.baudframe.grid(row=1, column=0)
        self.ddradar, self.radarselframe = self.mainFrameComponent(self.frame, "Radar", self.radarlist, self.fradar, self.enableconnwithsetupradar)
        self.radarselframe.grid(row=2, column=0)
        self.btnref.grid(row=0, column=1, padx=5)
        self.btnconn.grid(row=1, column=1, padx=5)
        self.btnreqdata.grid(row=2, column=1, padx=5)

    def variableFrameComponent(self, parent, ltext, setterfn):
        frame = tk.Frame(master=parent, bg='white')
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure((0,1,2), weight=1, uniform='a')
        tk.Label(frame, text=ltext, bg="white", width=10, anchor="w").grid(row=0, column=0)
        varVal = tk.StringVar()
        tk.Entry(frame, width=15, textvariable=varVal).grid(row=0, column=1)
        tk.Button(frame, text="Set", width=10, command= lambda: setterfn(varVal.get())).grid(row=0, column=2, padx=5)
        return frame
    
    def variableEditor(self):
        self.varframe = tk.LabelFrame(self.root, text="Variable Editor", bg="white", padx=5, pady=5)
        self.varframe.grid(row=0, column=6, columnspan=4, sticky='nsew')
        cnt = 0
        for k, v in self.parser.varlist.items():
            self.variableFrameComponent(self.varframe, k, v).grid(row=cnt%5, column=cnt//5)
            cnt+=1    

    def comref(self):
        for widget in self.conframe.winfo_children():
            widget.destroy()
        
        self.conframe.destroy()

        ports = lp.comports()
        self.comlist = [com[0] for com in ports]
        self.comlist.insert(0, "-")
        self.fcom = tk.StringVar()        
        self.ddcom, self.conframe = self.mainFrameComponent(self.frame, "Port", self.comlist, self.fcom, self.enableconn)
        self.conframe.grid(row=0, column=0)
        self.btnconn["state"] = "disabled"

    def enableconn(self, *args):
        if "-" in self.fbaud.get() or "-" in self.fcom.get() or "-" in self.fradar.get():
            self.btnconn["state"] = "disabled"
        else:
            self.btnconn["state"] = "active"

    def enableconnwithsetupradar(self, *args):
        self.enableconn(*args)
        self.ddrstngtype.destroy()
        self.settingtypelist = []
        if self.fradar.get() == "24GHz MR24HPC1":
            self.settingtypelist = [key for key in self.parser.settings24.keys()]
        elif self.fradar.get() == "60GHz MR60BHA1":
            self.settingtypelist = [key for key in self.parser.settings60.keys()]
        self.settingtypelist.insert(0, "-")
        self.frstngtype = tk.StringVar()
        self.frstngtype.set(self.settingtypelist[0])
        self.ddrstngtype = tk.OptionMenu(self.radarframe, self.frstngtype, *self.settingtypelist, command=self.btnsetup)
        self.ddrstngtype.config(width=30)
        self.ddrstngtype.grid(row=1, column=0)

    def radarSettings(self):
        self.radarframe = tk.LabelFrame(self.root, text="Radar Settings", bg="white", padx=5, pady=5)
        self.lrstngtype = tk.Label(self.radarframe, text='Setting Type', bg="white", width=15, anchor="w")
        self.btnsendpacket = tk.Button(self.radarframe, text="Inquire", width=10, command=self.sersend)
        self.settingtypelist = []
        if self.fradar.get() == "24GHz MR24HPC1":
            self.settingtypelist = [key for key in self.parser.settings24.keys()]
        elif self.fradar.get() == "60GHz MR60BHA1":
            self.settingtypelist = [key for key in self.parser.settings60.keys()]
        self.settingtypelist.insert(0, "-")
        self.frstngtype = tk.StringVar()
        self.frstngtype.set(self.settingtypelist[0])
        self.ddrstngtype = tk.OptionMenu(self.radarframe, self.frstngtype, *self.settingtypelist, command=self.btnsetup)
        self.ddrstngtype.config(width=30)
        self.evalrstngtype = tk.StringVar()
        self.entryrstngtype = tk.Entry(self.radarframe, width=30, textvariable=self.evalrstngtype)
        self.radarframe.grid(row=0, column=2, columnspan=2, sticky='nsew')
        self.lrstngtype.grid(row=0, column=0, sticky='w')
        self.ddrstngtype.grid(row=1, column=0, sticky='w')
        self.entryrstngtype.grid(row=2, column=0, sticky='we')
        self.btnsendpacket.grid(row=3, column=0, padx=5)

    def enableplotting1(self, *args):
        self.btnplot1["state"] = "disabled"
        for it in self.fpltlist1:
            if it.get() != "-":
                self.btnplot1["state"] = "active"
                break

    def enableplotting2(self, *args):
        self.btnplot2["state"] = "disabled"
        for it in self.fpltlist2:
            if it.get() != "-":
                self.btnplot2["state"] = "active"
                break

    def createoptions1(self):
        for it in self.ddpltlist1:
            it.destroy()

        self.btnplot1["state"] = "disabled"
        self.pltcnt1 = 0
        self.fpltlist1 = []
        self.ddpltlist1 = []
        try:
            val = int(self.evalplot1.get())
            for i in range(val):
                strvar = tk.StringVar()
                strvar.set(self.arrplt1[0])
                self.fpltlist1.append(strvar)
                dd = tk.OptionMenu(self.plotframe1, strvar, *self.arrplt1, command=self.enableplotting1)
                self.ddpltlist1.append(dd)
                dd.config(width=20)
                dd.grid(row=i+1, column=0, columnspan=3)
                self.pltcnt1+=1

            self.plotter.addAxis1(self.pltcnt1)
        except Exception as e:
            print(f"Enter a number {e}")

    def createoptions2(self):
        for it in self.ddpltlist2:
            it.destroy()

        self.btnplot2["state"] = "disabled"
        self.pltcnt2 = 0
        self.fpltlist2 = []
        self.ddpltlist2 = []
        try:
            val = int(self.evalplot2.get())
            for i in range(val):
                strvar = tk.StringVar()
                strvar.set(self.arrplt2[0])
                self.fpltlist2.append(strvar)
                dd = tk.OptionMenu(self.plotframe2, strvar, *self.arrplt2, command=self.enableplotting2)
                self.ddpltlist2.append(dd)
                dd.config(width=20)
                dd.grid(row=i+1, column=0, columnspan=3)
                self.pltcnt2+=1

            self.plotter.addAxis2(self.pltcnt2)
        except Exception as e:
            print(f"Enter a number {e}")

    def plotSettings(self):
        self.plotframe1 = tk.LabelFrame(self.root, text="Plot 1 Settings", bg="white", padx=5, pady=5)
        self.lplot1 = tk.Label(self.plotframe1, text='Plot Num', bg="white", width=10, anchor="w")
        self.evalplot1 = tk.StringVar()
        self.entryplot1 = tk.Entry(self.plotframe1, width=10, textvariable=self.evalplot1)
        self.btnplotgen1 = tk.Button(self.plotframe1, text="Gen", width=5, command=self.createoptions1)
        self.btnplot1 = tk.Button(self.plotframe1, text="Plot", state="disabled", width=5, command=self.startplotting1)
        self.plotframe1.grid(row=0, column=4, columnspan=1, padx=5, sticky='nsew')
        self.lplot1.grid(row=0, column=0)
        self.entryplot1.grid(row=0, column=1)
        self.btnplotgen1.grid(row=0, column=2)
        self.btnplot1.grid(row=0, column=3, padx=5)
        self.pltcnt1 = 0
        self.fpltlist1 = []
        self.ddpltlist1 = []
        self.arrplt1 = [key for key in self.parser.fnlist.keys()]
        self.arrplt1.insert(0, "-")

        self.plotframe2 = tk.LabelFrame(self.root, text="Plot 2 Settings", bg="white", padx=5, pady=5)
        self.lplot2 = tk.Label(self.plotframe2, text='Plot Num', bg="white", width=10, anchor="w")
        self.evalplot2 = tk.StringVar()
        self.entryplot2 = tk.Entry(self.plotframe2, width=10, textvariable=self.evalplot2)
        self.btnplotgen2 = tk.Button(self.plotframe2, text="Gen", width=5, command=self.createoptions2)
        self.btnplot2 = tk.Button(self.plotframe2, text="Plot", state="disabled", width=5, command=self.startplotting2)
        self.plotframe2.grid(row=0, column=5, columnspan=1, padx=5, sticky='nsew')
        self.lplot2.grid(row=0, column=0)
        self.entryplot2.grid(row=0, column=1)
        self.btnplotgen2.grid(row=0, column=2)        
        self.btnplot2.grid(row=0, column=3, padx=5)
        self.pltcnt2 = 0
        self.fpltlist2 = []
        self.ddpltlist2 = []
        self.arrplt2 = [key for key in self.parser.fnlist.keys()]
        self.arrplt2.insert(0, "-")

    def btnsetup(self, *args):
        val = self.frstngtype.get()
        bl = False
        if "-" != val:
            if self.fradar.get() == "24GHz MR24HPC1":
                bl = self.parser.settings24[val]["Inquiry"]
            elif self.fradar.get() == "60GHz MR60BHA1":
                bl = self.parser.settings60[val]["Inquiry"]

            if bl:
                self.btnsendpacket["text"] = "Inquire"
                self.entryrstngtype["state"] = "disabled"
            else:
                self.btnsendpacket["text"] = "Set Value"
                self.entryrstngtype["state"] = "normal"

    def serrequestdata(self):
        if self.fradar.get() == "60GHz MR60BHA1" and self.btnreqdata["text"] in "Request":
            self.btnreqdata["text"] = "Stop"
            msg = [83, 89, 133, 133, 0, 1, 15, 198, 84, 67]
            self.reader.t3 = threading.Thread(target=self.reader.SerialWriteStream, args=(msg, 0.5, True, ), daemon=True)
            self.reader.t3.start()
        else:
            self.reader.threadingw = False
            self.btnreqdata["text"] = "Request"
    
    def sersend(self):
        val = self.frstngtype.get()
        bl = False
        pack = []
        if "-" != val:
            if self.fradar.get() == "24GHz MR24HPC1":
                bl = self.parser.settings24[val]["Inquiry"]
                pack = self.parser.settings24[val]["Packet"]
            elif self.fradar.get() == "60GHz MR60BHA1":
                bl = self.parser.settings60[val]["Inquiry"]
                pack = self.parser.settings60[val]["Packet"]
            
            packc = pack.copy()

            if not bl:
                packc.append(int(self.evalrstngtype.get()))

            sumval = 0
            for item in packc:
                sumval += item

            packc.append(int(format(sumval, '02x')[-2:], 16))
            packc.append(84)
            packc.append(67)

            self.reader.t2 = threading.Thread(target=self.reader.SerialWriteStream, args=(packc, ), daemon=True)
            self.reader.t2.start()

    def serreceive(self):
        if self.btnconn["text"] in "Connect":
            self.reader.SerialOpen(self.fcom.get(), self.fbaud.get())
            if self.reader.ser.status:
                self.btnconn["text"] = "Disconnect"
                self.btnreqdata["state"] = "active"
                self.btnref["state"] = "disabled"
                self.ddcom["state"] = "disabled"
                self.ddbaud["state"] = "disabled"
                self.ddradar["state"] = "disabled"
                self.reader.starttime = time.time()
                self.reader.t1 = threading.Thread(target=self.reader.SerialReceiveStream, daemon=True)
                self.reader.t1.start()                     
        else:
            self.reader.SerialClose()
            self.btnconn["text"] = "Connect"
            self.btnreqdata["state"] = "disabled"
            self.btnref["state"] = "active"
            self.ddcom["state"] = "active"
            self.ddbaud["state"] = "active"
            self.ddradar["state"] = "active"
            self.reader.threadingr = False
            self.reader.threadingw = False
            
    def updateplots1(self):
        try:
            lines = None
            for p in range(self.pltcnt1):
                val = self.fpltlist1[p].get()
                if val != "-":
                    self.plotter.axis1[p].clear()
                    processingfn = self.parser.fnlist[val]
                    xd, yd = processingfn()                    
                    self.plotter.axis1[p].set_ylim(-10, 300)
                    l = self.plotter.axis1[p].plot(xd, yd, color=self.colorscheme[p], label=val)
                    if lines:
                        lines += l
                    else:
                        lines = l
            if self.pltcnt1 > 0:

                self.plotter.axis1[0].legend(lines, [x.get_label() for x in lines], loc='upper left')
            self.plotter.canvas1.draw()
        except Exception as e:
            print(e)

    def updateplots2(self):
        try:
            lines = None
            for p in range(self.pltcnt2):
                val = self.fpltlist2[p].get()
                if val != "-":
                    self.plotter.axis2[p].clear()
                    processingfn = self.parser.fnlist[val]
                    xd, yd = processingfn()
                    self.plotter.axis2[p].set_ylim(-10, 300)
                    l = self.plotter.axis2[p].plot(xd, yd, color=self.colorscheme[p], label=val)
                    if lines:
                        lines += l
                    else:
                        lines = l
            if self.pltcnt2 > 0:
                self.plotter.axis2[0].legend(lines, [x.get_label() for x in lines], loc='upper left')
            self.plotter.canvas2.draw()
        except Exception as e:
            print(e)

    def startplotting1(self):
        if self.btnplot1["text"] in "Plot":
            self.btnplot1["text"] = "Stop"
            self.btnplotgen1["state"] = "disabled"
            for it in self.ddpltlist1:
                it["state"] = "disabled"
            self.parser.t1 = threading.Thread(target=self.parser.decodeMsg1, args=(self.fradar.get(), self.updateplots1, ), daemon=True)       
            self.parser.t1.start() 
        else:
            self.btnplot1["text"] = "Plot"
            self.btnplotgen1["state"] = "active"
            for it in self.ddpltlist1:
                it["state"] = "active"
            self.parser.threading1 = False

    def startplotting2(self):
        if self.btnplot2["text"] in "Plot":
            self.btnplot2["text"] = "Stop"
            self.btnplotgen2["state"] = "disabled"
            for it in self.ddpltlist2:
                it["state"] = "disabled"
            self.parser.t2 = threading.Thread(target=self.parser.decodeMsg2, args=(self.fradar.get(), self.updateplots2, ), daemon=True)       
            self.parser.t2.start()
        else:
            self.btnplot2["text"] = "Plot"
            self.btnplotgen2["state"] = "active"
            for it in self.ddpltlist2:
                it["state"] = "active"
            self.parser.threading2 = False
         

class PlotGUI():
    def __init__(self, root, radartype):
        self.root = root
        self.radartype = radartype
        self.axis1 = []
        self.axis2 = []
        self.plotGraph()

    def plotGraph(self):
        self.pltframe1 = tk.LabelFrame(self.root, text="Plot 1", bg="white", padx=5, pady=5)
        self.fig1 = plt.Figure(figsize=(8,7), dpi=80)
        self.canvas1 = FigureCanvasTkAgg(self.fig1, master=self.pltframe1)
        self.pltframe1.grid(column=0, row=1, columnspan=5, padx=5, pady=5, sticky='nsew')
        self.canvas1.get_tk_widget().grid(column=0, row=0)

        self.pltframe2 = tk.LabelFrame(self.root, text="Plot 2", bg="white", padx=5, pady=5)
        self.fig2 = plt.Figure(figsize=(8,7), dpi=80)
        self.canvas2 = FigureCanvasTkAgg(self.fig2, master=self.pltframe2)
        self.pltframe2.grid(column=5, row=1, columnspan=5, padx=5, pady=5, sticky='nsew')
        self.canvas2.get_tk_widget().grid(column=0, row=0)

    def addAxis1(self, cnt):
        for it in self.axis1:
            it.remove()
        self.axis1 = []        
        self.fig1.clear()
        if cnt > 0:
            ax = self.fig1.add_subplot()
            self.axis1.append(ax)

        cnt-=1
        if cnt > 0:
            for i in range(cnt):
                self.axis1.append(ax.twinx())

    def addAxis2(self, cnt):
        for it in self.axis2:
            it.remove()
        self.axis2 = []
        self.fig2.clear()
        if cnt > 0:
            ax = self.fig2.add_subplot()
            self.axis2.append(ax)

        cnt-=1
        if cnt > 0:
            for i in range(cnt):
                self.axis2.append(ax.twinx())

if __name__ == "__main__":
    RootGUI()
    SelectionGUI()
    PlotGUI()
