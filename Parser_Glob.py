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


class xmlParser:
    def __init__(self, curr_path):
        self.curr_path = curr_path

        self.input_path = self.curr_path + '/Test Files/'
        self.intermed_path = self.curr_path + '/Proto Files/'
        self.output_path = self.curr_path + '/Output/'

        os.chdir(self.intermed_path)  # Set up working directory

        # Set Up Working Directory + Associated Variables + prefixes for lxml
        self.inputFilePaths = glob.glob(self.input_path + "/*")
        self.intermedFilePaths = glob.glob(self.intermed_path + "/*")
        self.prefix = '{urn:hl7-org:v3}'

        i = 1   # swap out blank datapoints

        for path in self.inputFilePaths:
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

        # Set up working directory
        os.chdir(self.output_path)

    # %% read directory function
    def read_dir(self):
        path = str()

        print('input folder path:')
        path = input()

        return path

    # %% functions
    def getCurrPtId(self):
        # get patient id

        global ptFound
        ptFound = False
        global ptId

        for elem in root.iter():
            if ptFound:
                ptId = elem.attrib
                break
            if elem.tag == self.prefix + "patientRole":
                ptFound = True

        return ptId


    def tableNames(self):
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


    def getTable(self, table_name):
        # get the relevant table for the file

        global currPt
        global key_table

        for section in currPt.getElementsByTagName("section"):
            for title in section.getElementsByTagName("title"):
                nodes = title.childNodes
                for node in nodes:
                    if node.nodeType == node.TEXT_NODE:
                        if node.data == table_name:
                            # print ("key_table:", node.data)
                            key_table = section
                        # else:
                        # print(node.data, "- Not This Table")
        return key_table


    def printTableName(self, table):
        # get the table of interest based on name

        for title in table.getElementsByTagName("title"):
            nodes = title.childNodes
            for node in nodes:
                if node.nodeType == node.TEXT_NODE:
                    print(node.data)


    def getHeaders(self, table):
        # get headers of the table of interest

        headerList = []

        for data in table.getElementsByTagName("th"):
            nodes = data.childNodes
            for node in nodes:
                if node.nodeType == node.TEXT_NODE:
                    # print(node.TEXT_NODE)
                    headerList.append(node.data)

        return headerList


    def getData(self, table):
        # get data of the table of interest

        dataList = []
        i = 1
        for data in table.getElementsByTagName("td"):
            nodes = data.childNodes
            for node in nodes:
                # print('node number:', i)
                i = i + 1
                if node.nodeType == node.TEXT_NODE:
                    dataList.append(node.data)
            if data.getAttribute("rowspan") != '':
                rowspan_var = 'rowspan=' + str(data.getAttribute("rowspan"))
                dataList.append(rowspan_var)

                # print(dataList)
        return dataList


    def chunker(self, dataList, headers):
        # creates a new row for every new row of data based on length of data
        global repeats

        DataLL = []
        DataChunk = []
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
                dataList = dataList[chunk_l - 1:]
            else:
                for i in range(len(DataChunk)):
                    if re.match('^rowspan=', DataChunk[i]) is not None:
                        column = i
                        repeats = int(re.split('^rowspan=', DataChunk[i])[1]) - 1
                        DataChunk[i] = 'NA'
                DataLL.append(DataChunk)
                dataList = dataList[chunk_l:]

        return DataLL


    def dataFrame(self, table_name):  # Todo: Someday rename this
        # creates the final dataframe for the patient's table of interest

        global tableData

        key_table = self.getTable(table_name)

        headers = self.getHeaders(key_table)
        # print(headers)
        tableData = self.getData(key_table)
        tableData_f = self.chunker(tableData, headers)

        df = pd.DataFrame(tableData_f)
        df.columns = headers

        return df


    def getDemographics(self):
        # gets demographics information of patient

        global pt_ID_t, pt_ID, pt_first_name, pt_last_name, pt_age, race_code, ethnicity_code, gender_code, demographics, demographics_pt, root

        i = 0
        pt_ID = []

        for path in self.intermedFilePaths:

            pt_ID_t = 'NA'
            pt_first_name = 'NA'
            pt_last_name = 'NA'
            pt_age = 'NA'
            race_code = 'NA'
            ethnicity_code = 'NA'
            gender_code = 'NA'

            file = et.parse(path)
            root = file.getroot()

            pt_ID_t = self.getCurrPtId()
            pt_ID_t = pt_ID_t['extension']
            pt_ID.append(pt_ID_t)
            print(i, pt_ID_t)

            file = parse(path)

            first_name = file.getElementsByTagName('given')
            nodes = first_name[0].childNodes
            node = nodes[0]
            pt_first_name = node.data
            if pt_first_name is None:
                print('no name information found')

            last_name = file.getElementsByTagName('family')
            nodes = last_name[0].childNodes
            node = nodes[0]
            pt_last_name = node.data
            if pt_last_name is None:
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
                demographics_pt = pd.DataFrame({"pt_id": [pt_ID_t],
                                                "first_name": [pt_first_name],
                                                "last_name": [pt_last_name],
                                                "age": [pt_age],
                                                "race": [race_code],
                                                "ethnicity": [ethnicity_code],
                                                "gender": [gender_code]})
                demographics = demographics_pt
                i = 1
            else:
                demographics_pt = pd.DataFrame({"pt_id": [pt_ID_t],
                                                "first_name": [pt_first_name],
                                                "last_name": [pt_last_name],
                                                "age": [pt_age],
                                                "race": [race_code],
                                                "ethnicity": [ethnicity_code],
                                                "gender": [gender_code]})
                demographics = pd.concat([demographics, demographics_pt])
                i = i + 1

        return demographics


    def getAllPatients(self, table_name):
        # puts everything together

        global currFile
        global tree
        global root
        global currPt
        global ptId
        global ptFound, df_row

        dfs = []

        for currFile in self.intermedFilePaths:

            # Get Patient ID
            tree = et.parse(currFile)
            root = tree.getroot()
            pt_ID_t = self.getCurrPtId()
            pt_ID = pt_ID_t['extension']

            # Get data
            currPt = parse(currFile)
            df_row = self.dataFrame(table_name)

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
    def inputTables(self):
        # function for getting the names of the relevant

        global currPt

        currFile = self.intermedFilePaths[1]

        currPt = parse(currFile)

        self.tableNames()

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

        encounters = self.getAllPatients(tblName_Encounters)
        problemList = self.getAllPatients(tblName_ProblemList)
        vitals = self.getAllPatients(tblName_Vitals)
        results = self.getAllPatients(tblName_Results)
        meds = self.getAllPatients(tblName_Meds)

        return demographics, encounters, problemList, vitals, results, meds


    # %%  Simple Input
    def inputTables_simple(self):
        # function for getting the names of the relevant

        encounters = self.getAllPatients('Encounters')
        problemList = self.getAllPatients('Problem List')
        vitals = self.getAllPatients('Vital Signs')
        results = self.getAllPatients('Results')
        meds = self.getAllPatients('Medications')
        demographics = self.getDemographics()

        return demographics, encounters, problemList, vitals, results, meds
