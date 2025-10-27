# -*- coding: utf-8 -*-
"""
Created on Tue Jul 26 14:07:45 2022

@author: user
"""

import modbus_tk
import modbus_tk.defines as cst
import modbus_tk.modbus_tcp as modbus_tcp
import datetime
import socket
import threading
import time
import xlwt

# In[1]
'''
   The parameters and registers of TiHub 
'''
Hub_host = '169.254.7.10'
register_port = 502        # TCP/IP port of TiHUB for setting registers 
sensor_1_port = 1505       # TCP/IP Port of TiHUB for Sensor_1
sensor_2_port = 1506       # TCP/IP Port of TiHUB for Sensor_2
TiHUB_address = 0x41       # HUB address  中強光: 0x51, 東台: 0x41
sameple_frequency = 1600   # sampling rate from Hub
open_switch = 435          # command to open switch, S4 S3 S2 S1 -> b3 b2 b1 b0, e.g. S1-> 433, S2 and S1 -> 435
close_switch = 432         # command to close switch
axis_buffer_length = 64    # the maximum buffer length in bytes
axis_number = 3
autolog = 1                # auto logging
start_mode = 1             # start 
Strm_autolog = 1           

data_bytes = 2     
data_length = 385          # header + axes* bytes * axis_buffer_length = 1 + 3*2*64
resolution = 2048          # 12 bits

save_file = True 
TsEnd = False

buffer_1 = []
buffer_2 = []
time_tag_1 = []
time_tag_2 = []
timetag = []
time_offset_1 = 0
time_offset_2 = 0

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
    global save_file, time_start, TsEnd, time_offset_1, time_offset_2 

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # new a TCP socket object
    s.connect((Hub_host, sensor_1_port))                   # connect to the TiHub to access sensor_1
    
    def Convert(x):                        
        num = int.from_bytes(x, byteorder='big')   # convert to int 
        
        if num>= 32768:
            num = num - 65535
        result = num/resolution                    # 12 bits 
        return result

    while True:
        
        #time_now = datetime.datetime.now().strftime('%H:%M:%S:%f') # keep now time
        # ADDR, AXISx_1H, AXISx_1L, AXISy_1H, AXISy_1L, AXISz_1H, AXISz_1L,..., AXISx_64H, AXISx_64L, AXISy_64H, AXISy_64L, AXISz_64H, AXISz_64L             
        indata = s.recv(data_length) # read data bytes
        
        if len(indata) == 0:           # no further data
            s.close();  print('server closed connection.')
            break            
        cut = indata[1:]             # delete header 0x43(C) 

        data = [cut[i:i+data_bytes] for i in range(0, len(cut), data_bytes)]  # read two bytes in a time

        for x in data:

            if save_file == True:
                buffer_1.append(Convert(x))             # append new data
                time_tag_1.append(time_offset_1/sameple_frequency)             # add timetag
                time_offset_1 += 1
                
            else:
                buffer_2.append(Convert(x))             # append new data
                time_tag_2.append(time_offset_2/sameple_frequency)             # add timetag
                time_offset_2 += 1
        
        if TsEnd == True:
            break
            
def SaveData():
    global buffer_1, buffer_2, time_start, time_tag_1, time_tag_2, save_file, TsEnd, time_offset_1, time_offset_2
    
    while True: 
        event.wait()

        if save_file == True:    

            save_file = False

            final_data_1 = [buffer_1[i:i+axis_number] for i in range(0, len(buffer_1), axis_number)]      
            [final_data_1[j].insert(0, time_tag_1[j]) for j in range(0, len(final_data_1))]
            
            time_end_1 = datetime.datetime.now()
            
            fileName_1 = xlwt.Workbook(encoding = 'utf-8')
            sheet = fileName_1.add_sheet('vib')
            
            columns = ['Timetag','Vib_X','Vib_Y','Vib_Z']
            for col, column in enumerate(columns):
                sheet.write(0, col, column)
            
            for row, data in enumerate(final_data_1):
                for col, column_data in enumerate(data):
                    sheet.write(row + 1, col, column_data)
                    
            fileName_1.save(time_end_1.strftime(".\savetest/TiHUB-01_%Y%m%d_%H%M%S.xls"))
            
            buffer_1 = []
            time_tag_1 = []
            time_offset_1 = 0

        else:
            
            save_file = True
            
            final_data_2 = [buffer_2[i:i+axis_number] for i in range(0, len(buffer_2), axis_number)]   
            [final_data_2[j].insert(0, time_tag_2[j]) for j in range(0, len(final_data_2))] 
            
            time_end_2 = datetime.datetime.now()
            
            fileName_2 = xlwt.Workbook(encoding = 'utf-8')
            sheet = fileName_2.add_sheet('vib')
            
            columns = ['Timetag','Vib_X','Vib_Y','Vib_Z']
            for col, column in enumerate(columns):
                sheet.write(0, col, column)
            
            for row, data in enumerate(final_data_2):
                for col, column_data in enumerate(data):
                    sheet.write(row + 1, col, column_data)
                    
            fileName_2.save(time_end_2.strftime(".\savetest/TiHUB-01_%Y%m%d_%H%M%S.xls"))
            
            buffer_2 = []
            time_tag_2 = []
            time_offset_2 = 0
                
        event.clear()
        
        if TsEnd == True:
            break

def TimerThread():  #
    global time_process_2, time_process_1, TsEnd

    time_process_2 = time.process_time()
    while True:

        time_process_1 = time.process_time()           
        if int(abs(time_process_2 - time_process_1)) >= 1 : # per one secod 
            time_process_2 = time.process_time()
            event.set()   # trigger save data event
            
        if TsEnd == True:
            break
        
def StopThread():
    global TsEnd
    stop_command = input('輸入q停止:')
    
    while True:
        if stop_command == 'q':
            TsEnd = True
            break
        
# In[100]
if __name__ == '__main__': 
    SetRegister()
    
    time_start = datetime.datetime.now()    # get current time
    event = threading.Event()               # new thread event
    
    collect_data = threading.Thread(target= MainLoop)  # new mainloop object for data collection
    collect_data.start()                    # start data collection thread 
    
    save_data = threading.Thread(target = SaveData)  # new save data object
    save_data.start()                        # start data saving thread    
    
    timer_thread = threading.Thread(target = TimerThread)   # new  
    timer_thread.start()
    
    stop_thread = threading.Thread(target = StopThread)
    stop_thread.start()
    
    # event.join()
    collect_data.join()
    save_data.join()
    timer_thread.join()
    stop_thread.join()
    print('stop')
