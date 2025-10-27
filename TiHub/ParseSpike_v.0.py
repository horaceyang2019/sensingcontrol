# -*- coding: utf-8 -*-
"""
Created on Sat Jul 16 09:52:02 2022

This code will access the files in the specified folder and show the results of each steps 
Designed for parsing data collected from ITRI and TiHub accelerometers 

Inputs: *.xslx files
Output: XMerged.xlsx
    
@author: hao
"""
import pandas as pd
import matplotlib.pyplot as plt
import xlsxwriter
import glob
import os
import re
import Init_Parameter as init

# In[1]:
''' 
Parameters:
    message: message title 
    variables: message data 
    flag: show this steps or not
'''
def ShowSteps(message, variables, flag):
    print(f'{message} {variables}\n')
    if flag: input('Press Enter to continue...')
       
# In[10]: Load data 
''' 
Parameters:
    file: data source path with extension in string
Result:
    df: dataframe
    targte_list: list with target name
'''
def LoadData(file):
    print(f'Loading {file}...')                              
    filename, file_extension = os.path.splitext(file)
    if file_extension == '.csv':
        df = pd.read_csv(file)
    if file_extension == '.xlsx':
        df = pd.read_excel(file)       # load the raw data in excel file
    target_list = df.columns       # only get the list what need to process 
    return df[target_list], target_list 
   
# In[20]: plot and slow the data
''' 
Parameters:
    title: title of chart
    p_data: data for plot (in data frame)
    name: column name for plot
    rate: data rate in second
Result:
    plot vibration signals of three axes 
'''
def PlotResult(title, p_data, name, rate):
    for i in range(3):
        plt.subplot(3, 1, i+1);       # assign the sub_plot chart
        if i == 0:                    # first subplot 
            plt.title(f'{title} \n(a) {name[0]} (b) {name[1]} (c) {name[2]}')
        plt.plot(p_data.iloc[:,i])    # plot the data from the row 
        plt.xlabel(f'point interval {1/rate} (sec)'); plt.ylabel('g')
    plt.show() 
    
# In[30]: 
''' 
Parameters:
    time: timetag
    data: data to derived their average 
    interval: how many points for average
    denoise: flag to indicate whether de-noise or not
Result:
    s_data: in dataframe
'''
def CalculateFeature(data):
    abs_mean = data.abs().mean(axis=0)
    # std =  data.std()
    features = round(abs_mean, 4)
    return features

def ExtractFeature(time, data, interval, denoise = True):
    dfs = pd.DataFrame()
     # denoise data by a wavelet filter 
    d_data = data # Denoise.wden(data, 'sqtwolog', 'soft', 'mln', 3, 'db5')  
    time_tag = []
    for i in range(int(len(d_data)/interval)):     # calculate mean features
        w_data = d_data.iloc[int(i*interval): int((i+1)*interval), 0:3]
        vib = CalculateFeature(w_data).to_list()
        features = pd.DataFrame([vib], columns = data.columns[0:3]) 
         # t = datetime.strptime(time.iloc[int((i+0.5)*interval)], '%Y/%m/%d %H:%M:%S')
        time_tag.append (time.iloc[int(i*interval)])
        #features['time'] =  # take the middle time 
        if dfs.empty:        
            dfs = features
        else: 
            dfs = pd.concat([dfs, features], ignore_index = True) 
            
    dfs.insert(0, 'Timetag', time_tag)
    return dfs
    
# In[7]: save the preprocessed result into a excel file
def SaveResult(file, sheet, columns, data):
    pattern = re.compile(r'\/\S[^\/]+')  # find the pattern '/*', '\S': alpha+number, '^\/': excluded  
    match = re.findall(pattern, file)
    path = ''                            # clear path
      # build the path by exclude the last file name
    for i in range(len(match)-1):  path = path + match[i]   #
    if not os.path.exists('.'+path):   os.makedirs('.'+path)     
    
    if not os.path.isfile(file):
        workbook = xlsxwriter.Workbook(file) # new an excel file with 'xlsx' extension
        worksheet = workbook.add_worksheet('Description')
        worksheet.write(0, 0, path)
        workbook.close()

    pd_data = pd.DataFrame(data)
    pd_data.columns = columns
    with pd.ExcelWriter(file, engine='openpyxl', mode='a') as writer:  
         pd_data.to_excel(writer, sheet_name = sheet, index = False)    
         
# In[100]
if __name__ == '__main__':   
    path = init.source_folder + '*.*' 

    merged = pd.DataFrame()   # assign an empty data frame 
    # file = glob.glob(path)[0]                     
    for file in glob.glob(path):     # read all files in this folder
        # Step 1: load data from a file 
        df, target_list = LoadData(file)
        
        vib_axes = ['X', 'Y', 'Z']
        PlotResult('From' + file, df[vib_axes], vib_axes, rate = init.sample_rate)
        ShowSteps('Step 1: Loading data.\n', df.head(), init.stepwise_check)
 
        # Step 2: extract the features from data by column      
        sum_data = ExtractFeature(time = df['Timetag'], data = df[vib_axes], 
                                  interval = init.sample_rate * init.sum_duration)   
        PlotResult(f'Average per {init.sum_duration} sec', sum_data[vib_axes], vib_axes, rate = 1/init.sum_duration)          
        ShowSteps('Step 2: Get the average data.\n', sum_data, init.stepwise_check)
        
        SaveResult(init.output_file, file[-17:-4], target_list, sum_data)        
       
        # Step 3: append data into the dataframe
        if merged.empty:               # if the merged data frame is empty 
            merged = sum_data          # save the first data frame
        else: 
            merged = pd.concat([merged, sum_data], ignore_index = True)  # otherwise  
                 
        ShowSteps('Step 3: Merge the last three data.\n', merged[-3:], init.stepwise_check)
        
    # Step 4: Save the final restult
    
    with pd.ExcelWriter(init.output_file, engine='openpyxl', mode='a') as writer:  
            merged.to_excel(writer, sheet_name = init.merged_sheet)    
    print(f'Step 4: Output file is {init.output_file}')                    