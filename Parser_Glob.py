from xml.dom.minidom import parse
import pandas as pd
import lxml.etree as et
import glob

#Set Up Working Directory + Associated Variables + prefixes for lxml
folderPath = "/Users/Excenity/Documents/CHiP-LOCAL/H3/XML_Parser/Files/test-18"
filePaths = glob.glob(folderPath+"/*")
prefix = '{urn:hl7-org:v3}'

def getCurrPtId():
    # Gets the current patient ID

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

    titles = []

    for section in currPt.getElementsByTagName("section"):
        for title in section.getElementsByTagName("title"):
            titles.append(title)
            
    for t in titles: 
        nodes = t.childNodes
        for node in nodes:
            if node.nodeType == node.TEXT_NODE:
                print(node.data)
                
    return titles

def getTable(table_name):
        
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
    
    for title in table.getElementsByTagName("title"):
        nodes = title.childNodes
        for node in nodes:
            if node.nodeType == node.TEXT_NODE:
                print(node.data)

def getHeaders(table):
    
    headerList = []
    
    for data in table.getElementsByTagName("th"):
        nodes = data.childNodes
        for node in nodes:
            if node.nodeType == node.TEXT_NODE:
                print(node.TEXT_NODE)
                headerList.append(node.data)   
              
    return headerList

def getData(table):
    
    dataList = []
            
    for data in table.getElementsByTagName("td"):
        nodes = data.childNodes
        for node in nodes:
            if node.nodeType == node.TEXT_NODE:
                dataList.append(node.data)
            
    
    #print(dataList)        
    return dataList

def chunker(dataList, headers):
    
    DataLL = []
    DataChunk =[]
    
    chunk_l = len(headers)
    
    while (len(dataList) != 0):
        DataChunk = dataList[:chunk_l]
        DataLL.append(DataChunk)
        dataList = dataList[chunk_l:]
        
    return DataLL

def dataFrame(table_name):
    
    key_table = getTable(table_name)
    
    headers = getHeaders(key_table)
    print(headers)
    tableData = getData(key_table)
    tableData_f = chunker(tableData,headers)
    
    df = pd.DataFrame(tableData_f)
    df.columns = headers
    
    return df

def getAllPatients(table_name):

    global currFile
    global tree
    global root
    global currPt
    global ptId
    global ptFound

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

def main():
    
    table_f = getAllPatients("Encounters")
    print(table_f)
    table_f.to_csv("Encounters-18.csv")
    
main()


