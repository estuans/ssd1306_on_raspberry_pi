
import time

import board
import busio
import digitalio
from PIL import Image, ImageDraw, ImageFont, ImageTk
import asyncio
from async_tkinter_loop import async_handler, async_mainloop
import tkinter as tk
from itertools import cycle
from widgets import Heartbeat, ClockWidget, ActivityWidget
import adafruit_ssd1306

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
        #self.display.draw_text((self.display.center_x - (font_width / 2), 0), self.name)
        self.display.draw_text((3, -1), self.name)
        if self.display.border == True:
         self.display.draw.rectangle((font_width + 4, 7, self.display.width - self.display.cl.width, 7 ), outline=255, fill=255)
        
        y_offset = 0
        y_idx = 1
        last_widget = None
        last_text_width = 0

        for idx, widget in enumerate(self.widgets):
            x_offset = 0
            if last_widget:
                if last_text_width == 0:
                    last_text_width = int(self.display.textsize(last_widget.value))

                this_text_width = int(self.display.textsize(widget.value))
                test_width = last_text_width + 2 + this_text_width
                if (test_width < self.display.width):
                    x_offset = last_text_width + 2
                    last_text_width = test_width
                    #y_offset = (y_idx - 1) * 8
                else:
                    # print("Too wide!")
                    # print(last_widget)
                    # print(widget)
                    y_idx += 1
                    last_text_width = 0
            
            y_offset = (y_idx) * 8
            widget.render(pos=(x_offset, y_offset))
            last_widget = widget

class Display:

    cur_page = None
    pages = []

    def __init__(self, font=None, page_pin=None, width=128, height=32,**kwargs):

        self.pages = []
        self.page_loop = cycle(self.pages)
            
        # Create blank image for drawing.
        # Make sure to create image with mode '1' for 1-bit color.
        self.width = width
        self.height = height
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
        padding = -1
        self.top = padding
        self.bottom = height - padding
        # Move left to right keeping track of the current x position for drawing shapes.
        self.x = 0

        self.border = kwargs.get("border", True)

        self.hb = Heartbeat(display=self)
        self.cl = ClockWidget(display=self)
        self.act = ActivityWidget(display=self)
        
        if page_pin:
            self.page_pin = page_pin

    def clear(self):
        # Draw a black filled box to clear the image.
        self.draw.rectangle((0, 0, self.width, self.height), outline=0, fill=0)

    def show(self):
        self.device.show()

    def draw_text(self, pos, val):
        self.draw.text(pos, val, font=self.font, fill=255)

    def update(self):
        # Display image.
        #self.device.image(self.image)
        #self.image.show()
        pass

    def check_input(self):
        # if self.page_pin.value:
        #     self.sleeps = 0
        #     self.next_page()
        #     print("Button Held!")
        pass

    def show_display(self):
        self.sleeps = 0
        self.next_page()
        while True:
            self.check_input()
            #self.clear()
            if self.sleeps == self.cur_page.interval: 
                self.next_page()
                self.clear()
                self.cur_page.render()
                self.sleeps = 0
            self.cl.render()
            self.hb.render()
            self.act.render()
            self.update()
            self.sleeps += 1
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

    def start():
        pass


class VirtualDisplay(Display):

    _scale_factor = 4

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.scaled_size = (int(self.image.width * self._scale_factor), int(self.image.height * self._scale_factor))
        self.init_hw(kwargs.get("width", 128), kwargs.get("height", 32))

    @property
    def scaled_image(self):
        return self.image.resize(self.scaled_size)

    def init_hw(self, width, height):
        self.window = window = tk.Tk()
        window.geometry(f"640x480")
        self.tk_img = ImageTk.PhotoImage(self.scaled_image)
        #self.device = tk.Label(window, image=self.tk_img)
        self.device = tk.Button(window, image=self.tk_img, command=self.show_display).pack()
        
    def update(self):
        # Display image.
        #self.device.imshow(self.image)
        self.tk_img.paste(self.scaled_image)
        #self.device.show()

    @async_handler
    async def show_display(self):
        self.sleeps = 0
        self.next_page()
        while True:
            self.check_input()
            #self.clear()
            if self.sleeps == self.cur_page.interval: 
                self.next_page()
                self.clear()
                self.cur_page.render()
                self.sleeps = 0
            self.hb.render()
            self.cl.render()
            self.act.render()
            self.update()
            self.sleeps += 1
            await asyncio.sleep(1)

    def start(self):
        async_mainloop(self.window)


class SSD1306Display(Display):

    def __init__(self, *args, **kwargs):
        self.init_hw(kwargs.get("width", 128), kwargs.get("height", 32))
        super().__init__(*args, **kwargs)


    def init_hw(self, width, height):
        # Create the I2C interface.
        i2c = busio.I2C(board.SCL, board.SDA)
        # Create the SSD1306 OLED class.
        # The first two parameters are the pixel width and pixel height.  Change these
        # to the right size for your display!
        self.device = device = adafruit_ssd1306.SSD1306_I2C(width, height, i2c)
        # Clear display.
        self.device.fill(0)
        self.device.show()


    def update(self):
        # Display image.
        self.device.image(self.image)
        self.device.show()

    def start(self):
        self.show_display()
