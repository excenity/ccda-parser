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

# Set up working directory 
os.chdir('C:/Users/jyk306/Documents/CHiP/C-CDA Parser/output')

# Set Up Working Directory + Associated Variables + prefixes for lxml
folderPath = "C:/Users/jyk306/Documents/CHiP/C-CDA Parser/Proto Files"
filePaths = glob.glob(folderPath+"/*")
prefix = '{urn:hl7-org:v3}'

# %% swap out blank datapoints

f_open = open('C:/Users/jyk306/Documents/CHiP/C-CDA Parser/Test Files/1.xml')
xml_file = f_open.read()
f_open.close()

xml_file = re.sub('<td/>', '<td>NA</td>', xml_file)
xml_file = re.sub('<td rowspan="1"/>', '<td>NA</td>', xml_file)

f_open = open('1_new.xml', 'w+')
f_open.write(xml_file)
f_open.close()

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
                print(node.TEXT_NODE)
                headerList.append(node.data)   
              
    return headerList

def getData(table):
    # get data of the table of interest
    
    dataList = []
            
    for data in table.getElementsByTagName("td"):
        nodes = data.childNodes
        for node in nodes:
            if node.nodeType == node.TEXT_NODE:
                dataList.append(node.data)
            else:
                dataList.append('NA')
    
    #print(dataList)        
    return dataList

def chunker(dataList, headers):
    # creates a new row for every new row of data based on length of data
    
    DataLL = []
    DataChunk =[]
    
    chunk_l = len(headers)
    
    while (len(dataList) != 0):
        DataChunk = dataList[:chunk_l]
        DataLL.append(DataChunk)
        dataList = dataList[chunk_l:]
        
    return DataLL

def dataFrame(table_name):
    # creates the final dataframe for the patient's table of interest
    
    global tableData
    
    key_table = getTable(table_name)
    
    headers = getHeaders(key_table)
    print(headers)
    tableData = getData(key_table)
    tableData_f = chunker(tableData,headers)
    
    df = pd.DataFrame(tableData_f)
    df.columns = headers
    
    return df

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

# %% run functions
def main():
    
    table_f = getAllPatients("Results")
    print(table_f)
    table_f.to_csv("test.csv")
    
    return 

main()

# %% test 

labs = getTable('Results')

dataList = []
n = 0

for data in labs.getElementsByTagName("td"):
        nodes = data.childNodes
        for node in nodes:
            n = n + 1
            if node.nodeType == node.TEXT_NODE:
                dataList.append(node.data)
            else:
                dataList.append('NA')

