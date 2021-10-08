#!/usr/bin/bash
# 

display="/usr/local/display/ssd1306_stats.py"

if [ -f $display ];then
        echo "running $display script"  
        /usr/bin/python3 $display
else
        echo "$display is not present, exiting"
exit 1
fi

