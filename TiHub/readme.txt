# -*- coding: utf-8 -*-
"""
Created on Fri Jul 22 17:10:30 2022

@author: hao
"""

# TiHub for parameters and collection
SetRegister()：執行TiHub參數設定
更改加速規取樣率：

*更改取樣率：sameple_frequency (程式碼23行)
*若有更改取樣率，副程式(SetRegister())執行完畢需關閉電源重新開啟，所設定取樣率才會更新

*目前只設定PORT1505---Sensor_1
*若需增加其他PORT，需自行增加。PORT1506---Sensor_2, PORT1507---Sensor_3, PORT1508---Sensor_4

MainLoop()：執行TiHub背景收集
加速規收集數據包括：
'Vib_X','Vib_Y','Vib_Z' , 'Timetag': 依序存檔成csv

---------------------------------------------------------------------------
@TiHub_MQTT

# TiHub_Mqtt_collection：執行TiHub_Mqtt數據收集

*透過Mqtt來發送開始(b = 1)與結束(b = 2)
*目前只設定PORT1505---Sensor_1
*若需增加其他PORT，需自行增加。PORT1506---Sensor_2, PORT1507---Sensor_3, PORT1508---Sensor_4
*x, y, z, timetag 依序存檔成csv
*若資料需外拋可設定 MQTT Connect(程式碼92~97行)