from display import Page, VirtualDisplay
from widgets import *

if __name__ == "__main__":
    
    disp = VirtualDisplay(font=("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 9), width=128, height=32)
    #disp = VirtualDisplay(width=128, height=32)
    #disp = Display()

    sys_page = disp.add_page(name="System", interval=10)
    sys_page.add_widget(CPUWidget)
    sys_page.add_widget(MemWidget)
    sys_page.add_widget(DiskWidget)
    sys_page.add_widget(TempWidget)

    net_page = disp.add_page(name="Network", interval=5)
    net_page.add_widget(NetworkWidget)

    disp.start()    