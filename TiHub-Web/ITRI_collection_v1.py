# -*- coding: utf-8 -*-
"""
Created on Fri Apr 24 21:14:58 2020

@author: HengZhi
"""
import serial  # 引用pySerial模組
import datetime
import csv
import pandas as pd

COM_PORT = 'COM6'    # 指定通訊埠名稱 "/dev/ttyACM0"
BAUD_RATES = 9600    # 設定傳輸速率 
ser = serial.Serial(COM_PORT, BAUD_RATES)   # 初始化序列通訊埠
command = [0x78,0x56,0x34,0x12,0x02,0x08,0x00,0x00,0x03,0x40,0x01]
ser.write(serial.to_bytes(command))

buffer ,timetag= [],[]
# In[]m
def Convert_to_G (data):

    x = ('0x'+data[4:6]) + (data[2:4])
    y = ('0x'+data[8:10]) + (data[6:8])
    z = ('0x'+data[12:14]) + (data[10:12])
    x = int(x,16)
    y = int(y,16)
    z = int(z,16)
    if x >32767:
        x1=-(2**16-x)
        X_G_value = ((x1)/8192)+0.72
    else:
        X_G_value = ((x)/8192)+0.72
    if y >32767:
        y1=-(2**16-y)
        Y_G_value = ((y1)/8192)-0.226
    else:
        Y_G_value = ((y)/8192)-0.226
    if z >32767:
        z1=-(2**16-z)
        Z_G_value = ((z1)/8192)+0.575
    else:
        Z_G_value = ((z)/8192)+0.575
    
    time = datetime.datetime.now()     #0.05
    timetag = time.strftime("%Y-%m-%d-%H-%M-%S")    
    return X_G_value,Y_G_value,Z_G_value,timetag

# In[] 0x000004E2=1250  0x000007D0=2000  
def main():   
    time_start = datetime.datetime.now() 
    print('Start ITRI')
    
    try:
        while True:
            while ser.in_waiting:
                data_raw = ser.read(8)
                data = data_raw.hex()
                if data[0:2] == '1e':
                    continue
                else:
                    buffer.append(Convert_to_G(data))              
    except:
        ser.close()
        print('Finished ITRI')
        time_end = datetime.datetime.now()
        print('Collect time',time_end-time_start)    
        fileName = time_end.strftime("ITRI_%Y%m%d_%H%M") + '.csv'
        columns=['X','Y','Z','Timetag']
        # columns=['X','Y','Z']
        file=pd.DataFrame(columns=columns,data=buffer)
        file.to_csv(fileName,encoding='gbk',index=None)
        print('Write CSV finish')

# In[101]
if __name__ == '__main__': 
    main()