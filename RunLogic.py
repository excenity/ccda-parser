import pandas as pd
import HTNLogic
import Data_Layer

DL = Data_Layer.DataLayer('C:/Users/farha/Google Drive/EW/CDAPtViz/ccda-parser/')

#Todo: Move initial path selection to this file
#Todo: Pass paths through Logic to CardMaker

# For loop for each patient name/patient id pair in the Demographics table
# Currently only for HTN, but can figure out a way to be more extensible in the future
for i, eachPtRow in DL.demographics.iterrows():
    pt_id = eachPtRow['pt_id']

    dg = eachPtRow
    encDF = DL.encounters[DL.encounters['pt_id'] == pt_id]
    probDF = DL.problemList[DL.problemList['pt_id'] == pt_id]
    medsDF = DL.meds[DL.meds['pt_id'] == pt_id]
    vitDF = DL.vitals[DL.vitals['pt_id'] == pt_id]
    bmiDF = DL.BMI_values[DL.BMI_values['pt_id'] == pt_id]
    bpDF = DL.BP_values[DL.BP_values['pt_id'] == pt_id]
    resDF = DL.results[DL.results['pt_id'] == pt_id]

    HTNRunner = HTNLogic.HTNLogic(pt_id, dg, encDF, probDF, medsDF, vitDF, bmiDF, bpDF, resDF)
    HTNRunner.run_htn_logic()
    # The above line should be self sufficient, running to produce all the outputs for HTN for this patient
