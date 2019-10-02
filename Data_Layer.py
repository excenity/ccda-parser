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
import datetime

# %% get data 

demographics, encounters, problemList, vitals, results, meds = PG.inputTables_simple()

# %% demographics

# age
demographics.age = pd.to_datetime(demographics.age)
demographics.age = datetime.datetime.now() - demographics.age
demographics.age = demographics.age.apply(lambda x: float(x.days / 365))

# race
demographics.race[demographics.race == '1002-5'] = 'American Indian or Alsaka Native'
demographics.race[demographics.race == '2028-9'] = 'Asian'
demographics.race[demographics.race == '2054-5'] = 'Black or African American'
demographics.race[demographics.race == '2076-8'] = 'Native Hawaiian or Other Pacific Islander'
demographics.race[demographics.race == '2106-3'] = 'White'

# ethnicity codes
demographics.ethnicity[demographics.ethnicity== '2186-5'] = 'Not Hispanic or Latino'
demographics.ethnicity[demographics.ethnicity== '2135-2'] = 'Hispanic or Latino'

# %% Vitals

vitals.columns = ['Vital_Name', 'Date', 'Vital_Value', 'pt_id']

# BP
BP_values = vitals[vitals.Vital_Name.str.contains('BP')]
BP_values.Vital_Value = BP_values.Vital_Value.str.replace(r'\D+', '').astype('int')
BP_values = BP_values.groupby(['pt_id', 'Date', 'Vital_Name'])['Vital_Value'].mean().unstack(fill_value = 0)
BP_values = BP_values.reset_index()

# BMI
BMI_values = vitals[vitals.Vital_Name.str.contains('BMI')]
BMI_values.Vital_Value = BMI_values.Vital_Value.str.replace(r'kg/m2', '').str.strip().astype('float')
BMI_values = BMI_values.groupby(['pt_id', 'Date', 'Vital_Name'])['Vital_Value'].mean().unstack(fill_value = 0)
BMI_values = BMI_values.reset_index()


# %% meds

# parse RXnorm Codes
meds['rxnorm'] = meds.RXnormCode.apply(lambda x: re.findall('\d+', x))
meds.rxnorm = meds.rxnorm.astype('str')

# conver med names to upper case
meds.GenericName = meds.GenericName.str.upper()

# get dosage information 
meds['dosage'] = meds.ProductStrength.apply(lambda x: re.findall('\d+', x))
meds.dosage = meds['dosage']

meds.rxnorm = meds.rxnorm.values[0]

