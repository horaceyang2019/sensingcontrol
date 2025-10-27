# -*- coding: utf-8 -*-
"""
Created on Sat Dec  4 16:56:52 2021

@author: Win10
"""
# In[1] TiHub_parameters

import modbus_tk
import sys
import logging
import modbus_tk.defines as cst
import modbus_tk.modbus_tcp as modbus_tcp


logger = modbus_tk.utils.create_logger("console")

if __name__ == "__main__":
    
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
        
        ''' 0x41 = TiHUB-01 address '''
        logger.info(master.execute(TiHUB_address, cst.READ_HOLDING_REGISTERS, 0, 16))

        ''' 52h~55h = 0x032 ,start-up,SamepleFrequency '''
        logger.info(master.execute(TiHUB_address, cst.WRITE_SINGLE_REGISTER, 82, output_value = SamepleFrequency))
        logger.info(master.execute(TiHUB_address, cst.WRITE_SINGLE_REGISTER, 83, output_value = SamepleFrequency))
        logger.info(master.execute(TiHUB_address, cst.WRITE_SINGLE_REGISTER, 84, output_value = SamepleFrequency))
        logger.info(master.execute(TiHUB_address, cst.WRITE_SINGLE_REGISTER, 85, output_value = SamepleFrequency))
    
        ''' 51h = 0x01 = AUTOLOG, 0x00 = no AUTOLOG '''
        logger.info(master.execute(TiHUB_address, cst.WRITE_SINGLE_REGISTER, 81, output_value = AUTOLOG))
        
        ''' 50h = 0x01 STARTMOD '''
        logger.info(master.execute(TiHUB_address, cst.WRITE_SINGLE_REGISTER, 80, output_value = STARTMOD))
        
        ''' 20h = 1B1(433,open), 1B0(432,close) '''
        logger.info(master.execute(TiHUB_address, cst.WRITE_SINGLE_REGISTER, 32, output_value = Open_switch))
        
        ''' 21h~24h = 0x032, SN1 data_rate = SamepleFrequency '''
        logger.info(master.execute(TiHUB_address, cst.WRITE_SINGLE_REGISTER, 33, output_value = SamepleFrequency))
        logger.info(master.execute(TiHUB_address, cst.WRITE_SINGLE_REGISTER, 34, output_value = SamepleFrequency))
        logger.info(master.execute(TiHUB_address, cst.WRITE_SINGLE_REGISTER, 35, output_value = SamepleFrequency))
        logger.info(master.execute(TiHUB_address, cst.WRITE_SINGLE_REGISTER, 36, output_value = SamepleFrequency))
        
        ''' 26h~2Ah = 0x40, Sensor Stream FIFO Buffer Length '''
        logger.info(master.execute(TiHUB_address, cst.WRITE_SINGLE_REGISTER, 38, output_value = Buffer_Length))
        logger.info(master.execute(TiHUB_address, cst.WRITE_SINGLE_REGISTER, 39, output_value = Buffer_Length))
        logger.info(master.execute(TiHUB_address, cst.WRITE_SINGLE_REGISTER, 40, output_value = Buffer_Length))
        logger.info(master.execute(TiHUB_address, cst.WRITE_SINGLE_REGISTER, 41, output_value = Buffer_Length))
        logger.info(master.execute(TiHUB_address, cst.WRITE_SINGLE_REGISTER, 42, output_value = Buffer_Length))
        
        ''' 2Ch = 0x01 '''
        logger.info(master.execute(TiHUB_address, cst.WRITE_SINGLE_REGISTER, 44, output_value = STRM_AUTO_LOG))
        
        ''' 2Dh = 1B1(433,open), 1B0(432,close) '''
        logger.info(master.execute(TiHUB_address, cst.WRITE_SINGLE_REGISTER, 45, output_value = Open_switch))


    except modbus_tk.modbus.ModbusError as exc:
        logger.error("%s- Code=%d", exc, exc.get_exception_code())
        
# In[2] TiHub_collection

import time
import datetime
import csv
import pandas as pd
import socket
import time
import math


''' TCP IP,Port (1505---Sensor_1) '''
HOST = '169.254.7.10'
PORT = 1505


''' TCP宣告 '''
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((HOST, PORT))

'''

ADDR, AXISx_1H, AXISx_1L, AXISy_1H, AXISy_1L, AXISz_1H, AXISz_1L, AXISx_2H, AXISx_2L, AXISy_2H, AXISy_2L, AXISz_2H, AXISz_2L,

'''

def find(num):
    
    while num >= 32768:
        num = num - 65535
    return num

time_start = datetime.datetime.now()
print('Start TiHUB-01')

buffer = []
counter = 0

try:
    while True:
         
        timetag = datetime.datetime.now()
        
        ''' 讀取 385 bytes'''
        indata = s.recv(385) 
        
        '''' 去除 0x43(C) '''
        cut = indata[1:]
        
        ''' 高低位元一起讀 '''
        step = 2        
        data = [cut[i:i+step] for i in range(0, len(cut), step)]
        
        for x in data:
            
            state_10 = int.from_bytes(x,byteorder='big')
            
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

except:
    
    step = 4
    final_data = [buffer[i:i+step] for i in range(0, len(buffer), step)]

    print('Finished TiHUB-01')
    time_end = datetime.datetime.now()
    print('Collect time', time_end-time_start)
    
    fileName = time_end.strftime(".\savefile/TiHUB-01_%Y%m%d_%H%M") + '.csv'
    
    ''' csv colums '''
    columns = ['Coretronic_X', 'Coretronic_Y', 'Coretronic_Z', 'Timetag']
    
    file = pd.DataFrame(columns = columns, data = final_data)

    file.to_csv(fileName, encoding = 'gbk')

    print('Write CSV finish')


