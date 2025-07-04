# SPDX-FileCopyrightText: 2017 Tony DiCola for Adafruit Industries
# SPDX-FileCopyrightText: 2017 James DeVito for Adafruit Industries
# SPDX-License-Identifier: MIT

# This example is for use on (Linux) computers that are using CPython with
# Adafruit Blinka to support CircuitPython libraries. CircuitPython does
# not support PIL/pillow (python imaging library)!
import time

from board import SCL, SDA
import busio
import gpio as GPIO
from PIL import Image, ImageDraw, ImageFont
from itertools import cycle
import adafruit_ssd1306

from widgets import *

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
                sleeps = 0
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
    disp = Display(font=("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 9))
    #disp = Display()

    temp_page = disp.add_page(name="Temperature", interval=5)
    temp_page.add_widget(TempWidget)

    sys_page = disp.add_page(name="System", interval=10)
    sys_page.add_widget(CPUWidget)
    sys_page.add_widget(MemWidget)
    sys_page.add_widget(DiskWidget)

    net_page = disp.add_page(name="Network", interval=5)
    net_page.add_widget(NetworkWidget)

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