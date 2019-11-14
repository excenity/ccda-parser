# -*- coding: utf-8 -*-
"""
Created on Tue Sep  3 11:08:26 2019

@author: jyk306
"""

import Parser_Glob
import pandas as pd
import re
import datetime

class DataLayer:
    def __init__(self, projectpath):
        self.projectpath = projectpath
        PG = Parser_Glob.xmlParser(projectpath)

        # %% get data

        self.demographics, self.encounters, self.problemList, self.vitals, self.results, self.meds = PG.inputTables_simple()

        # %% demographics

        # age
        self.demographics.age = pd.to_datetime(self.demographics.age)
        self.demographics.age = datetime.datetime.now() - self.demographics.age
        self.demographics.age = self.demographics.age.apply(lambda x: float(x.days / 365))

        # race
        self.demographics.loc[self.demographics.race == '1002-5', 'race'] = 'American Indian or Alaska Native'
        self.demographics.loc[self.demographics.race == '2028-9', 'race'] = 'Asian'
        self.demographics.loc[self.demographics.race == '2054-5', 'race'] = 'Black or African American'
        self.demographics.loc[self.demographics.race == '2076-8', 'race'] = 'Native Hawaiian or Other Pacific Islander'
        self.demographics.loc[self.demographics.race == '2106-3', 'race'] = 'White'

        # ethnicity codes
        self.demographics.loc[self.demographics.ethnicity == '2186-5', 'ethnicity'] = 'Not Hispanic or Latino'
        self.demographics.loc[self.demographics.ethnicity == '2135-2', 'ethnicity'] = 'Hispanic or Latino'

        # %% Vitals

        self.vitals.columns = ['Vital_Name', 'Date', 'Vital_Value', 'pt_id']

        # BP
        self.BP_values = self.vitals[self.vitals.Vital_Name.str.contains('BP')]
        self.BP_values.Vital_Value = self.BP_values.Vital_Value.str.replace(r'\D+', '').astype('int')
        self.BP_values = self.BP_values.groupby(['pt_id', 'Date', 'Vital_Name'])['Vital_Value'].mean().unstack(fill_value = 0)
        self.BP_values = self.BP_values.reset_index()

        # BMI
        self.BMI_values = self.vitals[self.vitals.Vital_Name.str.contains('BMI')]
        self.BMI_values.Vital_Value = self.BMI_values.Vital_Value.str.replace(r'kg/m2', '').str.strip().astype('float')
        self.BMI_values = self.BMI_values.groupby(['pt_id', 'Date', 'Vital_Name'])['Vital_Value'].mean().unstack(fill_value = 0)
        self.BMI_values = self.BMI_values.reset_index()


        # %% meds

        # parse RXnorm Codes
        self.meds['rxnorm'] = self.meds.RXnormCode.apply(lambda x: re.findall('\d+', x))
        self.meds.rxnorm = self.meds.rxnorm.astype('str')

        # conver med names to upper case
        self.meds.GenericName = self.meds.GenericName.str.upper()

        # get dosage information
        self.meds['dosage'] = self.meds.ProductStrength.apply(lambda x: re.findall('\d+', x))
        self.meds.dosage = self.meds['dosage']

        self.meds.rxnorm = self.meds.rxnorm.values[0]
