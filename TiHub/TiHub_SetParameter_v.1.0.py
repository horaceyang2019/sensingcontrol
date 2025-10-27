# -*- coding: utf-8 -*-
"""
Created on Sat Dec  4 16:56:52 2021

@author: Win10
"""

import modbus_tk
import modbus_tk.defines as cst
import modbus_tk.modbus_tcp as modbus_tcp
import datetime
import pandas as pd
import socket

# In[1]
'''
   The parameters and registers of TiHub 
'''
Hub_host = '169.254.7.10'
register_port = 502        # TCP/IP port of TiHUB for setting registers 
sensor_1_port = 1505       # TCP/IP Port of TiHUB for Sensor_1
TiHUB_address = 0x41       # HUB address  
sameple_frequency = 1600   # sampling rate from Hub
open_switch = 433          # command to open switch
close_switch = 432         # command to close switch
axis_buffer_length = 64    # the maximum buffer length in bytes
axis_number = 3
autolog = 1                # auto logging
start_mode = 1             # start 
Strm_autolog = 1           

data_bytes = 2     
data_length = 385          # header + axes* bytes * axis_buffer_length = 1 + 3*2*64
resolution = 2048          # 12 bits

# In[10]
'''
    Set the registers of Hub to collect the data in the specified frequency and operation mode
'''
def SetRegister():
    logger = modbus_tk.utils.create_logger("console")
    try:     
        ''' modbus TCP IP,Port '''
        master = modbus_tcp.TcpMaster(host = Hub_host, port = register_port)
        master.set_timeout(1)
        
        ''' 0x41: TiHUB-01 address '''
        logger.info(master.execute(TiHUB_address, cst.READ_HOLDING_REGISTERS, 0, 16))

        ''' 52h~55h: 0x032, start-up, SamepleFrequency '''
        logger.info(master.execute(TiHUB_address, cst.WRITE_SINGLE_REGISTER, 82, output_value = sameple_frequency))
        logger.info(master.execute(TiHUB_address, cst.WRITE_SINGLE_REGISTER, 83, output_value = sameple_frequency))
        logger.info(master.execute(TiHUB_address, cst.WRITE_SINGLE_REGISTER, 84, output_value = sameple_frequency))
        logger.info(master.execute(TiHUB_address, cst.WRITE_SINGLE_REGISTER, 85, output_value = sameple_frequency))
    
        ''' 51h: 0x01 = AUTOLOG, 0x00 = no AUTOLOG '''
        logger.info(master.execute(TiHUB_address, cst.WRITE_SINGLE_REGISTER, 81, output_value = autolog))
        
        ''' 50h: 0x01 STARTMOD '''
        logger.info(master.execute(TiHUB_address, cst.WRITE_SINGLE_REGISTER, 80, output_value = start_mode))
        
        ''' 20h: 1B1(433,open), 1B0(432,close) '''
        logger.info(master.execute(TiHUB_address, cst.WRITE_SINGLE_REGISTER, 32, output_value = open_switch))
        
        ''' 21h~24h: 0x032, SN1 data_rate = SamepleFrequency '''
        logger.info(master.execute(TiHUB_address, cst.WRITE_SINGLE_REGISTER, 33, output_value = sameple_frequency))
        logger.info(master.execute(TiHUB_address, cst.WRITE_SINGLE_REGISTER, 34, output_value = sameple_frequency))
        logger.info(master.execute(TiHUB_address, cst.WRITE_SINGLE_REGISTER, 35, output_value = sameple_frequency))
        logger.info(master.execute(TiHUB_address, cst.WRITE_SINGLE_REGISTER, 36, output_value = sameple_frequency))
        
        ''' 26h~2Ah: 0x40, Sensor Stream FIFO Buffer Length '''
        logger.info(master.execute(TiHUB_address, cst.WRITE_SINGLE_REGISTER, 38, output_value = axis_buffer_length))
        logger.info(master.execute(TiHUB_address, cst.WRITE_SINGLE_REGISTER, 39, output_value = axis_buffer_length))
        logger.info(master.execute(TiHUB_address, cst.WRITE_SINGLE_REGISTER, 40, output_value = axis_buffer_length))
        logger.info(master.execute(TiHUB_address, cst.WRITE_SINGLE_REGISTER, 41, output_value = axis_buffer_length))
        logger.info(master.execute(TiHUB_address, cst.WRITE_SINGLE_REGISTER, 42, output_value = axis_buffer_length))
        
        ''' 2Dh: 1B1(433,open), 1B0(432,close) '''
        logger.info(master.execute(TiHUB_address, cst.WRITE_SINGLE_REGISTER, 45, output_value = open_switch))

    except modbus_tk.modbus.ModbusError as exc:
        logger.error("%s- Code=%d", exc, exc.get_exception_code())
        
# In[20]
'''
   The main loop of collection data from TiHub by TCP/IP
'''
def MainLoop():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # new a TCP socket object
    s.connect((Hub_host, sensor_1_port))                   # connect to the TiHub to access sensor_1

    def Convert(x):             #                
       num = int.from_bytes(x, byteorder='big')   # convert to int 

       num = num if num >= 32768 else num - 65535 # 
       result = num/resolution                    # 12 bits 
       return result

    time_start = datetime.datetime.now()
    print('Start TiHUB-01')
    buffer = []
    ttag = []
    
    try:
        while True:
            time_now = datetime.datetime.now().strftime('%H:%M:%S:%f') # keep now time
            
            # ADDR, AXISx_1H, AXISx_1L, AXISy_1H, AXISy_1L, AXISz_1H, AXISz_1L,..., AXISx_64H, AXISx_64L, AXISy_64H, AXISy_64L, AXISz_64H, AXISz_64L 
            indata = s.recv(data_length) # read data bytes
            if len(indata) == 0:           # no further data
                s.close();  print('server closed connection.')
                break            
            cut = indata[1:]             # delete header 0x43(C)
              
            data = [cut[i:i+axis_number] for i in range(0, len(cut), data_bytes)]  # read two bytes in a time
            
            for x in data:
                buffer.append(Convert(x))                               # append new data
                if len(buffer) % axis_number == 0:    ttag.append(time_now)  # add timetag
    except:
         print('')
    finally:
        final_data = [buffer[i:i+axis_number] for i in range(0, len(buffer), axis_number)]  #
        [final_data[j].append(ttag[j]) for j in range(0, len(final_data))]     #
        print('TiHUB-01 Stoped')
        
        time_end = datetime.datetime.now()
        print(f'Total collection time: {time_end - time_start}')
        
        fileName = time_end.strftime(".\savetest/TiHUB-01_%Y%m%d_%H%M") + '.csv'
        columns = ['Vib_X','Vib_Y','Vib_Z' , 'Timetag']
        file = pd.DataFrame(columns = columns, data = final_data)
        file.to_csv(fileName, encoding = 'gbk', index = False)
        print('Write CSV finish')

# In[100]
if __name__ == '__main__': 
    SetRegister()
    MainLoop()