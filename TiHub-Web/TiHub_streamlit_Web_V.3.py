    # -*- coding: utf-8 -*-
"""
Created on Sun Feb 12 13:30:05 2023
!streamlit run TiHub_streamlit_V.1.py
@author: Guan
"""

import datetime
import threading
import pandas as pd
import numpy as np
import streamlit as st
import paho.mqtt.subscribe as subscribe
import queue
import ast
from PIL import Image
from streamlit.runtime.scriptrunner.script_run_context import add_script_run_ctx
import altair as alt
import TiHub_streamlit_datacollection as tsdc
import TiHub_streamlit_control as tsc
# In[]
TsEnd = False              # flag to stop data collection 
state_1  = False
folder_path = './SaveFile'   # initialization path
mqtt_host = "127.0.0.1"#"broker.emqx.io"
mqtt_portNo = 	1883
final_data_mqtt = []
vw_state = False

tsdc.buffer = [[],[]]           # two buffers used for saving data
tsdc.time_tag = [[],[]]         # two timetags when collecting data by buffer
tsdc.save_start = [[],[]]       # two start timetag 
tsdc.save_end = [[],[]]
tsdc.time_offset = [0,0]
tsdc.file_data_name = []       
# In[]
class TiHub_Strlit():
    def MainWindows(self):
        global state_1, final_data_pd,final_send,TsEnd,vw_state,all_data,folder_path,all_np,all_list,final_data_mqtt,stop
        title_style = '<p style="color:Orange; font-size: 20px;">Collect  vibration with TiHub</p>'
        st.markdown(title_style, unsafe_allow_html=True)  
        control_site = st.empty()       # create control site
        monitor_site = st.empty()       # creaat monitor site
        with control_site.container():    
            col1, col2, col3 = st.columns([1,1,1]) 
            with col1 :                
                self.Rate = st.selectbox('Sample rate:',options=['1600'])      # setting rigister rate 
                if(st.button('Setregister')):
                    self.SetRegisterCollect()
                # st.checkbox("protection", )
                if (st.button("Connect to switch")):                           # open sensor 
                    self.SwitchChange(close=False)                   
                if (st.button("Switch Off")):                                  # close senor 
                    self.SwitchChange(close=True)
                    
                fpath = st.text_input('Save Floder','./SaveFile')              # setting save floder 
                tsdc.folder_path = fpath
            with col2:
                st.write("Button")                 
                if (st.button('Collect')):                                     # starting collect 
                    all_data = []                    
                    state_1 = True
                    vw_state = True          
                    self.StartCollection()
                if(st.button('Restart')):                                      # stop collect and reset  
                    state_1 = False
                    TsEnd = True
                    self.StopCollection()
            with col3:
                if state_1 ==True:
                    st.markdown('start time:'+str(datetime.datetime.now())[0:-3]) # showing icon
                    self.SetupIcon() 
                elif state_1 == False:
                    st.markdown('stop time:'+str(datetime.datetime.now())[0:-3])
                    self.SetupIcon()                     
        with monitor_site.container():
            global all_np
            # mqtt recieve thread
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
            fshow_pd_all = pd.DataFrame()
            q = queue.Queue(1600)
            if vw_state ==True:
                get_data = threading.Thread(target=MQTTGet)
                add_script_run_ctx(get_data)
                get_data.start()
                # col4, col5, col6 = st.columns([1,1,1])
                chart =st.empty()   # create a empty chart
                while True:
                    all_list = np.array(q.get())  # transform tp np array
                    time_slice = int(len(all_list)*0.2) 
                    vx = [([np.sqrt(np.mean(all_list[j:j+time_slice,1]**2)) for j in range(0, len(all_list),time_slice)])] # Showing the rms of per 0.2 second
                    vy = [([np.sqrt(np.mean(all_list[j:j+time_slice,2]**2)) for j in range(0, len(all_list),time_slice)])] 
                    vz = [([np.sqrt(np.mean(all_list[j:j+time_slice,3]**2)) for j in range(0, len(all_list),time_slice)])]
                    timetag = [([all_list[j,0] for j in range(0, len(all_list),int(len(all_list)*0.2))])]
                    all_list1 = timetag+vx+vy+vz
                    all_np = np.array(all_list1).T
                    fshow_pd = ((pd.DataFrame((all_np),columns=['T','X','Y','Z'])))
                    fshow_pd_all = fshow_pd_all.append(fshow_pd)
                    with chart:
                        # plot the graphic
                        alt_layer = alt.Chart(fshow_pd_all).mark_line().encode(x='T')
                        st.altair_chart(alt.layer(alt_layer.mark_line(color='blue').transform_fold(fold=['Vib_X'],as_=['axial','value']).encode(y=alt.Y('X',scale=alt.Scale(domain=[-1, 1]),title='RMS'),color='axial:N'),
                                                  alt_layer.mark_line(color='red').transform_fold(fold=['Vib_Y'],as_=['axial','value']).encode(y=alt.Y('Y',scale=alt.Scale(domain=[-1, 1])),color='axial:N'),
                                                  alt_layer.mark_line(color='green').transform_fold(fold=['Vib_Z'],as_=['axial','value']).encode(y=alt.Y('Z',scale=alt.Scale(domain=[-1, 1])),color='axial:N')),use_container_width=True)
                        if len(fshow_pd_all) > 50:  
                            fshow_pd_all = fshow_pd_all[10:]   # if time reach to 10sec, wwill clear the first sec               
                    if TsEnd == True:
                        del fshow_pd,all_np,all_list,fshow_pd_all,write_pd,all_list1,q,alt_layer
                        
    def SetRegisterCollect(self):
        tsc.TiHub_control().SetRegister(Rate= self.Rate)                       # set the register 
              
    def SwitchChange(self,close=False):
        tsc.TiHub_control().StateChange(close_state=close)                     # trun on/off sensor
        
    def StartCollection(self):
        tsc.TiHub_control().StartThread()                                      # start collecy 
        
    def StopCollection(self):
        global TsEnd ,dic_state, vw_state
        TsEnd  = True
        vw_state = False                                                       # close monitor site
        tsdc.iti = 0
        tsc.TiHub_control().StopThread(mqtt_host=mqtt_host)                    # stop collect
    def SetupIcon(self):
        global state_1
        if state_1 == True:
            image = st.empty()
            image = Image.open('./Logo/green-led.png')                         # display start icon
            st.image(image)
        elif state_1 == False and state_1 == False:
            image = st.empty()
            image = Image.open('./Logo/red-led.png')                           # display stop icon
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
    TiHub_Strlit().do_tabs()