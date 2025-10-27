# -*- coding: utf-8 -*-
"""
Created on Fri Mar 24 17:29:45 2023

@author: Guan
"""

import threading
import socket
import datetime
import re
import xlwt
import json
import time
import ast
import paho.mqtt.client as mqtt
import paho.mqtt.subscribe as subscribe
import paho.mqtt.publish as publish
import paho.mqtt.client as mqttcc
from streamlit.runtime.scriptrunner.script_run_context import add_script_run_ctx
# In[]
# =============================================================================
#    The parameters and registers of TiHub 
# =============================================================================

Hub_host = '169.254.7.10'
register_port = 502        # TCP/IP port of TiHUB for setting registers 
sensor_1_port = 1505       # TCP/IP Port of TiHUB for Sensor_1
TiHUB_address = 0x41       # HUB address  中強光: 0x51, 東台: 0x41
sameple_frequency = 1600   # sampling rate from Hub
open_switch = 433          # command to open switch
close_switch = 432         # command to close switch
axis_buffer_length = 64    # the maximum buffer length in bytes
axis_number = 3            # data axis(x,y,z)
autolog = 1                # auto logging
start_mode = 1             # start 
Strm_autolog = 1           

data_bytes = 2     
data_length = 385          # header + axes* bytes * axis_buffer_length = 1 + 3*2*64
frame_payload = 192        # default payload size by frame in byte
# save_interval = (frame_payload * 8)/sameple_frequency
save_interval = (frame_payload * 8)/sameple_frequency
resolution = 2048          # 12 bits

save_file = True           # flag for saving file
TsEnd = False              # flag to stop data collection 
# ts = False
state_flag = False         # initialization state
stop_flag = True
state_1  = False
send_state = False
statey = False

buffer = [[],[]]           # two buffers used for saving data
time_tag = [[],[]]         # two timetags when collecting data by buffer
save_start = [[],[]]       # two start timetag 
save_end = [[],[]]
time_offset = [0,0]
file_data_name = []

sheet = ''
folder_path = './SaveFile'   # initialization path

mqtt_host = "127.0.0.1"#"broker.emqx.io"
mqtt_portNo = 	1883
final_data_mqtt = []
mqstate = True
vw_state = False
mqstep = 160
iti = 0

# In[]
class DataThread(threading.Thread):
    global save_file, TsEnd, time_offset ,stop_flag,aa
    
    def __init__(self):
        
        threading.Thread.__init__(self)        
        
    
    def MainLoopThread(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)                           # new a TCP socket object
        s.connect((Hub_host, sensor_1_port))                                            # connect to the TiHub to access sensor_1
        
        
        def Convert(x):                        
            num = int.from_bytes(x, byteorder='big')                                    # convert to int 
            
            if num>= 32768:
                num = num - 65535
            result = num/resolution                                                     # 12 bits 
            return result
    
        while True:
            # ADDR, AXISx_1H, AXISx_1L, AXISy_1H, AXISy_1L, AXISz_1H, AXISz_1L,..., AXISx_64H, AXISx_64L, AXISy_64H, AXISy_64L, AXISz_64H, AXISz_64L             
            
            indata = s.recv(data_length) # read data bytes
            
            if len(indata) == 0:                                                        # no further data
                s.close();  print('server closed connection.')
                # self.DisplayImg('./Logo/error.jpg')
                break            
            cut = indata[1:]                                                            # delete header 0x43(C) 
    
            data = [cut[i:i+data_bytes] for i in range(0, len(cut), data_bytes)]        # read two bytes in a time
    
            for x in data:
                index = 0 if save_file == True else 1                                   # change the buffer for saving data
                buffer[index].append(Convert(x))                                        # append new data
                time_tag[index].append(time_offset[index]/sameple_frequency)            # add timetag
                time_offset[index] += 1                                                 # increase the time_offset  
                
            if TsEnd == True :                                                           # to stop 
                break            
# In[]: save the data collected in the buffer            

            
    def SaveDataThread(self):
        global buffer, time_tag, save_file, TsEnd, time_offset, save_start, path, state_flag,final_data,send_data,send_state, iti
        
        for i in range(2):
            save_start[i] = datetime.datetime.now()
        while True: 
            self.event.wait()                                                           # wait for the timer trigger for saving data
            
           
            state_flag = True
            if save_file == True:              
                save_file = False; index = 0                                            # inverse the save file flag 
            else: 
                save_file = True; index = 1
            save_end[index] = datetime.datetime.now()
            
            final_data = [buffer[index][i:i+axis_number] for i in range(0, len(buffer[index]), axis_number)]
            

            # [final_data[j].insert(0, (str(datetime.datetime.now())[:-7])+str(time_tag[index][j])[1:]) for j in range(0, len(final_data))]
            [final_data[j].insert(0,  iti + time_tag[index][j]) for j in range(0, len(final_data))]     
            self.event1.set()

            
            fileName = xlwt.Workbook(encoding = 'utf-8')
            
            start_min = re.sub(r'[^\w\s]','',str(save_start[index])[14:16])
            start_sec = re.sub(r'[^\w\s]','',str(save_start[index])[17:19])
            start_msec = re.sub(r'[^\w\s]','',str(save_start[index])[20:])
            
            end_min = re.sub(r'[^\w\s]','',str(save_end[index])[14:16])
            end_sec = re.sub(r'[^\w\s]','',str(save_end[index])[17:19])
            end_msec = re.sub(r'[^\w\s]','',str(save_end[index])[20:])
            
            # record start and end times
            sheet_name = start_min + '-' + start_sec + '-' + start_msec + '~' + end_min + '-' + end_sec + '-' + end_msec
            
            sheet = fileName.add_sheet(sheet_name)
    
            columns = ['Timetag','Vib_X','Vib_Y','Vib_Z']
            
            for col, column in enumerate(columns):
                # print(col,column)
                sheet.write(0, col, column)
            
            for row, data in enumerate(final_data):
                for col, column_data in enumerate(data):
                    sheet.write(row + 1, col, column_data)
                    
            fileName.save(save_start[index].strftime(folder_path + './TiHUB-01_%Y%m%d_%H%M%S.xls')) 
            
            buffer[index] = []
            time_tag[index] = []
            time_offset[index] = 0
            iti += 1
            if index == 0:
                save_start[1] = datetime.datetime.now()
            else:
                save_start[0] = datetime.datetime.now()
            
            if TsEnd == True:
                # msg = {'data':0}
                # jmsg = json.dumps(msg, ensure_ascii=False)
                # publish.single("mislab/id/data1",jmsg, hostname = mqtt_host)   
                break
             
            self.event.clear()

    def TimerThread(self, interval = save_interval,):  #
        global timer_1, timer_2, TsEnd,stop_flag,iti
        
        
        timer_2 = time.process_time()
        while True: 
            
            timer_1 = time.process_time()                
            if abs(timer_2 - timer_1) >= interval :                                       # per one secod 
                self.event.set()                                                          # trigger save data event
                timer_2 = time.process_time()
            if TsEnd == True  :
                self.event.set()
                break

    def MqttSend(self):
        global final_data,TsEnd
        while True:
            self.event1.wait()       
            msg = {'data':final_data}
            jmsg = json.dumps(msg, ensure_ascii=False)
            publish.single("mislab/id/data1",jmsg, hostname = mqtt_host) 
            self.event1.clear()
            if TsEnd == True  :
                break

    def StopThread(self):
        global TsEnd ,dic_state
        def on_message_print(client, userdata, message):
            global TsEnd
            byte_str = message.payload
            dict_str = byte_str.decode("UTF-8")
            mydata = ast.literal_eval(dict_str)
            dic_state = mydata['State']
            if dic_state == 1:
                TsEnd = True
                # os._exit()
        while True:
            subscribe.callback(on_message_print, "mislab/id/xy", hostname=mqtt_host)
            if TsEnd == True:
                break                
    # In[]: run            

    def run(self):        
        
        # Step 2: inital the four threads
        
        self.event = threading.Event()                                                    # new the timer event by a time interval
        self.event1 = threading.Event()
        
        self.collect_data_thread = threading.Thread(target = self.MainLoopThread)         # new mainloop object for data collection
        add_script_run_ctx(self.collect_data_thread)
        self.collect_data_thread.start()                                                  # start data collection thread 
        
        self.save_data_thread = threading.Thread(target = self.SaveDataThread)            # new save data thread object
        add_script_run_ctx(self.save_data_thread)
        self.save_data_thread.start()                                                     # start data saving_data thread
                
        self.timer_thread = threading.Thread(target = self.TimerThread)                   # new a timer to trigger the saving event 
        add_script_run_ctx(self.timer_thread)
        self.timer_thread.start()
        
        self.stop_thread = threading.Thread(target = self.StopThread)
        add_script_run_ctx(self.stop_thread)
        self.stop_thread.start()
        
        self.send_thread = threading.Thread(target = self.MqttSend)
        add_script_run_ctx(self.send_thread)
        self.send_thread.start()

            
        # Step 3: join all threads into a poll   
        self.collect_data_thread.join()
        self.save_data_thread.join()
        # self.send_data_thread.join()
        self.timer_thread.join()
        self.stop_thread.join()
        
# In[]
if __name__ == "__main__":
    # client = mqttcc.Client('Python')
    DataThread().start()
