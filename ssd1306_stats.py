# SPDX-FileCopyrightText: 2017 Tony DiCola for Adafruit Industries
# SPDX-FileCopyrightText: 2017 James DeVito for Adafruit Industries
# SPDX-License-Identifier: MIT

# This example is for use on (Linux) computers that are using CPython with
# Adafruit Blinka to support CircuitPython libraries. CircuitPython does
# not support PIL/pillow (python imaging library)!
import math
import time
import subprocess
import re
import shutil

from board import SCL, SDA
import busio
from PIL import Image, ImageDraw, ImageFont
import adafruit_ssd1306

interval=1
cpu_last=[]
cpu_last_sum=0
display=['ip','cpu','mem','disk']

def get_meminfo():
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

def get_cpu_usage():
    global cpu_last
    global cpu_last_sum
    # logic taken from https://www.idnt.net/en-GB/kb/941772
    f=open('/proc/stat','r')
    sline=f.readline().split()
    sline.pop(0)
    cpu_now=list(map(int,sline))
    cpu_sum=sum(cpu_now)
    if cpu_last_sum != 0:
        cpu_delta=cpu_sum - cpu_last_sum
        cpu_idle=cpu_now[3]- cpu_last[3]
        cpu_used=cpu_delta - cpu_idle
        cpu_usage=100 * cpu_used / cpu_delta
        cpu_last=cpu_now
        cpu_last_sum=cpu_sum
        return(cpu_usage)
    else:
        cpu_last=cpu_now
        cpu_last_sum=cpu_sum
        return 0

def get_ip():
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


# Create the I2C interface.
i2c = busio.I2C(SCL, SDA)
# Create the SSD1306 OLED class.
# The first two parameters are the pixel width and pixel height.  Change these
# to the right size for your display!
disp = adafruit_ssd1306.SSD1306_I2C(128, 32, i2c)

# Clear display.
disp.fill(0)
disp.show()

# Create blank image for drawing.
# Make sure to create image with mode '1' for 1-bit color.
width = disp.width
height = disp.height
image = Image.new("1", (width, height))

def get_disk_usage():
     total, used, free = shutil.disk_usage("/")
     return("{:.0f}/{:.0f} GB".format(used/pow(2,30), total/pow(2,30)))

# Get drawing object to draw on image.
draw = ImageDraw.Draw(image)
# Draw a black filled box to clear the image.
draw.rectangle((0, 0, width, height), outline=0, fill=0)
# Load default font.
#font = ImageFont.load_default()
#font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 28)
font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)


font = ImageFont.load_default()
# Draw some shapes.
# First define some constants to allow easy resizing of shapes.
padding = -2
top = padding
bottom = height - padding
# Move left to right keeping track of the current x position for drawing shapes.
x = 0
while True:
    # Draw a black filled box to clear the image.
    draw.rectangle((0, 0, width, height), outline=0, fill=0)

    IP = "IP: " + get_ip()
    CPU="CPU: {:.0f}%".format(get_cpu_usage())
    meminfo=get_meminfo()
    MemUsage="Mem: {:.0f}/{:.0f} MB".format(meminfo[0],meminfo[1])
    Disk = "Disk: " + get_disk_usage()

    f=open("/sys/class/thermal/thermal_zone0/temp", "r")
    Temp = f.readline()
    Temp = "Temp: " + "{:.2f}".format(int(Temp) /1000) + chr(176) + "C"

    # Write four lines of text.

    if 'ip' in display:
        draw.text((x, top + 0), IP, font=font, fill=255)
    if 'cpu' in display:
        draw.text((x, top + 8), CPU + " " + Temp, font=font, fill=255)
    if 'mem' in display:
        draw.text((x, top + 16), MemUsage, font=font, fill=255)
    if 'disk' in display:
        draw.text((x, top + 25), Disk, font=font, fill=255)


    # Display image.
    disp.image(image)
    disp.show()
    time.sleep(interval)
