import pandas as pd
from pandas.plotting import register_matplotlib_converters
register_matplotlib_converters()
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as plticker


# Matplotlib formatting
plt.rcParams.update({'font.size': 6})

# Reportlab Imports
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib.colors import red, blue, green, orange
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.pagesizes import landscape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Frame, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

#For SVG Importing into Reportlab
from io import BytesIO
from reportlab.graphics import renderPDF
from svglib.svglib import svg2rlg

# ReportLab Style Elements - Available Styles: BodyText, Bullet, Code, Definition, Heading1-6, Italic, Normal, OrderedList, Title, UnorderedList
styles = getSampleStyleSheet()
normStyle = styles['Normal']
h4Style = styles['Heading4']

# ReportLab Font Styles
dFontSize = 10
normStyle.fontSize = dFontSize
normStyle.fontName = "Helvetica"
normStyle.textColor = "Black"
normStyle.leading = dFontSize * 1.2  # Typically font size *120%


class CardMaker:

    def __init__(self, logic):
        self.logic = logic

        # Doc Set Up
        c = canvas.Canvas(self.logic.pt_name + '.pdf', pagesize=letter, bottomup=1) #bottomup = 1 is default

        # Start with basic patient identifiers
        title = c.beginText()
        title.setTextOrigin(0.5 * inch, 10.25 * inch)
        title.setFont("Helvetica-Bold", 16) #Top Line
        title.textLine(self.logic.pt_name +", " + str(self.logic.pt_age) + self.logic.pt_sex)

        c.drawText(title)

        # BP History Chart with Meds Changes
        #Frame Creation is (x1, y1, width, height)
        # BP Chart is at x1, y1, width, height = 0.5*inch, 7.25*inch, 7.5*inch, 2.9*inch
        # Prepping data to create graph
        self.logic.bpdf['Date'] = pd.to_datetime(self.logic.bpdf['Date'])
        self.logic.bpdf.sort_values('Date', inplace=True)
        sysBPList = self.logic.bpdf['Systolic BP']
        diaBPList = self.logic.bpdf['Diastolic BP']
        dateList = self.logic.bpdf['Date']

        # BP Chart Plotting
        fig = plt.figure(figsize=(6, 2.25), frameon=True)  # Start the figure plot capture

        plt.plot(dateList, sysBPList, 'ro-')
        plt.plot(dateList, diaBPList, 'bo-')
        plt.ylabel("Blood Pressure (mmHg)")
        plt.gca().set_ylim([min(diaBPList) - 20, max(sysBPList) + 20])
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
        loc = mdates.AutoDateLocator(minticks=3)
        plt.gca().xaxis.set_major_locator(loc)
        plt.gcf().autofmt_xdate()

        for x, y in zip(dateList, sysBPList):
            label = "{0:d}".format(y)
            plt.annotate(label, (x, y), textcoords="offset points", xytext=(0, 5), ha='center')

        for x, y in zip(dateList, diaBPList):
            label = "{0:d}".format(y)
            plt.annotate(label, (x, y), textcoords="offset points", xytext=(0, 5), ha='center')

        # By this point, image is generated, now gonna pour it into Bytes
        imgdata = BytesIO()
        fig.savefig(imgdata, format='svg')
        imgdata.seek(0)  # rewind the data
        drawing = svg2rlg(imgdata)
        renderPDF.draw(drawing, c, 0.5 * inch, 7.25 * inch, showBoundary=1)

        # Pertinent Demog + Fam + Soc
        subj_frame = Frame(0.5 * inch, 4.5 * inch, 1.75 * inch, 2.5 * inch, showBoundary=1)
        subj_frame.drawBoundary(c)
        subj_list = [Paragraph("Family and Social History", h4Style)]
        subj_list.append(Paragraph("\nNone Identified pertinent to guideline", normStyle))
        subj_frame.addFromList(subj_list, c) #Todo: Is this accurate? It looks like nothing is added right now

        #Identified comorbidities - just go one by one
        comorbid_frame = Frame(2.5 * inch, 4.5 * inch, 1.75 * inch, 2.5 * inch, showBoundary=1)
        comorbid_frame.drawBoundary(c)
        comorbid_list = [Paragraph("Identified Comorbidities", h4Style)]
        if self.logic.hx_htn: comorbid_list.append(Paragraph("Hypertension", normStyle))
        if self.logic.hx_ua: comorbid_list.append(Paragraph("Unstable Angina", normStyle))
        if self.logic.hx_sihd: comorbid_list.append(Paragraph("Stable Ischemic Heart Disease", normStyle))
        if self.logic.hx_mi: comorbid_list.append(Paragraph("Myocardial Infarction", normStyle))
        if self.logic.hx_stktia: comorbid_list.append(Paragraph("Stroke/TIA", normStyle))
        if self.logic.hx_cvd: comorbid_list.append(Paragraph("CVD", normStyle))
        if self.logic.hx_hf: comorbid_list.append(Paragraph("Heart Failure", normStyle))
        if self.logic.hx_hfpef: comorbid_list.append(Paragraph("HFpEF", normStyle))
        if self.logic.hx_dm: comorbid_list.append(Paragraph("Diabetes Mellitus", normStyle))
        if self.logic.hx_ckd: comorbid_list.append(Paragraph("CKD", normStyle))

        comorbid_frame.addFromList(comorbid_list, c)

        # New column: Current Antihypertensives
        curr_meds_frame = Frame(4.5 * inch, 4.5 * inch, 1.75 * inch, 2.5 * inch, showBoundary=1)
        curr_meds_frame.drawBoundary(c)
        curr_meds_list = [Paragraph("Current Antihypertensives", h4Style)]

        if logic.onHTNMeds:
            print("Yup, On em.")
            curr_meds_list.extend([Paragraph(x['GenericName'].lower() + " " + x['ProductStrength'], normStyle) for i, x in logic.medsdf[logic.medsdf['htnMed']].loc[:, ['GenericName', 'ProductStrength']].iterrows()])
        else:
            curr_meds_list.append(Paragraph("None", normStyle))

        curr_meds_frame.addFromList(curr_meds_list, c)

        #New Column: Current BP Goal + Today's BP and coloring
        curr_bp_frame = Frame(6.5 * inch, 4.5 * inch, 1.5 * inch, 2.5 * inch, showBoundary=1)
        curr_bp_frame.drawBoundary(c)
        curr_bp_list = [Paragraph("Current BP:", h4Style)]
        bp_string = str(logic.curr_sbp) + "/" + str(logic.curr_dbp)
        curr_bp_list.append(Paragraph(bp_string, normStyle))
        curr_bp_list.append(Paragraph("BP Goal:", h4Style))
        curr_bp_list.append(Paragraph(str(logic.pt_sbp_goal) + "/" + str(logic.pt_dbp_goal), normStyle))
        curr_bp_frame.addFromList(curr_bp_list, c)

        #Recs List
        recs_frame = Frame(0.5 * inch, 0.5 * inch, 7.5 * inch, 3.75 * inch, showBoundary=1)
        recs_frame.drawBoundary(c)
        recs_list = [Paragraph("Recommendations per Guideline: " + "2017 Hypertension Guidelines", h4Style)]
        for rec in logic.rec_List:
            recs_list.append(Paragraph(str(rec), normStyle))

        recs_list.append(Paragraph("All recommendations based on Level 1 Recommendations from the selected guideline.", normStyle))
        recs_frame.addFromList(recs_list, c)

        c.showPage()
        c.save()