from GUI import RootGUI, SelectionGUI
from Parser import Parser
from Reader import SerialReader

par = Parser()
ser = SerialReader(par)
gui = RootGUI(par, ser)
sel = SelectionGUI(par, ser, gui.root)


gui.root.mainloop()