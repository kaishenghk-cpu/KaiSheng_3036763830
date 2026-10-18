"""Build a short report from the calculated replication results."""
from pathlib import Path
from xml.sax.saxutils import escape
import numpy as np
import matplotlib
from scipy import stats
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


def build(root, r):
    fonts=Path(matplotlib.get_data_path())/'fonts/ttf'
    pdfmetrics.registerFont(TTFont('Plain',str(fonts/'DejaVuSans.ttf')))
    pdfmetrics.registerFont(TTFont('PlainBold',str(fonts/'DejaVuSans-Bold.ttf')))
    pdfmetrics.registerFontFamily('Plain',normal='Plain',bold='PlainBold',italic='Plain',boldItalic='PlainBold')
    styles=getSampleStyleSheet()
    for name,font,size,lead in [('BodyX','Plain',10,14),('NoteX','Plain',8.1,11),('HeadX','PlainBold',12,16),('TitleX','PlainBold',17,21),('CellX','Plain',8,10.5),('SmallX','Plain',7.2,9.5),('HeaderX','PlainBold',7.8,10)]:
        styles.add(ParagraphStyle(name=name,fontName=font,fontSize=size,leading=lead,spaceAfter=7 if name in ['BodyX','NoteX','HeadX'] else 0,textColor=colors.black))
    story=[]
    def p(t,style='BodyX'):story.append(Paragraph(t,styles[style]))
    def h(t):p(t,'HeadX')
    def page():story.append(PageBreak())
    def tab(headers,rows,widths,small=False):
        data=[[Paragraph(escape(str(v)),styles['HeaderX']) for v in headers]]
        for row in rows:
            data.append([Paragraph(escape(str(v)).replace('\n','<br/>'),styles['SmallX' if small else 'CellX']) for v in row])
        t=Table(data,colWidths=widths,repeatRows=1,hAlign='LEFT')
        t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#eeeeee')),('GRID',(0,0),(-1,-1),.4,colors.HexColor('#cccccc')),('VALIGN',(0,0),(-1,-1),'MIDDLE'),('LEFTPADDING',(0,0),(-1,-1),5),('RIGHTPADDING',(0,0),(-1,-1),5),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5)]))
        story.append(t);story.append(Spacer(1,8))
    def f(v,d=2):return f'{v:.{d}f}'
    models=r['models'];ext=r['extension'];rob=r['robustness'];m=models[0]
    pmain=2*stats.t.sf(abs(m['beta']['STATE']/m['se']['STATE']),m['df'])

    # Page 1: short introduction and method.
    p('Minimum wages and employment','TitleX');story.append(Spacer(1,8))
    p('Kai Sheng | 3036763830 | ECO6067 | 18 October 2026','NoteX')
    h('1 Research question')
    p('This project replicates Tables 2 to 4 and Figure 1 of Card and Krueger (1994). It asks whether the increase in New Jersey\'s minimum wage from $4.25 to $5.05 in April 1992 reduced employment at fast-food restaurants. Pennsylvania, where the minimum wage stayed at $4.25, is the comparison group.')
    p('A higher minimum wage raises labour costs, so firms may hire fewer workers. However, the effect may differ when employers have wage-setting power or adjust prices and staffing in other ways. The data are used to examine the employment response rather than assume its direction.')
    h('2 Data and variables')
    p('The data are public.csv from course Package 01. They cover 410 restaurants in four chains, surveyed before and after the policy. The main sample counts are shown below.')
    tab(['Sample','Restaurants'],[['All restaurants',410],['New Jersey',331],['Pennsylvania',79],['Employment observed in both waves',384],['Table 4 and main extension sample',357]],[365,120])
    p('Full-time-equivalent employment (FTE) equals full-time employees plus managers plus half the number of part-time employees. Missing components are kept missing. Follow-up FTE is zero for six permanent closures. Four temporary closures are missing in the baseline and zero in a sensitivity check.')
    p('Table 4 requires employment and wage data in both waves, with an exception for permanent closures, whose follow-up employment is zero. All models use the same 357 stores. Different sample rules explain why its estimate differs from the 384-store comparison.')
    p('Meal price is the sum of soda, fries and entree prices. The full-time percentage in Table 2 follows the numerical convention 100 x EMPFT / FTE, rather than an ordinary headcount share. Initial wage gap is max[(5.05 - initial wage) / initial wage, 0] in New Jersey and zero in Pennsylvania.','NoteX')
    h('3 Method')
    p('The difference-in-differences (DID) estimate is the employment change in New Jersey minus the change in Pennsylvania. Its causal interpretation assumes the two groups would have had similar employment trends without the policy. There is only one pre-policy survey, so this assumption cannot be checked with pre-trends.')
    p('Table 4 regresses the change in FTE on the New Jersey indicator or the initial wage gap, adding chain, ownership and region controls as specified in the paper. Standard errors in the replication table use the conventional OLS formula. HC1 robust standard errors are also checked.')

    # Page 2: full Table 2, without unnecessary duplicate sample-size columns.
    page();h('4 Replication results')
    p('Table 2 Means of key variables','HeadX')
    rows=[]
    for _,a in r['t2'].iterrows():
        label=a.Variable.replace('Full time percentage convention','Full time percentage').removesuffix(' percent')
        rows.append([label,f'{a.NJ_mean:.2f} ({a.NJ_SE:.2f})',f'{a.PA_mean:.2f} ({a.PA_SE:.2f})',f(a.t_Welch)])
    tab(['Variable','New Jersey','Pennsylvania','t statistic'],rows,[215,100,100,70],True)
    p('Standard errors are in parentheses. Prefix 1 refers to store types, 2 to the first survey and 3 to the second survey. Store types, wage thresholds and recruiting bonuses are percentages. Wages and meal prices are dollars. Sample sizes vary by variable and are listed in outputs/tables/table2.csv. The t statistics use unequal-variance standard errors.','NoteX')
    p('Average starting wages rose from $4.61 to $5.08 in New Jersey, while Pennsylvania wages changed little. Average FTE rose slightly in New Jersey and fell in Pennsylvania.')
    p('Most means are close to the original table. One difference is the follow-up New Jersey share at exactly $5.05: the supplied file gives 85.50 percent, compared with 85.2 in the paper. Wage-threshold percentages use all state records as the denominator; missing wages are not counted at the threshold. The data are not changed to force a match.','NoteX')

    # Page 3: the required wage figure and complete eight-column Table 3.
    page();h('Figure 1 Starting wage distributions')
    story.append(Image(str(root/'outputs/figures/figure1.png'),width=425,height=330))
    p('After the policy, New Jersey wages are concentrated near $5.05. The figure excludes missing wages, uses 10-cent intervals from $4.20, and groups wages of $5.50 or more together. Small differences from the original graph can follow from these bin choices.','NoteX')
    h('Table 3 Employment before and after the policy')
    tab(['Statistic','PA','NJ','NJ - PA','NJ low','NJ mid','NJ high','Low - high','Mid - high'],
        [[a.iloc[0]]+[str(v).replace(' (','\n(') for v in a.iloc[1:]] for _,a in r['t3'].iterrows()],[109]+[47]*8,True)
    p('FTE units; standard errors in parentheses. Low, middle and high refer to initial NJ wages of $4.25, $4.26 to $4.99, and at least $5.00. The available-case change-in-means SE retains within-store covariance; its NJ - PA value is 1.31 versus 1.36 in the original. The balanced-sample SE is 1.34.','NoteX')
    p(f'In the balanced sample, New Jersey employment increases by 0.47 FTE and Pennsylvania employment falls by 2.28 FTE. The DID is therefore {r["validation"]["balanced_did"]:.2f} FTE. Treating temporary closures as zero lowers it to 2.51. Table 3 point estimates differ from the printed values by no more than 0.01 at the displayed precision.')

    # Page 4: keep all five regression models and a short interpretation.
    page();h('Table 4 Models for the change in employment')
    def est(mm,t):return f'{mm["beta"][t]:.2f}\n({mm["se"][t]:.2f})'
    rows=[['New Jersey indicator']+[est(mm,'STATE') if i<2 else '-' for i,mm in enumerate(models)],
          ['Initial wage gap']+[est(mm,'gap') if i>=2 else '-' for i,mm in enumerate(models)],
          ['Chain and ownership','No','Yes','No','Yes','Yes'],
          ['Region controls','No','No','No','No','Yes'],
          ['Regression SE']+[f(mm['rmse']) for mm in models],
          ['Controls joint F test p']+['-' if np.isnan(a) else f(a) for a in r['t4']['Controls joint p']],
          ['Observations']+[str(mm['n']) for mm in models]]
    tab(['Variable','Model 1','Model 2','Model 3','Model 4','Model 5'],rows,[150]+[67]*5)
    p('The dependent variable is the change in FTE. All models include an intercept. Chain controls omit Burger King. Region controls are SOUTHJ, CENTRALJ, PA1 and PA2, with northern New Jersey omitted. Conventional OLS standard errors are in parentheses.','NoteX')
    p('The estimated NJ effect is 2.33 FTE without controls and 2.30 with chain and ownership controls. The wage-gap coefficient in model 3 is 15.65. For a gap of 0.10, this corresponds to about 1.57 FTE, not 15.65 FTE.')
    tab(['Main coefficient','Original paper','This project'],[[f'Model {i+1}',f(o),f(models[i]['beta']['STATE' if i<2 else 'gap'])] for i,o in enumerate([2.33,2.30,15.65,14.92,11.91])],[215,135,135])
    p('The first four coefficients match the original table at two decimal places. Model 5 gives 11.98 (7.42), compared with 11.91 (7.39). The remaining difference is not fully explained, and no observations are changed to remove it.')
    p(f'The model 1 p value is {pmain:.3f} with conventional standard errors and {rob.iloc[0]["p"]:.3f} with HC1 errors. The estimate is positive, but it is not significant at the 5 percent level under either method. The sign should therefore be distinguished from the strength of the evidence.')
    h('Checks')
    p('The code checks the original file checksum, sample counts and closure rules. It keeps both restaurants with SHEET number 407 because they are in different states. It also checks that the DID equals the corresponding OLS slope and verifies the baseline slope and standard error using SciPy. A run from a separate clean-input folder reproduces the same output files.')

    # Page 5: one clear extension, brief limitations and disclosure.
    page();h('5 Extension on company ownership')
    p('The extension asks whether company-owned and franchised restaurants respond differently. Company-owned stores may have different hiring decisions or access to funding. I test this by adding NJ x Company to a model with the NJ indicator, company ownership and chain controls. The interaction is the difference between the two ownership groups\' DID estimates.')
    tab(['Comparison','Estimate','HC1 SE','95 percent interval','p'],[[a.Contrast,f(a.Estimate),f(a.HC1_SE),f'[{a.CI_low:.2f}, {a.CI_high:.2f}]',f(a['p'],3)] for _,a in ext.iterrows()],[175,60,60,130,60])
    p(f'The franchise DID is {ext.iloc[0].Estimate:.2f} and the company-owned DID is {ext.iloc[1].Estimate:.2f}. Their difference is {ext.iloc[2].Estimate:.2f} FTE, with p = {ext.iloc[2]["p"]:.3f}. There is no clear evidence of a difference. The interval is wide, so this does not show that the effects are equal.')
    p('The ownership interaction remains negative and insignificant when using all 384 balanced stores or treating temporary closures as zero. A wage-gap interaction is also insignificant. Full sensitivity estimates are in outputs/tables/robustness.csv. Ownership is not randomly assigned, so the extension is exploratory.')
    h('6 Limitations and conclusion')
    p('The data have only two survey waves and may contain reporting errors. State-specific shocks could affect the DID, and store-level standard errors do not resolve policy inference with only two states. The sample covers existing restaurants in four chains, so the findings should not be applied to every industry or to new store entry.')
    p('The project recovers the main positive employment comparisons in the paper. It does not provide clear evidence that this policy reduced employment in the surveyed restaurants. The ownership extension is inconclusive. These results do not establish that minimum-wage increases always raise employment.')
    h('AI use and reproduction')
    p('ChatGPT Codex assisted with interpreting the paper, developing and debugging code, preparing figures and drafting the report. Checks included source-table comparisons, sample checks, an independent baseline regression and a clean-input rerun. The full record is in AI_USE_DISCLOSURE.md. Responsibility for reviewing the submitted work remains with the author.','NoteX')
    p('After providing the documented data, install requirements.txt and run python code/run_all.py. This regenerates all tables, figures, processed samples and this report. Row-level data are supplied separately to the teaching team rather than published in the repository.','NoteX')
    h('References')
    p('Card, D., and A. B. Krueger (1994). Minimum Wages and Employment: A Case Study of the Fast-Food Industry in New Jersey and Pennsylvania. American Economic Review, 84(4), 772-793. https://davidcard.berkeley.edu/papers/njmin-aer.pdf','NoteX')
    p('ECO6067 project instructions, Package 01 README and data dictionary, and the teaching-team repository example. Accessed 18 October 2026.','NoteX')
    def footer(canvas,doc):
        canvas.setFont('Plain',8);canvas.setFillColor(colors.HexColor('#555555'))
        canvas.drawRightString(A4[0]-55,28,str(doc.page))
    doc=SimpleDocTemplate(str(root/'report.pdf'),pagesize=A4,rightMargin=55,leftMargin=55,topMargin=45,bottomMargin=45,title='Minimum wages and employment',author='Kai Sheng',invariant=1)
    doc.build(story,onFirstPage=footer,onLaterPages=footer)
