# -*- coding: utf-8 -*-
"""
Created on Tue Apr 11 10:46:01 2023

@author: USER
"""
import streamlit as st
import modbus_tk
import modbus_tk.defines as cst
import modbus_tk.modbus_tcp as modbus_tcp
import paho.mqtt.publish as publish
import json
import TiHub_streamlit_datacollection
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
frame_payload = 192        # default payload size by frame in byte
# In[]
class TiHub_control():
    def SetRegister(self,Rate):    
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
                sameple_frequency = int(Rate)
                st.write('Samplerate:' + str(sameple_frequency))
                
                
                master.execute(TiHUB_address, cst.WRITE_SINGLE_REGISTER, 33, output_value = sameple_frequency)
                master.execute(TiHUB_address, cst.WRITE_SINGLE_REGISTER, 34, output_value = sameple_frequency)
                master.execute(TiHUB_address, cst.WRITE_SINGLE_REGISTER, 35, output_value = sameple_frequency)
                master.execute(TiHUB_address, cst.WRITE_SINGLE_REGISTER, 36, output_value = sameple_frequency)
                
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
            except modbus_tk.modbus.ModbusError as exc:
                st.write(self, st.warning('Warning',icon="⚠️"), exc)
    def StateChange(self, close_state=False):
        master = modbus_tcp.TcpMaster(host = Hub_host, port = register_port)
        master.set_timeout(1)
        if close_state == False:
            ''' 20h: 1B1(433,open), 1B0(432,close) '''
            master.execute(TiHUB_address, cst.WRITE_SINGLE_REGISTER, 32, output_value = open_switch)#close_switch
            st.info('Set successful')
        else:
            master.execute(TiHUB_address, cst.WRITE_SINGLE_REGISTER, 32, output_value = close_switch)#close_switch
            st.info('Close Switch')
            
    def StartThread(self):
        TiHub_streamlit_datacollection.TsEnd = False
        start_thread = TiHub_streamlit_datacollection.DataThread()
        add_script_run_ctx(start_thread)
        start_thread.start()
        
    def StopThread(self,mqtt_host):
        msg = {'State':1}
        jmsg = json.dumps(msg, ensure_ascii=False)
        publish.single("mislab/id/xy", jmsg, hostname= mqtt_host)