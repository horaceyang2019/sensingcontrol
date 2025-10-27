# -*- coding: utf-8 -*-
"""
Created on Fri Jul 22 17:10:30 2022

@author: hao
"""

# TiHub for parameters and collection

# In[1] TiHub_parameters：執行TiHub參數設定
更改加速規取樣率：

*更改取樣率：SamepleFrequency (程式碼23行)
*若有更改取樣率，程式(In[1])執行完畢需關閉電源重新開啟，所設定取樣率才會更新

# In[2] TiHub_collection：執行TiHub數據收集
加速規收集數據包括：

*目前只設定PORT1505---Sensor_1
*若需增加其他PORT，需自行增加。PORT1506---Sensor_2, PORT1507---Sensor_3, PORT1508---Sensor_4
*x, y, z, timetag 依序存檔成csv


@TiHub_Mqtt

# In[1] TiHub_parameters：執行TiHub參數設定
更改加速規取樣率：

*更改取樣率：SamepleFrequency (程式碼第23行)
*若有更改取樣率，程式(In[1])執行完畢需關閉電源重新開啟，所設定取樣率才會更新

# In[2] TiHub_Mqtt_collection：執行TiHub_Mqtt數據收集

*透過Mqtt來發送開始(b = 1)與結束(b = 2)
*目前只設定PORT1505---Sensor_1
*若需增加其他PORT，需自行增加。PORT1506---Sensor_2, PORT1507---Sensor_3, PORT1508---Sensor_4
*x, y, z, timetag 依序存檔成csv
*若資料需外拋可設定 MQTT Connect(程式碼92~97行)

# In[3] TiHub_thread

*執行序
