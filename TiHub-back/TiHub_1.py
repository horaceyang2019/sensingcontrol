# -*- coding: utf-8 -*-
"""
Created on Sat Dec  4 16:56:52 2021

@author: Win10
"""

''' Read path = ./Read/Tongtai_TiHUB-01_UM_v0.1.0 '''
''' 若未更改 SamepleFrequency 直接從 #In[4]執行 '''


# In[1]: 
import modbus_tk
import sys
import logging
import modbus_tk.defines as cst
import modbus_tk.modbus_tcp as modbus_tcp

import time
import datetime
import csv
import pandas as pd
import socket
import time
import math
import threading
import numpy as np

file_location = ".\savefile/TiHUB-01_%Y%m%d_%H%M"

# In[2]: 
def configure_Hub(): 
    ''' 暫存器參數設定 '''
    ''' After setting, Restart TiHUB-01 by power-down and power-up again '''
    ''' HUB IP = 169.254.7.10, HUB PORT = 502 '''
    
    HOST = '169.254.7.10' 
    PORT = 502
    TiHUB_address = 0x41
    SamepleFrequency = 1600
    Open_switch = 433
    Close_switch = 432
    Buffer_Length = 64
    AUTOLOG = 1
    STARTMOD = 1
    STRM_AUTO_LOG = 1
    
    try:
        
        ''' modbus TCP IP,Port '''
        master = modbus_tcp.TcpMaster(host = HOST, port = PORT)
        master.set_timeout(1)
        
        ''' 0x41 = TiHUB-01 address (by 5-2 (p27)) '''
        logger.info(master.execute(TiHUB_address, cst.READ_HOLDING_REGISTERS, 0, 16))

        ''' 52h~55h = 0x032 ,start-up,SamepleFrequency (by 3-3 (p14)) '''
        logger.info(master.execute(TiHUB_address, cst.WRITE_SINGLE_REGISTER, 82, output_value = SamepleFrequency))
        logger.info(master.execute(TiHUB_address, cst.WRITE_SINGLE_REGISTER, 83, output_value = SamepleFrequency))
        logger.info(master.execute(TiHUB_address, cst.WRITE_SINGLE_REGISTER, 84, output_value = SamepleFrequency))
        logger.info(master.execute(TiHUB_address, cst.WRITE_SINGLE_REGISTER, 85, output_value = SamepleFrequency))
    
        ''' 51h = 0x01 = AUTOLOG, 0x00 = no AUTOLOG (by 3-3 (p14))'''
        logger.info(master.execute(TiHUB_address, cst.WRITE_SINGLE_REGISTER, 81, output_value = AUTOLOG))
        
        ''' 50h = 0x01 STARTMOD (by 3-3 (p14)) '''
        logger.info(master.execute(TiHUB_address, cst.WRITE_SINGLE_REGISTER, 80, output_value = STARTMOD))
        
        ''' 20h = 1B1(433,open), 1B0(432,close) (by 3-3 (p14)) '''
        logger.info(master.execute(TiHUB_address, cst.WRITE_SINGLE_REGISTER, 32, output_value = Open_switch))
        
        ''' 21h~24h = 0x032, SN1 data_rate = SamepleFrequency (by 3-5 (p14)) '''
        logger.info(master.execute(TiHUB_address, cst.WRITE_SINGLE_REGISTER, 33, output_value = SamepleFrequency))
        logger.info(master.execute(TiHUB_address, cst.WRITE_SINGLE_REGISTER, 34, output_value = SamepleFrequency))
        logger.info(master.execute(TiHUB_address, cst.WRITE_SINGLE_REGISTER, 35, output_value = SamepleFrequency))
        logger.info(master.execute(TiHUB_address, cst.WRITE_SINGLE_REGISTER, 36, output_value = SamepleFrequency))
        
        ''' 26h~2Ah = 0x40, Sensor Stream FIFO Buffer Length (by 3-5 (p15)) '''
        logger.info(master.execute(TiHUB_address, cst.WRITE_SINGLE_REGISTER, 38, output_value = Buffer_Length))
        logger.info(master.execute(TiHUB_address, cst.WRITE_SINGLE_REGISTER, 39, output_value = Buffer_Length))
        logger.info(master.execute(TiHUB_address, cst.WRITE_SINGLE_REGISTER, 40, output_value = Buffer_Length))
        logger.info(master.execute(TiHUB_address, cst.WRITE_SINGLE_REGISTER, 41, output_value = Buffer_Length))
        logger.info(master.execute(TiHUB_address, cst.WRITE_SINGLE_REGISTER, 42, output_value = Buffer_Length))
        
        ''' 2Ch = 0x01 (by 3-5 (p15)) '''
        logger.info(master.execute(TiHUB_address, cst.WRITE_SINGLE_REGISTER, 44, output_value = STRM_AUTO_LOG))
        
        ''' 2Dh = 1B1(433,open), 1B0(432,close) (by 3-5 (p15)) '''
        logger.info(master.execute(TiHUB_address, cst.WRITE_SINGLE_REGISTER, 45, output_value = Open_switch))

    except modbus_tk.modbus.ModbusError as exc:
        logger.error("%s- Code=%d", exc, exc.get_exception_code())
        
        
# In[4]
def find(num):
      
    ''' 1 111111111111111    1→負 需變換 1→0  0→1 '''
    ''' 0 111111111111111    0→正 保持不變 '''
    ''' 10000000000000000 = 32768 ,只要大於32767就是負數 '''
    
    while num >= 32768:
        num = num - 65535
    return num

# In[5]: 
def collect():
    
    counter = 0
    while True:
        
        buffer = []
        timetag = datetime.datetime.now()
        
        ''' 讀取 385 bytes'''
        indata = s.recv(385) 
        ''' 去除 0x43(C) '''
        cut = indata[1:]
        
        ''' 高低位元一起讀 '''
        step = 2  
        data = [cut[i:i+step] for i in range(0, len(cut), step)]    
    
        for x in data:
            
            state_10 = int.from_bytes(x, byteorder='big')
            
            final = find(state_10)/2048
            
            if len(indata) == 0: 
                s.close()
                print('server closed connection.')
                break       
            else:
                buffer.append(final)
                counter += 1
                if(counter == 3):
                    buffer.append(timetag)
                    counter = 0
                      
        step = 4
        final_data = [buffer[i:i+step] for i in range(0, len(buffer), step)]
           
    return final_data
 
# In[6]:       
def save(file_location, samples):
    
    time_end = datetime.datetime.now()
    file_name = time_end.strftime(file_location) + '.csv'
    # columns = ['X','Y','Z','Timetag']
    columns = ['Coretronic_X','Coretronic_Y','Coretronic_Z']
    file = pd.DataFrame(columns = columns, data = samples)

    file.to_csv(file_name, encoding = 'gbk')

    # print('Write CSV finish')

# In[7]
if __name__ == "__main__":
    
    ''' 暫存器參數設定 '''
    ''' After setting, Restart TiHUB-01 by power-down and power-up again '''
    
    logger = modbus_tk.utils.create_logger("console")        
    configure_Hub()
    
    ''' Coretronic 資料收集 '''
    
    time_start = datetime.datetime.now()
    print('Start TiHUB-01')

    ''' TCP IP,Port (1505---Sensor_1) '''
    HOST = '169.254.7.10'
    PORT = 1505
    
    ''' TCP宣告 '''
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((HOST, PORT))
    
    try:
        samples = collect()
    except:
        save(file_location, samples)
  


