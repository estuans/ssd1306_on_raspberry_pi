import shutil
import re


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
        #print(val)
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



class DiskWidget(Widget):

    def get_value(self):
        total, used, free = shutil.disk_usage("/")
        return("{:.0f}/{:.0f} GB".format(used/pow(2,30), total/pow(2,30)))

