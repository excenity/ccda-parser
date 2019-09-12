# -*- coding: utf-8 -*-
"""
Created on Tue Sep  3 11:08:26 2019

@author: jyk306
"""
# %% Prepatory Work 
import os
os.chdir('C:/Users/jyk306/Documents/CHiP/C-CDA Parser/git/')

# %% import data 

import Parser_Glob as PG
import pandas as pd
import re

# %% get data 

demographics, encounters, problemList, vitals, results, meds = PG.inputTables_simple()

# %% BP 

vitals.columns = ['Vital_Name', 'Date', 'Vital_Value', 'pt_id']

vitals = vitals[vitals.Vital_Name.str.contains('BP')]

vitals.Vital_Value = vitals.Vital_Value.str.replace(r'\D+', '').astype('int')

vitals = vitals.groupby(['pt_id', 'Date', 'Vital_Name'])['Vital_Value'].mean().unstack(fill_value = 0)
vitals = vitals.reset_index()

# %% meds

# parse RXnorm Codes
meds['rxnorm'] = meds.RXnormCode.apply(lambda x: re.findall('\d+', x))
meds.rxnorm = meds.rxnorm.astype('str')

# conver med names to upper case
meds.GenericName = meds.GenericName.str.upper()

# get dosage information 
meds['dosage'] = meds.ProductStrength.apply(lambda x: re.findall('\d+', x))
meds.dosage = meds['dosage']

