# -*- coding: utf-8 -*-
"""
Created on Sun Feb 12 13:30:05 2023
!streamlit run TiHub_streamlit_V.1.py
@author: Guan
"""
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
import sys
import gc
import pandas as pd
import numpy as np
from collections import deque
import streamlit as st
import streamlit.components.v1 as components
import pyvista as pv
import paho.mqtt.client as mqtt
import paho.mqtt.subscribe as subscribe
import paho.mqtt.publish as publish
import paho.mqtt.client as mqttcc
# import plotly.graph_objects as go
import queue
import json
import ast
# import segmentation_1
from PIL import Image
import copy
import queue
# from persist import persist, load_widget_state
from streamlit.runtime.scriptrunner.script_run_context import add_script_run_ctx
import gc
import altair as alt
# from streamlit_server_state import force_rerun_bound_sessions,server_state,server_state_lock,no_rerun
# import streamlit_sync
import TiHub_streamlit_thread

# In[]
TsEnd = False              # flag to stop data collection 
state_1  = False
folder_path = './SaveFile'   # initialization path
mqtt_host = "127.0.0.1"#"broker.emqx.io"
mqtt_portNo = 	1883
final_data_mqtt = []
vw_state = False


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
class TiHub_Strlit():
    def MainWindows(self):
        global state_1, final_data_pd,final_send,TsEnd,vw_state,all_data,folder_path,all_np,all_list,final_data_mqtt,stop
        title_style = '<p style="color:Orange; font-size: 20px;">Collect  vibration with TiHub</p>'
        st.markdown(title_style, unsafe_allow_html=True)  
        
        control_site = st.empty()
        monitor_site = st.empty()
               
        with control_site.container():    
            col1, col2, col3 = st.columns([1,1,1])
            with col1 :
                
                self.Rate = st.selectbox('Sample rate:',options=['1600'])
                if(st.button('Setregister')):
                    self.SetRegisterCollect()
                # st.checkbox("protection", )
                if (st.button("Connect to switch")):
      
                    self.SwitchChange(close=False)  
                    
                if (st.button("Switch Off")):
                    self.SwitchChange(close=True)
                    
                fpath = st.text_input('Save Floder','./SaveFile')
                folder_path = fpath
                   
            with col2:
                st.write("Button")    
                
                if (st.button('Collect')):    #,disabled=st.session_state.disabled                    
                    all_data = []
                    start_thread = TiHub_streamlit_thread.DataThread()
                    add_script_run_ctx(start_thread)
                    start_thread.start()

                    state_1 = True
                    vw_state = True

                if(st.button('Restart')):
                    # st.session_state.disabled1 = True
                    state_1 = False
                    TsEnd = True

                    self.StopCollection()
            
            with col3:
                if state_1 ==True:
                    st.markdown('start time:'+str(datetime.datetime.now())[0:-3])
                    self.SetupIcon() 
                elif state_1 == False:
                    st.markdown('stop time:'+str(datetime.datetime.now())[0:-3])
                    self.SetupIcon() 
                    
        with monitor_site.container():
            global all_np
            
            # MQTT subcribe
            def MQTTGet() :
                while True:
                    if not q.full():
                        msg = subscribe.simple("mislab/id/data1", hostname=mqtt_host)
                        msg_byte = msg.payload
                        dic_str = msg_byte.decode("utf-8")
                        mymqtt = ast.literal_eval(dic_str)
                        final_data_mqtt=(mymqtt['data'])

                        if final_data_mqtt == 0:
                            del final_data_mqtt,dic_str,mymqtt
                            break
                        else:
                            q.put(final_data_mqtt)

            st.write("---")
            
            title_style = '<p style="color:Orange; font-size: 20px;">Monitor</p>'
            st.markdown(title_style, unsafe_allow_html=True)
            write_pd = pd.DataFrame()
            fshow_pd_all = pd.DataFrame()
            # df_t = pd.DataFrame()
            q = queue.Queue(1600)

            if vw_state ==True:
                get_data = threading.Thread(target=MQTTGet)
                add_script_run_ctx(get_data)
                get_data.start()
                col4, col5, col6 = st.columns([1,1,1])
                chart =st.empty()

                while True:
                    all_list = np.array(q.get())  #np array
        
                    time_slice = int(len(all_list)*0.2) # 間格每0.2秒
                    vx = [([np.sqrt(np.mean(all_list[j:j+time_slice,1]**2)) for j in range(0, len(all_list),time_slice)])] # Showing the rms of per 0.2 second
                    vy = [([np.sqrt(np.mean(all_list[j:j+time_slice,2]**2)) for j in range(0, len(all_list),time_slice)])] 
                    vz = [([np.sqrt(np.mean(all_list[j:j+time_slice,3]**2)) for j in range(0, len(all_list),time_slice)])]
                    timetag = [([all_list[j,0] for j in range(0, len(all_list),int(len(all_list)*0.2))])]
                    all_list1 = timetag+vx+vy+vz
                    all_np = np.array(all_list1).T
                  
                    fshow_pd = ((pd.DataFrame((all_np),columns=['T','X','Y','Z'])))
                    # fshow_pd['T'] = pd.to_datetime(fshow_pd['T'])                      
                    # fshow_pd = fshow_pd.append(df_t)
                    fshow_pd_all = fshow_pd_all.append(fshow_pd)
                    # st.write(fshow_pd)

                    #顯示圖形
                    with chart:
                            
                        alt_layer = alt.Chart(fshow_pd_all).mark_line().encode(x='T') 
                        # st.altair_chart(alt.layer(alt_layer.mark_line(color='blue').encode(y=alt.Y('X',scale=alt.Scale(domain=[-5, 5]),title='Vibration')).interactive(),alt_layer.mark_line(color='red').encode(y=alt.Y('Y',scale=alt.Scale(domain=[-5, 5]))).interactive(),
                        #                             alt_layer.mark_line(color='green').encode(y=alt.Y('Z',scale=alt.Scale(domain=[-5 ,5]))).interactive()),use_container_width=True)
                        st.altair_chart(alt.layer(alt_layer.mark_line(color='blue').transform_fold(fold=['Vib_X'],as_=['axial','value']).encode(y=alt.Y('X',scale=alt.Scale(domain=[-2, 2]),title='Vibration'),color='axial:N'),alt_layer.mark_line(color='red').transform_fold(fold=['Vib_Y'],as_=['axial','value']).encode(y=alt.Y('Y',scale=alt.Scale(domain=[-2, 2])),color='axial:N'),
                                                  alt_layer.mark_line(color='green').transform_fold(fold=['Vib_Z'],as_=['axial','value']).encode(y=alt.Y('Z',scale=alt.Scale(domain=[-2, 2])),color='axial:N')),use_container_width=True)
                        if len(fshow_pd_all) > 50:
                            fshow_pd_all = fshow_pd_all[10:] 
                 
                    if TsEnd == True:
                        del fshow_pd,all_np,all_list,fshow_pd_all,write_pd,all_list1,q,alt_layer
  
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
                sameple_frequency = int(self.Rate)
                st.write('Samplerate:' + str(sameple_frequency))
                interval = (frame_payload * int(sameple_frequency/frame_payload))/sameple_frequency
                
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
                
    def SwitchChange(self,close=False):
        master = modbus_tcp.TcpMaster(host = Hub_host, port = register_port)
        master.set_timeout(1)
        if close == False:
            ''' 20h: 1B1(433,open), 1B0(432,close) '''
            master.execute(TiHUB_address, cst.WRITE_SINGLE_REGISTER, 32, output_value = open_switch)#close_switch
            st.info('Set successful')
        else:
            master.execute(TiHUB_address, cst.WRITE_SINGLE_REGISTER, 32, output_value = close_switch)#close_switch
            st.info('Close Switch')
              
    def StopCollection(self):
        global TsEnd ,dic_state, vw_state

        TsEnd  = True
        vw_state = False

        msg = {'State':1}
        jmsg = json.dumps(msg, ensure_ascii=False)
        publish.single("mislab/id/xy", jmsg, hostname= mqtt_host)
        
    def SetupIcon(self):
        global state_1

        if state_1 == True:
            image = st.empty()
            image = Image.open('./Logo/green-led.png')                                  # start icon
            st.image(image)
        elif state_1 == False and state_1 == False:
            image = st.empty()
            image = Image.open('./Logo/red-led.png')                                  # start icon
            st.image(image)
    
    def _tabs(self,tabs_data = {}, default_active_tab=0):
        tab_titles = list(tabs_data.keys())
        if not tab_titles:
            return None
    
        active_tab = st.radio("", tab_titles, index=default_active_tab)
        child = tab_titles.index(active_tab)+1
        st.markdown("""  
            <style type="text/css">
            div[role=radiogroup] > label > div:first-of-type {
                display: none
            }
            div[role=radiogroup] {
                flex-direction: unset
            }
            div[role=radiogroup] label {             
                border: 1px solid #999;
                background: #222;
                padding: 4px 12px;
                border-radius: 4px 4px 0 0;
                position: relative;
                top: 1px;
                }
            div[role=radiogroup] label:nth-child(""" + str(child) + """) {    
                background: #7a0 !important;
                border-bottom: 1px solid transparent;
            }            
            </style>
        """, unsafe_allow_html=True)
        tabs_data[active_tab]        
        return tabs_data[active_tab]
    
    def do_tabs(self):
        st.set_page_config(
            page_title= 'Tihub',
            page_icon="🔵"
            )   
        st.title("Welcome to TiHub")
 
        # st.sidebar.success(' ')
        tab_content = self._tabs({
                "TiHub Collecter": self.MainWindows,   
            })
        
        if callable(tab_content):
            tab_content()
            
        elif type(tab_content) == str:
            st.markdown(tab_content, unsafe_allow_html=True)
        else:
            st.write(tab_content)
     
# In[]
if __name__ == "__main__":
    # client = mqttcc.Client('Python')
    TiHub_Strlit().do_tabs()

    
    



