# SPDX-FileCopyrightText: 2017 Tony DiCola for Adafruit Industries
# SPDX-FileCopyrightText: 2017 James DeVito for Adafruit Industries
# SPDX-License-Identifier: MIT

# This example is for use on (Linux) computers that are using CPython with
# Adafruit Blinka to support CircuitPython libraries. CircuitPython does
# not support PIL/pillow (python imaging library)!
import time
import re
import shutil

from board import SCL, SDA
import busio
import gpio as GPIO
from PIL import Image, ImageDraw, ImageFont
from itertools import cycle
import adafruit_ssd1306

interval=10
display=['ip','cpu','mem','disk']

def get_disk_usage():
     total, used, free = shutil.disk_usage("/")
     return("{:.0f}/{:.0f} GB".format(used/pow(2,30), total/pow(2,30)))


class Widget:

    name = ""
    position_x = 0
    position_y = 0 

    def __init__(self, position_x=0, position_y=0, page=None, display=None):
        self.position_x = position_x
        self.position_y = position_y

        if page:
            self.page = page

        if display:
            self.display = display

    def get_value(self):
        return 0

    @property
    def value(self):
        return self.get_value()

    def render(self, pos=None):
        if pos:
            pos_x, pos_y = pos
        else:
            pos_x = self.position_x
            pos_y = self.position_y

        self.page.display.draw_text(pos=(pos_x, pos_y), val=self.value)


class Page:
    height = 0
    width = 0
    name = ""

    def __init__(self, name="", height=0, width=0, interval=0, display=None):
        self.name = name
        self.display = display
        self.interval = interval
        self.widgets = []

        if height:
            self.height = height
        else:
            self. height = display.height
        if width:
            self.width = width
        else:
            self.width = display.width

    def add_widget(self, widget_class):
        w = widget_class(page=self)
        self.widgets.append(w)

    def render(self):
        font_width = self.display.textsize(self.name)
        self.display.draw_text((self.display.center_x - (font_width / 2), 0), self.name)
        #self.display.draw_text((self.display.center_x - (font_width / 2), 0), self.name)
        y_offset = 0
        for idx, widget in enumerate(self.widgets):
            y_offset = (idx + 1) * 8
            widget.render(pos=(0, y_offset))

class Heartbeat(Widget):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.shown = False

    def get_value(self):
        if not self.shown:
            self.shown = True
        else:
            self.shown = False

        return self.shown

    def render(self):
        disp = self.display
        val = self.value
        print(val)
        disp.draw.rectangle((disp.width -1, disp.height - 1, disp.width, disp.height), outline=val, fill=0)

class TempWidget(Widget):
    
    def get_value(self):
        with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
            temp = f.readline()
            temp = "Temp: " + "{:.2f}".format(int(temp) /1000) + chr(176) + "C"
        return temp

class MemWidget(Widget):

    def get_meminfo(self):
        with open('/proc/meminfo') as file:
            for line in file:
                if 'MemTotal' in line:
                    total_mem_in_kb = int(line.split()[1])
                if 'MemAvailable' in line:
                    available_mem_in_kb = int(line.split()[1])
                if 'Shmem' in line:
                    shared_mem_in_kb = int(line.split()[1])
                try:
                    if total_mem_in_kb and available_mem_in_kb and shared_mem_in_kb:
                        f.close()
                        break
                except:
                    continue
        used_mem_in_kb=total_mem_in_kb-available_mem_in_kb-shared_mem_in_kb
        return(used_mem_in_kb/1024, total_mem_in_kb/1024)

    def get_value(self):
        meminfo=self.get_meminfo()
        mem_usage="Mem: {:.0f}/{:.0f} MB".format(meminfo[0],meminfo[1])
        return mem_usage

class NetworkWidget(Widget):

    def get_ip(self):
        with open('/proc/net/fib_trie') as file:
                for line in file:
                        line=line.strip()
                        if line == 'Local:':
                                break
                        ipline=re.compile('\|-- (\S+)')
                        typeline=re.compile('32 host')
                        mi=ipline.search(line)
                        mt=typeline.search(line)
                        if mi is not None:
                                ip=mi.group(1)
                        if mt is not None and ip[0:5] != '127.0':
                                return(ip)


    def get_value(self):
        return "IP: " + self.get_ip()


class CPUWidget(Widget):

    cpu_last=[]
    cpu_last_sum=0

    def get_cpu_usage(self):
        # logic taken from https://www.idnt.net/en-GB/kb/941772
        f=open('/proc/stat','r')
        sline=f.readline().split()
        sline.pop(0)
        cpu_now=list(map(int,sline))
        cpu_sum=sum(cpu_now)
        if self.cpu_last_sum != 0:
            cpu_delta=cpu_sum - self.cpu_last_sum
            cpu_idle=cpu_now[3]- self.cpu_last[3]
            cpu_used=cpu_delta - cpu_idle
            cpu_usage=100 * cpu_used / cpu_delta
            self.cpu_last=cpu_now
            self.cpu_last_sum=cpu_sum
            return(cpu_usage)
        else:
            self.cpu_last=cpu_now
            self.cpu_last_sum=cpu_sum
            return 0

    def get_value(self):
        return "CPU: {:.0f}%".format(self.get_cpu_usage())

class Display:

    cur_page = None
    pages = []

    def __init__(self, font=None):

        self.pages = []
        self.page_loop = cycle(self.pages)
    
        # Create the I2C interface.
        i2c = busio.I2C(SCL, SDA)
        # Create the SSD1306 OLED class.
        # The first two parameters are the pixel width and pixel height.  Change these
        # to the right size for your display!
        self.disp = disp = adafruit_ssd1306.SSD1306_I2C(128, 32, i2c)

        # Clear display.
        self.disp.fill(0)
        self.disp.show()

        # Create blank image for drawing.
        # Make sure to create image with mode '1' for 1-bit color.
        self.width = width = disp.width
        self.height = height = disp.height
        
        self.center_x = width / 2
        self.center_y = height / 2

        self.image = image = Image.new("1", (self.width, self.height))

        # Get drawing object to draw on image.
        self.draw = draw = ImageDraw.Draw(image)
        # Draw a black filled box to clear the image.
        draw.rectangle((0, 0, width, height), outline=0, fill=0)
        # Load default font.
        #font = ImageFont.load_default()
        #font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 28)
        if font:
            self.font = font = ImageFont.truetype(*font)
        else:
            self.font = font = ImageFont.load_default()
        # Draw some shapes.
        # First define some constants to allow easy resizing of shapes.
        padding = -2
        self.top = padding
        self.bottom = height - padding
        # Move left to right keeping track of the current x position for drawing shapes.
        self.x = 0

        self.hb = Heartbeat(display=self)

    def clear(self):
        # Draw a black filled box to clear the image.
        self.draw.rectangle((0, 0, self.width, self.height), outline=0, fill=0)

    def show(self):
        self.disp.show()

    def draw_text(self, pos, val):
        self.draw.text(pos, val, font=self.font, fill=255)

    def update(self):
        # Display image.
        self.disp.image(self.image)
        self.disp.show()

    def show_display(self):
        sleeps = 0
        self.next_page()
        while True:
            self.clear()
            if sleeps == self.cur_page.interval: 
                self.next_page()
            self.cur_page.render()
            self.hb.render()
            self.update()
            sleeps += 1
            time.sleep(1)

    def add_page(self, name, idx=0, interval=1):
        p = Page(name, interval=interval, display=self)
        self.pages.insert(idx, p)
        return p

    def get_page(self, idx):
        return self.pages[idx]

    def next_page(self):
        p = next(self.page_loop)
        self.cur_page = p
        return p

    def textsize(self, text, font=None):
        if font == None:
            font = self.font
        w = self.draw.textlength(text, font)
        return w

if __name__ == "__main__":
    #disp = Display(font=("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 9))
    disp = Display()

    temp_page = disp.add_page(name="Temperature", interval=5)
    temp_page.add_widget(TempWidget)

    sys_page = disp.add_page(name="System", interval=10)
    sys_page.add_widget(CPUWidget)
    sys_page.add_widget(MemWidget)

    disp.show_display()


# ip = "IP: " + get_ip()
# cpu ="CPU: {:.0f}%".format(get_cpu_usage())
# meminfo=get_meminfo()
# mem_usage="Mem: {:.0f}/{:.0f} MB".format(meminfo[0],meminfo[1])
# disk = "Disk: " + get_disk_usage()

# f=open("/sys/class/thermal/thermal_zone0/temp", "r")
# temp = f.readline()
# temp = "Temp: " + "{:.2f}".format(int(temp) /1000) + chr(176) + "C"

# # Write four lines of text.

# if 'ip' in display:
#     disp.draw_text(pos=(disp.x, disp.top + 0), val=ip)
# if 'cpu' in display:
#     disp.draw_text((disp.x, disp.top + 8), val=cpu + " " + temp)
# if 'mem' in display:
#     disp.draw_text((disp.x, disp.top + 16), mem_usage)
# if 'disk' in display:
#     disp.draw_text((disp.x, disp.top + 25), disk)