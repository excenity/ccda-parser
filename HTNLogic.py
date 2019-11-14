"""
Created by FarhadG - October 2019

"""
import re
import pandas as pd
import cardMaker

class HTNLogic:

    def __init__(self, pt_id, dg, encdf, probdf, medsdf, vitdf, bmidf, bpdf, resdf):
        # Create HTN Med Table
        self.htn_med_table = pd.read_excel('C:/Users/farha/Google Drive/EW/CDAPtViz/ccda-parser/HTN Meds.xlsx').iloc[:, :-1]

        self.rec_List = []

        # Demographics
        self.pt_id = pt_id

        self.dg = dg
        self.dg: pd.Series

        self.pt_name = str(self.dg['first_name'] + " " + self.dg['last_name'])
        self.pt_age = int(dg['age'])
        self.pt_sex = str(dg['gender'])
        self.pt_race = str(dg['race'])

        # Encounters in encdf
        self.encdf = encdf

        # PMH - Please note that while the below definitions are imperfect as currently written, they can be improved upon
        self.probdf = probdf
        self.hx_htn = probdf['Problem Description'].str.contains('hypertensi', case=False).any()
        self.hx_ua = probdf['Problem Description'].str.contains('unstable angina', case=False).any()
        self.hx_sihd = probdf['Problem Description'].str.contains('angina', case=False).any() and not self.hx_ua
        self.hx_mi = probdf['Problem Description'].str.contains('myocardial infaraction', case=False).any()
        self.hx_stktia = probdf['Problem Description'].str.contains('stroke', case=False).any()
        self.hx_cvd = self.hx_sihd or self.hx_ua or self.hx_mi
        self.hx_hf = probdf['Problem Description'].str.contains('heart failure', case=False).any()
        self.hx_hfpef = self.hx_hf and probdf['Problem Description'].str.contains('preserved ejection', case=False).any()
        self.hx_dm = probdf['Problem Description'].str.contains('diabetes mellitus', case=False).any()
        self.hx_ckd = probdf['Problem Description'].str.contains('chronic kidney', case=False).any()

        # Meds
        self.medsdf = self.flagMedList(self.htn_med_table.loc[:, 'Generic':], medsdf, columnToSearch='GenericName', columnToFlag='htnMed')
        self.medsdf = self.flagMedList(self.htn_med_table[self.htn_med_table['Class'] == 'Diuretics'].loc[:,'Generic':], self.medsdf, columnToSearch='GenericName', columnToFlag='diuretic')

        self.onDmMeds = self.medsdf['GenericName'].str.contains('metformin', case=False).any()
        self.onHTNMeds = any(self.medsdf['htnMed'])
        self.onDiuretics = any(self.medsdf['diuretic'])
        self.onStatin = self.medsdf['GenericName'].str.contains('statin', case=False).any()

        # SocHx
        self.isSmoker = False

        # Vitals + PEX
        self.vitdf = vitdf
        self.bmidf = bmidf
        self.bpdf = bpdf
        self.pt_bmi = self.bmidf['BMI (Body Mass Index)'].iloc[-1]
        self.curr_sbp = self.bpdf[self.bpdf.Date == self.bpdf.Date.max()]['Systolic BP'].iloc[0]
        self.curr_dbp = self.bpdf[self.bpdf.Date == self.bpdf.Date.max()]['Diastolic BP'].iloc[0]

        # Set Default BP Goals
        self.pt_sbp_goal = 120  # defaults that change if a dx of HTN is identified
        self.pt_dbp_goal = 80
        self.stage2 = False

        # Labs
        self.resdf = resdf

    # Takes in a target DataFrame and a masterSet (list or series or DF).
    # Column of 1's and 0's produced indicating presence in masterList.
    def flagMedList(self, masterSet, targetDF, columnToSearch, columnToFlag="Flag"):
        masterList = []
        if type(masterSet) == type(pd.DataFrame()) or type(masterSet) == type(pd.Series()):
            masterList = self.processFrameForSearch(masterSet)
        else:
            masterList = masterSet

        targetDF[columnToFlag] = targetDF[columnToSearch].apply(lambda x: x.lower() in masterList)
        return targetDF

    # Cleans up a dataframe/Series for ease of search, and returns as a List
    def processFrameForSearch(self, df):
        ret_list = []
        for col in df:  # Todo: This was written for a specific case, not sure if useful as written. Check again if recycling
            for element in df[col]:
                if not pd.isna(element):
                    if str(element).find('*') > -1:
                        ret_list.append(str(element).lower()[:str(element).find('*')])
                    else:
                        ret_list.append(str(element).lower())
        return ret_list

    def review_history(self):
        pass  # Todo

    def at_bp_goal(self):
        if self.curr_sbp < self.pt_sbp_goal and self.curr_dbp < self.pt_dbp_goal:
            return True
        else:
            # If BP > 20/10 over goal, consider Stage 2 Hypertension, or uncontrolled and requiring bigger changes
            if self.curr_sbp - self.pt_sbp_goal >= 20 or self.curr_dbp - self.pt_dbp_goal >= 10:
                self.stage2 = True
            return False

    def initiate_or_intensify(self):  # Todo: Is this all you want?
        if self.onHTNMeds:
            self.intensify_rx()
        else:
            self.initiate_rx()

    def intensify_rx(self):
        self.rec_List.append("Prior to intensifying therapy, ensure medication compliance.")

        # Todo: clean up the below logic, i don't think it's perfect yet
        # Todo: In the future can use asserts to ensure certain recommendations.
        if self.pt_race.__contains__('Black') or self.pt_race.__contains__('African'):
            self.rec_List.append("HTN in Black/African-American: Ensure a Thiazide or Calcium-Channel Blocker, optimize dosing, then consider adding another Thiazide/CCB/ACE-I/ARB")
        if self.hx_cvd:
            self.rec_List.append("HTN CVD: Ensure a first line CVD GDMT (BBlocker/ACEi/ARB), optimize dosing, then consider adding CCBs/Thiazides/MRAs")
        if self.hx_hf:
            self.rec_List.append("HTN in Heart Failure: Ensure Bblocker, an ACEi/ARB, and a Diuretic. After optimizing, consider adding MRA's.")
        if self.hx_hfpef:
            if not self.onDiuretics:
                self.rec_List.append("HTN in HFpEF w/o Diuretic: Recommend starting a Diuretic.")
            else:
                self.rec_List.append("HTN in HFpEF: Optimise dosing, then consider adding an ACEi/ARB and BetaBlocker.")
        if self.hx_ckd:
            self.rec_List.append("HTN in CKD: Consider ACEi/ARB to prevent kidney disease.")
        if self.hx_dm:
            self.rec_List.append("HTN in DM: Consider ACEi/ARB to prevent kidney disease.")
        elif self.stage2:
            self.rec_List.append("HTN w/ BP >20/10 above goal: Ensure 2 meds, optimize dosing, then consider adding another first line med (Thiazide/CCB/ACEi/ARB).")
        else:
            self.rec_List.append("HTN: Ensure first line medications (Thiazides, CCB, ACEi/ARB), optimize dosing, then consider adding another first line agent.")

    def initiate_rx(self):
        if not self.stage2:
            if (self.pt_race.__contains__('Black') or self.pt_race.__contains__('African')) and not (self.hx_cvd or self.hx_hf or self.hx_ckd):
                self.rec_List.append("Black/African-American: Start thiazide/CCB (can be overwritten by CVD, HF, CKD recs)")
                if self.pt_sbp_goal <= 130 or self.pt_dbp_goal == 80:
                    self.rec_List.append("For African Americans especially, 2 medications are recommended to reach a goal of 130/80.")
            if self.hx_cvd:
                self.rec_List.append("HTN in CVD: Ensure a Bblocker/ACEi/ARB as first med.")
            if self.hx_hf:
                self.rec_List.append("HTN in HF: Ensure Bblocker, ACEi/ARB and a Thiazide Diuretic, optimize dosing, then consider adding MRA's.")
            if self.hx_hfpef:
                self.rec_List.append("HTN in HFpEF: Optimize diuretics, then consider ACEi/ARB and BBlocker.")
            if self.hx_ckd:
                self.rec_List.append("HTN in CKD: Consider ACEi/ARB to prevent kidney disease.")
            if self.hx_dm:
                self.rec_List.append("HTN in DM: All first line agents are useful and effective (Thiazide/CCB/ACEi/ARB).")
        if self.stage2:
            self.rec_List.append("HTN w/ BP >20/10 above goal: Start two first line agents (Thiazide/CCB/ACEi/ARB).")

    def run_htn_logic(self):  # Two major branches --> Either yes or no HTN
        # Set any custom BP Goals
        if self.pt_age >= 65 or self.hx_cvd or self.hx_dm or self.hx_ckd:  # Todo: or ASCVD >= 10%
            self.pt_sbp_goal = 130
            self.pt_dbp_goal = 80
        if self.pt_age >= 65:
            self.rec_List.append("Pt is 65+: Consider a BP Goal of 130/80.")
        if self.hx_stktia:
            self.rec_List.append("Hx of Stroke/TIA: Consider a BP Goal of 130/80.")

        # No HTN and Diagnosis - Consider this block as a standalone thread
        if not self.hx_htn:
            if self.at_bp_goal():
                self.rec_List.append("Promote optimal lifestyle habits.")
                self.rec_List.append("BP at goal in pt w/o HTN: Recommend reassessment in 1 year.")
            elif self.curr_sbp < 130 and self.curr_dbp < 80:
                self.rec_List.append(
                    "Blood Pressure elevated - Recommend Non-Pharmacologic therapy. Recommend reassessment in 3-6 months.")
            elif self.curr_sbp < 140 and self.curr_dbp < 90:
                self.rec_List.append("Consider diagnosis of Stage 1 Hypertension. Recommend starting pharmacotherapy as well as lifestyle modification. Recommend reassessment in 1 month.")
            elif self.curr_sbp >= 140 or self.curr_dbp >= 90:
                self.rec_List.append("Consider diagnosis of Stage 2 Hypertension. Recommend starting pharmacotherapy as well as lifestyle modification. Recommend reassessment in 1 month.")

        # Yes HTN - Review HTN Status and Goals
        if self.hx_htn:
            if self.at_bp_goal():
                self.rec_List.append("Promote optimal lifestyle habits.")
                self.rec_List.append("BP at goal: Recommend reassessment in 1 year.")
            else:
                if self.curr_dbp < 90 and self.curr_sbp < 140:
                    if self.hx_cvd or self.hx_dm or self.hx_ckd:  # Todo: or ASCVD >= 10%:
                        self.rec_List.append("BP near goal in pt with CVD/DM/CKD: Recommend reassessment in 1 month.")
                    else:
                        self.rec_List.append("BP near goal: Recommend reassessment in 3-6 months.")

                elif self.curr_dbp >= 90 or self.curr_sbp >= 140:
                    self.rec_List.append("BP not at goal: Recommend reassessment in 1 month.")
                self.rec_List.append("BP not at goal: Recommend Non-Pharmacologic therapies in addition to others.")  # Todo: Improve this
                self.initiate_or_intensify()

        cardMaker.CardMaker(self)