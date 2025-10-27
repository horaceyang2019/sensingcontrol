# -*- coding: utf-8 -*-
"""
Created on Thu Aug  4 14:18:09 2022

@author: hao
"""
index = 0                        # index for using different source folder
  # fpath 
conditions = [['/0822-22-PMC/'],
              ]

source_folder = './Source'+ conditions[index][0]  
output_folder = './Output'+ conditions[index][0] 
  
file_ext = '.xlsx'                   # source and output files extension 
output_file = output_folder + 'XMerged' + file_ext
merged_sheet = 'Merged'              # sheet name of output file
stepwise_check = False                # show the steps or not