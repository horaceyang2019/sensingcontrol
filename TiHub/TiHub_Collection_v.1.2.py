# -*- coding: utf-8 -*-
"""
Created on Tue Jul 26 14:07:45 2022

pip install modbus

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
import re

# In[1]
'''
   The parameters and registers of TiHub 
'''
Hub_host = '169.254.7.10'
register_port = 502        # TCP/IP port of TiHUB for setting registers 
sensor_1_port = 1505       # TCP/IP Port of TiHUB for Sensor_1
TiHUB_address = 0x41       # HUB address  中強光: 0x51, 東台: 0x41
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
frame_payload = 192        # default payload size by frame in byte
save_interval = (frame_payload * 8)/sameple_frequency
resolution = 2048          # 12 bits

save_file = True           # flag for saving file
TsEnd = False              # flag to stop data collection 

buffer = [[],[]]           # two buffers used for saving data
time_tag = [[],[]]         # two timetags when collecting data by buffer
save_start = [[],[]]       # two start timetag 
save_end = [[],[]]
time_offset = [0,0]

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
def MainLoopThread():
    global save_file, time_start, TsEnd, time_offset 

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
        
        if len(indata) == 0:         # no further data
            s.close();  print('server closed connection.')
            break            
        cut = indata[1:]             # delete header 0x43(C) 

        data = [cut[i:i+data_bytes] for i in range(0, len(cut), data_bytes)]  # read two bytes in a time

        for x in data:
            index = 0 if save_file == True else 1                             # change the buffer for saving data
            buffer[index].append(Convert(x))                                  # append new data
            time_tag[index].append(time_offset[index]/sameple_frequency)      # add timetag
            time_offset[index] += 1                                           # increase the time_offset  

        if TsEnd == True:                                                     # click 'q' to stop 
            break
        
# In[30]: save the data collected in the buffer            
def SaveDataThread():
    global buffer, time_start, time_tag, save_file, TsEnd, time_offset, save_start
    
    for i in range(2):
        save_start[i] = datetime.datetime.now()
        
    while True: 
        event.wait()                      # wait for the timer trigger for saving data

        if save_file == True:              
            save_file = False; index = 0  # inverse the save file flag 
        else: 
            save_file = True; index = 1
        save_end[index] = datetime.datetime.now()
        
        final_data = [buffer[index][i:i+axis_number] for i in range(0, len(buffer[index]), axis_number)]      
        [final_data[j].insert(0, time_tag[index][j]) for j in range(0, len(final_data))]
        
        fileName = xlwt.Workbook(encoding = 'utf-8')
        
        start_min = re.sub(r'[^\w\s]','',str(save_start[index])[14:16])
        start_sec = re.sub(r'[^\w\s]','',str(save_start[index])[17:19])
        start_msec = re.sub(r'[^\w\s]','',str(save_start[index])[20:])
        
        end_min = re.sub(r'[^\w\s]','',str(save_end[index])[14:16])
        end_sec = re.sub(r'[^\w\s]','',str(save_end[index])[17:19])
        end_msec = re.sub(r'[^\w\s]','',str(save_end[index])[20:])
        
        # record start and end times
        sheet = fileName.add_sheet(start_min + '-' + start_sec + '-' + start_msec + '~' + end_min + '-' + end_sec + '-' + end_msec)

        columns = ['Timetag','Vib_X','Vib_Y','Vib_Z']
        
        for col, column in enumerate(columns):
            sheet.write(0, col, column)
        
        for row, data in enumerate(final_data):
            for col, column_data in enumerate(data):
                sheet.write(row + 1, col, column_data)
                
        fileName.save(save_start[index].strftime(".\Output/TiHUB-01_%Y%m%d_%H%M%S.xls"))
        
        buffer[index] = []
        time_tag[index] = []
        time_offset[index] = 0
        if index == 0:
            save_start[1] = datetime.datetime.now()
        else:
            save_start[0] = datetime.datetime.now()
        event.clear()
        
        if TsEnd == True:
            break
        
# In[40]: Set the timer thread with preset interval      
def TimerThread(interval = save_interval):  #
    global timer_1, timer_2, TsEnd

    timer_2 = time.process_time()
    while True:

        timer_1 = time.process_time()                
        if abs(timer_2 - timer_1) >= interval :      # per one secod 
            event.set()                              # trigger save data event
            timer_2 = time.process_time()
            
        if TsEnd == True:
            break
        
# In[50]: stop the data collection by click 'q'              
def StopThread():
    global TsEnd
    stop_command = input('輸入q停止:')
    while True:
        if stop_command == 'q' or  stop_command == 'Q':
            TsEnd = True
            break
        
# In[100]
if __name__ == '__main__': 
    # Step 1: set the registers of the TiHub 
    SetRegister()
    
    # Step 2: inital the five threads
    time_start = datetime.datetime.now()                            # get current time
    event = threading.Event()                                       # new the timer event by a time interval
    
    collect_data_thread = threading.Thread(target= MainLoopThread)  # new mainloop object for data collection
    collect_data_thread.start()                                     # start data collection thread 
    
    save_data_thread = threading.Thread(target = SaveDataThread)    # new save data thread object
    save_data_thread.start()                                        # start data saving_data thread    
    
    timer_thread = threading.Thread(target = TimerThread)           # new a timer to trigger the saving event 
    timer_thread.start()                                            # start the timer thread  
    
    stop_thread = threading.Thread(target = StopThread)             # new a keyboard stop thread 
    stop_thread.start()                                             # start the stop thread
    
    # Step 3: join all threads into a poll
    collect_data_thread.join()
    save_data_thread.join()
    timer_thread.join()
    stop_thread.join()
    
    # Step 4: if click 'q'
    print('stop')