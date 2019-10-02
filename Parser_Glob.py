# -*- coding: utf-8 -*-
"""
Newest XML Parser Tool

For AMIA Submission 
"""
# %%  prep
from xml.dom.minidom import parse
import pandas as pd
import lxml.etree as et
import glob
import os 
import re

win_path = 'C:/Users/jyk306/Documents/CHiP/C-CDA Parser/git/'
mac_path = '/Users/Excenity/Documents/CHiP-LOCAL/C-CDA_Parser/ccda-parser/'

dir_path = win_path

# Set up working directory 
os.chdir(dir_path + 'output')

# Set Up Working Directory + Associated Variables + prefixes for lxml
folderPath = dir_path + "Test Files"
filePaths = glob.glob(folderPath+"/*")
prefix = '{urn:hl7-org:v3}'

# %% read directory function
def read_dir():
    path = str()
    
    print('input folder path:')
    path = input()
    
    return path

# %% swap out blank datapoints
i = 1 

for path in filePaths:
    
    # read file
    f_open = open(path)
    xml_file = f_open.read()
    f_open.close()
    
    # replace null nodes 
    xml_file = re.sub('<td/>', '<td>NA</td>', xml_file)
    
    # write new file 
    file_name = str(i) + '_new.xml'
    f_open = open(file_name, 'w+')
    f_open.write(xml_file)
    f_open.close()
    i = i + 1 

# %% Read New Data

folderPath = dir_path + "Proto Files"
filePaths = glob.glob(folderPath+"/*")
prefix = '{urn:hl7-org:v3}'

# %% functions 
def getCurrPtId():
    # get patient id 
    
    global ptFound 
    ptFound = False
    global ptId

    for elem in root.iter():
        if ptFound:
            ptId = elem.attrib
            break
        if elem.tag == prefix+"patientRole":
            ptFound = True

    return ptId
 
def tableNames():
    # get the table names in the C-CDA file
    
    titles = []

    for section in currPt.getElementsByTagName("section"):
        for title in section.getElementsByTagName("title"):
            titles.append(title)
            
    for t in titles: 
        nodes = t.childNodes
        for node in nodes:
            if node.nodeType == node.TEXT_NODE:
                print(node.data)
    
def getTable(table_name):
    # get the relevant table for the file 
        
    global currPt 
    global key_table

    for section in currPt.getElementsByTagName("section"):
        for title in section.getElementsByTagName("title"):
            nodes = title.childNodes
            for node in nodes:
                if node.nodeType == node.TEXT_NODE:
                    if node.data == table_name:
                        #print ("key_table:", node.data)
                        key_table = section
                    #else:
                        #print(node.data, "- Not This Table")
    return key_table

def printTableName(table):
    # get the table of interest based on name
    
    for title in table.getElementsByTagName("title"):
        nodes = title.childNodes
        for node in nodes:
            if node.nodeType == node.TEXT_NODE:
                print(node.data)

def getHeaders(table):
    # get headers of the table of interest
    
    headerList = []
    
    for data in table.getElementsByTagName("th"):
        nodes = data.childNodes
        for node in nodes:
            if node.nodeType == node.TEXT_NODE:
                #print(node.TEXT_NODE)
                headerList.append(node.data)   
              
    return headerList

def getData(table):
    # get data of the table of interest
    
    dataList = []
    i = 1         
    for data in table.getElementsByTagName("td"):
        nodes = data.childNodes
        for node in nodes:
            #print('node number:', i) 
            i = i + 1
            if node.nodeType == node.TEXT_NODE:
                dataList.append(node.data)
        if data.getAttribute("rowspan") != '':
            rowspan_var = 'rowspan=' + str(data.getAttribute("rowspan"))
            dataList.append(rowspan_var)        
    
    #print(dataList)        
    return dataList

def chunker(dataList, headers):
    # creates a new row for every new row of data based on length of data
    global repeats
    
    DataLL = []
    DataChunk =[] 
    repeats = 0
    column = 0    
    
    chunk_l = len(headers)
    
    while (len(dataList) != 0):
        
        DataChunk = dataList[:chunk_l]
        
        if repeats > 0:
            DataChunk = DataChunk[:column] + ['NA'] + DataChunk[column:]
            repeats = repeats - 1 
            DataChunk = DataChunk[:-1]
            DataLL.append(DataChunk)
            dataList = dataList[chunk_l-1:]
        else:
            for i in range(len(DataChunk)):
                if re.match('^rowspan=', DataChunk[i]) is not None:     
                    column =  i 
                    repeats = int(re.split('^rowspan=', DataChunk[i])[1]) - 1  
                    DataChunk[i] = 'NA'        
            DataLL.append(DataChunk)
            dataList = dataList[chunk_l:]
        
    return DataLL

def dataFrame(table_name):
    # creates the final dataframe for the patient's table of interest
    
    global tableData
    
    key_table = getTable(table_name)
    
    headers = getHeaders(key_table)
    #print(headers)
    tableData = getData(key_table)
    tableData_f = chunker(tableData, headers)
    
    df = pd.DataFrame(tableData_f)
    df.columns = headers
    
    return df

def getDemographics():
# gets demographics information of patient 
    
    global pt_name, pt_age, race_code, ethnicity_code, gender_code, demographics, demographics_pt
    
    i = 0
    
    for path in filePaths:
        
        pt_name = 'NA'
        pt_age = 'NA'
        race_code = 'NA'
        ethnicity_code = 'NA'
        gender_code = 'NA'
    
        file = parse(path)
        
        name = file.getElementsByTagName('nameCode')
        for node in name:    
            pt_name = node.getAttribute('code')
            if pt_name is None: 
                print('no name information found')
            
            
        age = file.getElementsByTagName('birthTime')
        for node in age:    
            pt_age = node.getAttribute('value')
            if pt_age is None: 
                print('no name information found')
                pt_age = 'no birthday'
                
        race = file.getElementsByTagName('raceCode')
        for node in race:    
            race_code = node.getAttribute('code')
            if race_code is None: 
                print('no race information found')

                
        ethnicity = file.getElementsByTagName('ethnicGroupCode')
        for node in ethnicity: 
            ethnicity_code = node.getAttribute('code')
            if ethnicity_code is None:
                print('no ethnicity information found')
   
        gender = file.getElementsByTagName('administrativeGenderCode')
        for node in gender: 
            gender_code = node.getAttribute('code')
            if gender_code is None:
                print('no gender information found')
                   
        # create data frame
        if i == 0: 
            demographics_pt = pd.DataFrame({"name"      : [pt_name],
                                            "age"       : [pt_age],
                                            "race"      : [race_code],
                                            "ethnicity" : [ethnicity_code],
                                            "gender"    : [gender_code]})
            demographics = demographics_pt
            i = 1
        else:
            demographics_pt = pd.DataFrame({"name"      : [pt_name],
                                            "age"       : [pt_age],
                                            "race"      : [race_code],
                                            "ethnicity" : [ethnicity_code],
                                            "gender"    : [gender_code]})
            demographics = pd.concat([demographics, demographics_pt])
          
    return demographics

def getAllPatients(table_name):
    # puts everything together 

    global currFile
    global tree
    global root
    global currPt
    global ptId
    global ptFound, df_row

    dfs = []
    
    for currFile in filePaths:
    
        # Get Patient ID
        tree = et.parse(currFile)
        root = tree.getroot()
        pt_ID_t = getCurrPtId()
        pt_ID= pt_ID_t['extension']
    
        # Get data 
        currPt = parse(currFile)
        df_row = dataFrame(table_name)
        
        #  Create Column of Patient ID
        pt_id_rows = []
        df_len = len(df_row.index)
        for i in range(df_len):
        	pt_id_rows.append(pt_ID)
    
        # Merge Patient ID to DF
        df_row['pt_id'] = pt_id_rows
        dfs.append(df_row)

    table_final = pd.concat(dfs, sort=False)
    
    return table_final

# %% get table names 
def inputTables():
# function for getting the names of the relevant 
    
    global currPt
    
    currFile = filePaths[1]
    
    currPt = parse(currFile)
    
    tableNames()
    
    print('Enter name for Encounters table:')
    tblName_Encounters = input()
    
    print('Enter name for Problem List table:')
    tblName_ProblemList = input()
    
    print('Enter name for Vitals table:')
    tblName_Vitals = input()
    
    print('Enter name for Results table:')
    tblName_Results = input()
    
    print('Enter name for Medications table:')
    tblName_Meds = input()

    encounters = getAllPatients(tblName_Encounters)
    problemList = getAllPatients(tblName_ProblemList)
    vitals = getAllPatients(tblName_Vitals)
    results = getAllPatients(tblName_Results)
    meds = getAllPatients(tblName_Meds)

    return demographics, encounters, problemList, vitals, results, meds


# %%  Simple Input
def inputTables_simple():
# function for getting the names of the relevant 
        
    encounters = getAllPatients('Encounters')
    problemList = getAllPatients('Problem List')
    vitals = getAllPatients('Vital Signs')
    results = getAllPatients('Results')
    meds = getAllPatients('Medications')
    demographics = getDemographics()

    return demographics, encounters, problemList, vitals, results, meds

