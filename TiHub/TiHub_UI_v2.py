# -*- coding: utf-8 -*-
"""
Created on Thu Aug  4 09:48:34 2022

@author: Win10
"""

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QFileDialog
from PyQt5 import QtWidgets
from UI_2 import Ui_MainWindow
from PyQt5.QtCore import QThread
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtGui import QTextCursor 
from Plot import PlotMainWindow
from matplotlib import pyplot as plt
import modbus_tk
import modbus_tk.defines as cst
import modbus_tk.modbus_tcp as modbus_tcp
import sys
import datetime
import socket
import threading
import time
import xlwt
import re
import os
import pandas as pd
import numpy as np
from collections import deque


# In[]
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
axis_number = 3            # data axis(x,y,z)
autolog = 1                # auto logging
start_mode = 1             # start 
Strm_autolog = 1           

data_bytes = 2     
data_length = 385          # header + axes* bytes * axis_buffer_length = 1 + 3*2*64
frame_payload = 192        # default payload size by frame in byte
# save_interval = (frame_payload * 8)/sameple_frequency
save_interval = (frame_payload * (int(sameple_frequency/frame_payload)+1)/sameple_frequency)
resolution = 2048          # 12 bits

save_file = True           # flag for saving file
TsEnd = False              # flag to stop data collection 
state_flag = False         # initialization state
state_flag1 = False

buffer = [[],[]]           # two buffers used for saving data
time_tag = [[],[]]         # two timetags when collecting data by buffer
save_start = [[],[]]       # two start timetag 
save_end = [[],[]]
time_offset = [0,0]
file_data_name = []

queue1 = ''
folder_path = './SaveFile'   # initialization path

# In[]
class DataThread(QThread):
    
    def __init__(self):
        super(DataThread, self).__init__()

    def __del__(self):
        # self.wait()
        self.event.wait()  
        self.img_path = './Logo/green-led.png'
        # self.display_img()
        
    
# In[]: The main loop of collection data from TiHub by TCP/IP
    def MainLoopThread(self):
        global save_file, TsEnd, time_offset
    
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)                           # new a TCP socket object
        s.connect((Hub_host, sensor_1_port))                                            # connect to the TiHub to access sensor_1
        
        def Convert(x):                        
            num = int.from_bytes(x, byteorder='big')                                    # convert to int 
            
            if num>= 32768:
                num = num - 65535
            result = num/resolution                                                     # 12 bits 
            return result
        
        try:
            while True: 
                # state_flag = True
                # ADDR, AXISx_1H, AXISx_1L, AXISy_1H, AXISy_1L, AXISz_1H, AXISz_1L,..., AXISx_64H, AXISx_64L, AXISy_64H, AXISy_64L, AXISz_64H, AXISz_64L             
                indata = s.recv(data_length) # read data bytes
                
                if len(indata) == 0:                                                        # no further data
                    s.close();  print('server closed connection.')
                    TsEnd = True
                    # self.DisplayImg('./Logo/error.jpg')
                    break            
                cut = indata[1:]                                                            # delete header 0x43(C) 
        
                data = [cut[i:i+data_bytes] for i in range(0, len(cut), data_bytes)]        # read two bytes in a time
        
                for x in data:
                    index = 0 if save_file == True else 1                                   # change the buffer for saving data
                    buffer[index].append(Convert(x))                                        # append new data
                    time_tag[index].append(time_offset[index]/sameple_frequency)            # add timetag
                    time_offset[index] += 1                                                 # increase the time_offset  
        
                if TsEnd == True:                                                           # to stop 
                    break
        except:
            TsEnd = True
            s.close();  print('server closed connection.')
            
# In[]: save the data collected in the buffer            
    def SaveDataThread(self):
        global buffer, time_tag, save_file, TsEnd, time_offset, save_start, path, state_flag, sheet_name,state_flag1
        
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
            [final_data[j].insert(0, time_tag[index][j]) for j in range(0, len(final_data))]
            
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
            state_flag1 = True
                
            buffer[index] = []
            time_tag[index] = []
            time_offset[index] = 0
            if index == 0:
                save_start[1] = datetime.datetime.now()
            else:
                save_start[0] = datetime.datetime.now()
            
            if TsEnd == True:
                state_flag = False
                print('end')                
                # self.event.clear()
                break
            self.event.clear()
            

            
# In[]: Set the timer thread with preset interval      
    def TimerThread(self, interval = save_interval):  #
        global timer_1, timer_2, TsEnd
    
        timer_2 = time.process_time()
        while True:    
            timer_1 = time.process_time()                
            if abs(timer_2 - timer_1) >= interval :                                       # per one secod 
                self.event.set()                                                          # trigger save data event
                timer_2 = time.process_time()
                
            if TsEnd == True:
                self.event.set()
                break
            
# In[]: run            
    def run(self):        
        # Step 2: inital the four threads
        self.event = threading.Event()                                                    # new the timer event by a time interval
        
        self.collect_data_thread = threading.Thread(target = self.MainLoopThread)         # new mainloop object for data collection
        self.collect_data_thread.start()                                                  # start data collection thread 
        
        self.save_data_thread = threading.Thread(target = self.SaveDataThread)            # new save data thread object
        self.save_data_thread.start()                                                     # start data saving_data thread    
        
        self.timer_thread = threading.Thread(target = self.TimerThread)                   # new a timer to trigger the saving event 
        self.timer_thread.start()                                                         # start the timer thread   
        
        # Step 3: join all threads into a poll   
        self.collect_data_thread.join()
        self.save_data_thread.join()
        self.timer_thread.join()
        
        # if TsEnd == True:
        #     print(self.save_data_thread.is_alive())
        #     print(self.collect_data_thread.is_alive())
        #     print(self.timer_thread.is_alive())
        #     print(sheet_name)

                         
                                   
# In[]
class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):    
    
    def __init__(self, parent = None):
        # initialization
        super(MainWindow, self).__init__(parent)
        self.setupUi(self)

        # window name
        self.setWindowTitle('TiHub_v.1')
        # window icon
        self.setWindowIcon(QIcon('./Logo/NKUST.png'))     
      
        # button clicked
        self.SetRegister.clicked.connect(self.SetRegisterCollect)
        self.SavePath.clicked.connect(self.OpenFolder) 
        self.Start.clicked.connect(self.StartCollection) 
        self.Stop.clicked.connect(self.StopCollection)
        self.Plot.clicked.connect(self.PlotGraphics)
        self.Load.clicked.connect(self.LoadFileType)
        self.LoadPlot.clicked.connect(self.PlotFileGraphics)
        
        # add sample frequency
        self.Rate.addItems(['1600'])
        # self.Rate.addItems(['1600', '50', '100', '200', '400', '800', '3200', '6400', '12800'])
                
        # initialization icon
        self.DisplayImg('./Logo/red-led.png') 
        self.State.setText('')
        self.SaveFIlePath.setText(folder_path)
        
        
        # disabled
        # self.SetRegister.setEnabled(False)
        self.Plot.setEnabled(False)
        # self.State.setEnabled(False)
        
        
# In[]: set state image        
    def SetupIcon(self):
        global state_flag
        previous_state = state_flag
        while True:
            if previous_state != state_flag:
                if state_flag == True:
                    self.DisplayImg('./Logo/green-led.png')                                  # start icon
                else:
                    self.DisplayImg('./Logo/red-led.png')                                    # stop icon
                previous_state = state_flag
            time.sleep(0.5)
        
# In[]: display state image        
    def DisplayImg(self, img):       
        self.myqimage = QImage(img)
        self.label.setPixmap(QPixmap.fromImage(self.myqimage))
        self.label.setScaledContents(True)
        
# In[]: set the registers of Hub to collect the data in the specified frequency and operation mode
    def SetRegisterCollect(self):
        ''' modbus TCP IP,Port '''
        master = modbus_tcp.TcpMaster(host = Hub_host, port = register_port)
        master.set_timeout(1)
            
        try:     
            ''' modbus TCP IP,Port '''
            master = modbus_tcp.TcpMaster(host = Hub_host, port = register_port)
            master.set_timeout(1)
            
            ''' 20h: 1B1(433,open), 1B0(432,close) '''
            master.execute(TiHUB_address, cst.WRITE_SINGLE_REGISTER, 32, output_value = close_switch)
            
            ''' 0x41: TiHUB-01 address '''
            master.execute(TiHUB_address, cst.READ_HOLDING_REGISTERS, 0, 16)
              
            ''' 21h~24h: 0x032, SN1 data_rate = SamepleFrequency '''
            self.sameple_frequency = int(self.Rate.currentText())            
            self.interval = (frame_payload * int(self.sameple_frequency/frame_payload))/self.sameple_frequency
            
            master.execute(TiHUB_address, cst.WRITE_SINGLE_REGISTER, 33, output_value = self.sameple_frequency)
            master.execute(TiHUB_address, cst.WRITE_SINGLE_REGISTER, 34, output_value = self.sameple_frequency)
            master.execute(TiHUB_address, cst.WRITE_SINGLE_REGISTER, 35, output_value = self.sameple_frequency)
            master.execute(TiHUB_address, cst.WRITE_SINGLE_REGISTER, 36, output_value = self.sameple_frequency)
            
            ''' 51h: 0x01 = AUTOLOG, 0x00 = no AUTOLOG '''
            master.execute(TiHUB_address, cst.WRITE_SINGLE_REGISTER, 81, output_value = autolog)
            
            ''' 50h: 0x01 STARTMOD '''
            master.execute(TiHUB_address, cst.WRITE_SINGLE_REGISTER, 80, output_value = start_mode)
       
            ''' 26h~2Ah: 0x40, Sensor Stream FIFO Buffer Length '''
            master.execute(TiHUB_address, cst.WRITE_SINGLE_REGISTER, 38, output_value = axis_buffer_length)
            master.execute(TiHUB_address, cst.WRITE_SINGLE_REGISTER, 39, output_value = axis_buffer_length)
            master.execute(TiHUB_address, cst.WRITE_SINGLE_REGISTER, 40, output_value = axis_buffer_length)
            master.execute(TiHUB_address, cst.WRITE_SINGLE_REGISTER, 41, output_value = axis_buffer_length)
            master.execute(TiHUB_address, cst.WRITE_SINGLE_REGISTER, 42, output_value = axis_buffer_length)
            
            ''' 20h: 1B1(433,open), 1B0(432,close) '''
            master.execute(TiHUB_address, cst.WRITE_SINGLE_REGISTER, 32, output_value = open_switch)
            QtWidgets.QMessageBox.information(self, 'Information', 'Set successful')
            
        except modbus_tk.modbus.ModbusError as exc:
            QtWidgets.QMessageBox.critical(self, 'Warning', exc)

# In[]: select folder    
    def OpenFolder(self):
        global folder_path
        folder_path = QFileDialog.getExistingDirectory(self, "Open folder", "./")
        self.SaveFIlePath.setText(folder_path)
        
# In[]: display current filename
    def DisplayFile(self):
        global folder_path, state_flag, sheet_name,TsEnd,state_flag1,queue1
        
        
        
        while True:
            if state_flag1 == True:
                queue = deque(sheet_name)
                if queue != queue1:                    
                    # print(queue)
                    self.State.append(''.join(queue))
                    self.State.moveCursor(QTextCursor.End)
                    # previous_sheet == sheet_name
                    queue1 = queue
                else:
                    self.State.append(''.join('wait'))
                    self.State.moveCursor(QTextCursor.End)
                    
                    
                        
            if TsEnd == True:
                queue1 = queue

                break
                


            time.sleep(save_interval)
   
# In[]: stop the data collection by click stop              
    def StopCollection(self):
        global TsEnd, state_flag
        TsEnd = True
        state_flag = False
        

# In[]: start
    def StartCollection(self):   
        global TsEnd, state_flag
        
        self.start_thread = DataThread()
        self.start_thread.start()
        
        self.setup_icon = threading.Thread(target = self.SetupIcon)
        self.setup_icon.start()
        
        self.display_file = threading.Thread(target = self.DisplayFile)     
        self.display_file.start() 
        TsEnd = False
        state_flag = True
        

# In[]: close window reminder            
    def closeEvent(self, close_event):
        reply = QtWidgets.QMessageBox.question(self, 'Warning', "Do you want to close the window？",
                                               QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                                               QtWidgets.QMessageBox.No)
        if reply == QtWidgets.QMessageBox.Yes:
            close_event.accept()
        else:
            close_event.ignore()  

# In[]: plot graphics
    def PlotGraphics(self):
        self.plot_graphics_thread = threading.Thread(target = PlotMainWindow())
        self.plot_graphics.start()
        
# In[]: load file
    def LoadFileType(self):
        self.load_file = QFileDialog.getOpenFileName(filter = "(*.csv);; (*.xls)")[0]    # require csv or xls   
        self.LoadFilePath.setText(self.load_file)  
        self.LoadFilePath.moveCursor(QTextCursor.End)

# In[] plot file graphics
    def PlotFileGraphics(self):       
        
        axia_x = 'Vib_X'
        axia_y = 'Vib_Y'
        axia_z = 'Vib_Z'
        
        self.lastname = self.load_file.split('.')[-1]
        if self.lastname == 'csv':
            df = pd.read_csv(self.load_file, encoding = 'utf-8')
        elif self.lastname == 'xls':
            df = pd.read_excel(self.load_file)
         
        x = df[axia_x]   
        y = df[axia_y]
        z = df[axia_z]
        
        
        fig,ax = plt.subplots(3,1)
        base_name = os.path.basename(self.load_file)
        self.Title = os.path.splitext(base_name)[0]
        fig.suptitle(self.Title)
        ax[0].set_xticks
        ax[0].set_yticks
        ax[0].plot(x)
        ax[0].set_ylabel('X', fontsize = 10)
        
        
        ax[1].set_xticks
        ax[1].set_yticks
        ax[1].plot(y)   
        ax[1].set_ylabel('Y', fontsize = 10)
        
        
        ax[2].set_xticks
        ax[2].set_yticks 
        ax[2].plot(z)
        ax[2].set_ylabel('Z', fontsize = 10)
                
        plt.show()

# In[100]        
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())
    