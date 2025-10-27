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
from PyQt5.QtGui import QPixmap
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtGui import QTextCursor 
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
state_flag = False

buffer = [[],[]]           # two buffers used for saving data
time_tag = [[],[]]         # two timetags when collecting data by buffer
save_start = [[],[]]       # two start timetag 
save_end = [[],[]]
time_offset = [0,0]

# In[]
class UIThread(QThread):
    
    def __init__(self):
        super(UIThread, self).__init__()

    def __del__(self):
        self.wait()
        self.img_path = './Logo/green-led.png'
        self.display_img()
    
# In[]: The main loop of collection data from TiHub by TCP/IP
    def MainLoopThread(self):
        global save_file, time_start, TsEnd, time_offset, state_flag
    
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # new a TCP socket object
        s.connect((Hub_host, sensor_1_port))                   # connect to the TiHub to access sensor_1
        
        def Convert(x):                        
            num = int.from_bytes(x, byteorder='big')           # convert to int 
            
            if num>= 32768:
                num = num - 65535
            result = num/resolution                            # 12 bits 
            return result
    
        while True: 
            state_flag = True
            # ADDR, AXISx_1H, AXISx_1L, AXISy_1H, AXISy_1L, AXISz_1H, AXISz_1L,..., AXISx_64H, AXISx_64L, AXISy_64H, AXISy_64L, AXISz_64H, AXISz_64L             
            indata = s.recv(data_length) # read data bytes
            
            if len(indata) == 0:         # no further data
                s.close();  print('server closed connection.')
                self.DisplayImg('./Logo/error.jpg')
                break            
            cut = indata[1:]             # delete header 0x43(C) 
    
            data = [cut[i:i+data_bytes] for i in range(0, len(cut), data_bytes)]  # read two bytes in a time
    
            for x in data:
                index = 0 if save_file == True else 1                             # change the buffer for saving data
                buffer[index].append(Convert(x))                                  # append new data
                time_tag[index].append(time_offset[index]/sameple_frequency)      # add timetag
                time_offset[index] += 1                                           # increase the time_offset  
    
            if TsEnd == True:                                                     # to stop 
                break
            
# In[]: save the data collected in the buffer            
    def SaveDataThread(self):
        global buffer, time_start, time_tag, save_file, TsEnd, time_offset, save_start, path, fileName
        
        for i in range(2):
            save_start[i] = datetime.datetime.now()
            
        while True: 
            self.event.wait()                       # wait for the timer trigger for saving data
    
            if save_file == True:              
                save_file = False; index = 0        # inverse the save file flag 
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
                    
            fileName.save(save_start[index].strftime(folder_path + './TiHUB-01_%Y%m%d_%H%M%S.xls'))     
            # fileName.save(save_start[index].strftime(".\Output/TiHUB-01_%Y%m%d_%H%M%S.xls"))

            buffer[index] = []
            time_tag[index] = []
            time_offset[index] = 0
            if index == 0:
                save_start[1] = datetime.datetime.now()
            else:
                save_start[0] = datetime.datetime.now()
            self.event.clear()
            
            if TsEnd == True:
                break
            
# In[]: Set the timer thread with preset interval      
    def TimerThread(self, interval = save_interval):  #
        global timer_1, timer_2, TsEnd
    
        timer_2 = time.process_time()
        while True:
    
            timer_1 = time.process_time()                
            if abs(timer_2 - timer_1) >= interval :                                  # per one secod 
                self.event.set()                                                     # trigger save data event
                timer_2 = time.process_time()
                
            if TsEnd == True:
                break
            
# In[]: run            
    def run(self):        
        # Step 2: inital the four threads
        self.time_start = datetime.datetime.now()                                    # get current time
        self.event = threading.Event()                                               # new the timer event by a time interval
        
        self.collect_data_thread = threading.Thread(target = self.MainLoopThread)    # new mainloop object for data collection
        self.collect_data_thread.start()                                             # start data collection thread 
        
        self.save_data_thread = threading.Thread(target = self.SaveDataThread)       # new save data thread object
        self.save_data_thread.start()                                                # start data saving_data thread    
        
        self.timer_thread = threading.Thread(target = self.TimerThread)              # new a timer to trigger the saving event 
        self.timer_thread.start()                                                    # start the timer thread   

        # Step 3: join all threads into a poll   
        self.collect_data_thread.join()
        self.save_data_thread.join()
        self.timer_thread.join()                   
                                   
# In[]
class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):    
    
    def __init__(self, parent = None):
        # initialization
        super(MainWindow, self).__init__(parent)
        self.setupUi(self)

        # window name
        self.setWindowTitle('TiHub UI')
        # window icon
        self.setWindowIcon(QIcon('./Logo/NKUST.png'))     
      
        # function
        self.SetRegister.clicked.connect(self.SetRegisterCollect)
        self.SavePath.clicked.connect(self.OpenFolder) 
        self.Start.clicked.connect(self.StartCollect) 
        self.Stop.clicked.connect(self.StopCollect)
        # add sample frequency
        self.Rate.addItems(['50', '100', '200', '400', '800', '1600'])
        
        
        self.SetupIcon()
        
# In[]: set state image        
    def SetupIcon(self):
        global state_flag
        if state_flag == False:
            self.DisplayImg('./Logo/red-led.png')  
        else:
            self.DisplayImg('./Logo/green-led.png')
        
# In[]: display state image        
    def DisplayImg(self, img):       
        self.myqimage = QImage(img)
        self.label.setPixmap(QPixmap.fromImage(self.myqimage))
        self.label.setScaledContents(True)
        
# In[]: set the registers of Hub to collect the data in the specified frequency and operation mode
    def SetRegisterCollect(self):
        logger = self.modbus_tk.utils.create_logger("console")
        try:     
            ''' modbus TCP IP,Port '''
            master = modbus_tcp.TcpMaster(host = Hub_host, port = register_port)
            master.set_timeout(1)
            
            ''' 0x41: TiHUB-01 address '''
            logger.info(self.master.execute(TiHUB_address, cst.READ_HOLDING_REGISTERS, 0, 16))
            
            ''' 20h: 1B1(433,open), 1B0(432,close) '''
            logger.info(self.master.execute(TiHUB_address, cst.WRITE_SINGLE_REGISTER, 32, output_value = close_switch))
    
            ''' 52h~55h: 0x032, start-up, SamepleFrequency '''
            logger.info(self.master.execute(TiHUB_address, cst.WRITE_SINGLE_REGISTER, 82, output_value = sameple_frequency))
            logger.info(self.master.execute(TiHUB_address, cst.WRITE_SINGLE_REGISTER, 83, output_value = sameple_frequency))
            logger.info(self.master.execute(TiHUB_address, cst.WRITE_SINGLE_REGISTER, 84, output_value = sameple_frequency))
            logger.info(self.master.execute(TiHUB_address, cst.WRITE_SINGLE_REGISTER, 85, output_value = sameple_frequency))
        
            ''' 51h: 0x01 = AUTOLOG, 0x00 = no AUTOLOG '''
            logger.info(self.master.execute(TiHUB_address, cst.WRITE_SINGLE_REGISTER, 81, output_value = autolog))
            
            ''' 50h: 0x01 STARTMOD '''
            logger.info(self.master.execute(TiHUB_address, cst.WRITE_SINGLE_REGISTER, 80, output_value = start_mode))
       
            ''' 21h~24h: 0x032, SN1 data_rate = SamepleFrequency '''
            logger.info(self.master.execute(TiHUB_address, cst.WRITE_SINGLE_REGISTER, 33, output_value = sameple_frequency))
            logger.info(self.master.execute(TiHUB_address, cst.WRITE_SINGLE_REGISTER, 34, output_value = sameple_frequency))
            logger.info(self.master.execute(TiHUB_address, cst.WRITE_SINGLE_REGISTER, 35, output_value = sameple_frequency))
            logger.info(self.master.execute(TiHUB_address, cst.WRITE_SINGLE_REGISTER, 36, output_value = sameple_frequency))
            
            ''' 26h~2Ah: 0x40, Sensor Stream FIFO Buffer Length '''
            logger.info(self.master.execute(TiHUB_address, cst.WRITE_SINGLE_REGISTER, 38, output_value = axis_buffer_length))
            logger.info(self.master.execute(TiHUB_address, cst.WRITE_SINGLE_REGISTER, 39, output_value = axis_buffer_length))
            logger.info(self.master.execute(TiHUB_address, cst.WRITE_SINGLE_REGISTER, 40, output_value = axis_buffer_length))
            logger.info(self.master.execute(TiHUB_address, cst.WRITE_SINGLE_REGISTER, 41, output_value = axis_buffer_length))
            logger.info(self.master.execute(TiHUB_address, cst.WRITE_SINGLE_REGISTER, 42, output_value = axis_buffer_length))
            
            ''' 20h: 1B1(433,open), 1B0(432,close) '''
            logger.info(self.master.execute(TiHUB_address, cst.WRITE_SINGLE_REGISTER, 32, output_value = open_switch))
            self.State.append('set successful')
            
        except modbus_tk.modbus.ModbusError as exc:
            logger.error("%s- Code=%d", exc, exc.get_exception_code())
            self.State.append(exc.get_exception_code())   

# In[]: select folder    
    def OpenFolder(self):
        global folder_path
        folder_path = QFileDialog.getExistingDirectory(self, "Open folder", "./")
        self.SaveFIlePath.setText(folder_path)
        
# In[]
    def DisplayFile(self):
        global folder_path
        while state_flag == False:
            # filename = os.listdir('C:/Users/Win10/Desktop/TiHub_ui/Output')
            filename = os.listdir(folder_path)
            for i in filename:
                self.State.append(i)
                self.State.moveCursor(QTextCursor.End)

    
# In[]: stop the data collection by click stop              
    def StopThread(self):
        global TsEnd, state_flag
        while True:
            TsEnd = True
            state_flag = True
            break
            
# In[]: start
    def StartCollect(self):
        self.start_thread = UIThread()
        self.start_thread.start()
        
        self.display_file = threading.Thread(target = self.DisplayFile)     
        self.display_file.start()             
        
# In[]: stop   
    def StopCollect(self):
        stop_thread = threading.Thread(target = self.StopThread)                # new a keyboard stop thread 
        stop_thread.start()                                                     # start the stop thread
        
# In[]: close window reminder            
    def closeEvent(self, close_event):
        reply = QtWidgets.QMessageBox.question(self,
                                               'Warning',
                                               "Do you want to close the window？",
                                               QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                                               QtWidgets.QMessageBox.No)
        if reply == QtWidgets.QMessageBox.Yes:
            close_event.accept()
        else:
            close_event.ignore()  
        
# In[100]        
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    win = MainWindow()
    win.show()
    
    