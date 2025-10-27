# -*- coding: utf-8 -*-
"""
Created on Wed Dec 22 15:10:51 2021

@author: user
"""
# In[1] TiHub_parameters

import modbus_tk
import sys
import logging
import modbus_tk.defines as cst
import modbus_tk.modbus_tcp as modbus_tcp


logger = modbus_tk.utils.create_logger("console")

if __name__ == "__main__":
    
    HOST = "169.254.7.10"
    PORT = 502
    TiHUB_address = 0x41
    SamepleFrequency = 800
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
        
# In[2] TiHub_Mqtt_collection

import time
import datetime
import csv
import pandas as pd
import socket
import paho.mqtt.client as mqtt
import paho.mqtt.subscribe as subscribe
import threading
import json

''' MQTT Connect '''

MQTT_ServerIP = '127.0.0.1'
MQTT_ServerPort = 1883 
MQTT_TopicName1 = "Coretronic_X"
MQTT_TopicName2 = "Coretronic_Y"
MQTT_TopicName3 = "Coretronic_Z"
topic = "command"


b = 0
buffer = []


def get_master_command():
    
    global b
    
    while True:
        msg = subscribe.simple("command", hostname = MQTT_ServerIP)
        # b = str(msg.payload).split(',')
        # b = int(str(msg.payload).split(',')[2].split(':')[1].split('"')[1])
        b = int(msg.payload)
        # print(b)   
            
def find(num):
    
    while num >= 32768:
        num = num - 65535
    return num

def push_data_to_master():
    
    global b
    
    counter = 0
    
    ''' TCP IP,Port (1505---Sensor_1) '''
    HOST = '169.254.7.10'
    PORT = 1505
    
    time_start = datetime.datetime.now()   

    while True:
        
        if b == 1:
            
            timetag = datetime.datetime.now()
            
            ''' TCP宣告 '''
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((HOST, PORT))
            
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

            # print(final_data)
            
            # for i in range(len(final_data)):
            
            #     # print(final_data[i][0]) 
            #     x = final_data[i][0]
            #     y = final_data[i][1]
            #     z = final_data[i][2]
            #     # print("x =",x)
            # mqttc = mqtt.Client()
            # mqttc.connect(MQTT_ServerIP, MQTT_ServerPort)
            # mqttc.publish(MQTT_TopicName1, x)
            # mqttc.publish(MQTT_TopicName2, y)
            # mqttc.publish(MQTT_TopicName3, z)
            
            # i2 = i2 + 1
            
        if b == 2:
            
            step = 4
            final_data = [buffer[i:i+step] for i in range(0, len(buffer), step)]
            
            time_end = datetime.datetime.now()
                        
            fileName = time_end.strftime(".\savefile/TiHUB-01_%Y%m%d_%H%M") + '.csv'

            columns = ['Coretronic_X', 'Coretronic_Y', 'Coretronic_Z', 'Timetag']
            file = pd.DataFrame(columns = columns, data = final_data)
            
            file.to_csv(fileName, encoding = 'gbk')
            
            break
    
# In[3] TiHub_thread

thread_1 = threading.Thread( target = get_master_command , args = () )

thread_2 = threading.Thread( target = push_data_to_master , args = () )

thread_1.start()
thread_2.start()






