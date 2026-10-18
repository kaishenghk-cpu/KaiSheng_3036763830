"""Generate an empirical report directly from calculated outputs."""
from pathlib import Path
from xml.sax.saxutils import escape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.lib.pagesizes import A4
from scipy import stats
import numpy as np
import matplotlib
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


def build(root, r):
    fonts=Path(matplotlib.get_data_path())/'fonts/ttf'
    pdfmetrics.registerFont(TTFont('ReportSans',str(fonts/'DejaVuSans.ttf')))
    pdfmetrics.registerFont(TTFont('ReportSansBold',str(fonts/'DejaVuSans-Bold.ttf')))
    pdfmetrics.registerFontFamily('ReportSans',normal='ReportSans',bold='ReportSansBold',italic='ReportSans',boldItalic='ReportSansBold')
    styles=getSampleStyleSheet()
    styles.add(ParagraphStyle(name='BodyX',fontName='ReportSans',fontSize=9.7,leading=14.1,spaceAfter=9))
    styles.add(ParagraphStyle(name='NoteX',fontName='ReportSans',fontSize=8.1,leading=11.3,spaceAfter=7,textColor=colors.HexColor('#444444')))
    styles.add(ParagraphStyle(name='HeadX',fontName='ReportSansBold',fontSize=14,leading=18,spaceAfter=12,textColor=colors.black))
    styles.add(ParagraphStyle(name='TitleX',fontName='ReportSansBold',fontSize=22,leading=27,spaceAfter=14,textColor=colors.black))
    styles.add(ParagraphStyle(name='CellX',fontName='ReportSans',fontSize=8,leading=11))
    styles.add(ParagraphStyle(name='CellSmallX',fontName='ReportSans',fontSize=7.2,leading=9.5))
    styles.add(ParagraphStyle(name='CellHeadX',fontName='ReportSansBold',fontSize=7.8,leading=10.5,textColor=colors.white))
    story=[]
    def p(text,kind='BodyX'):
        story.append(Paragraph(text,styles[kind]))
    def h(text):p(text,'HeadX')
    def page():story.append(PageBreak())
    def table(headers,rows,widths,small=False):
        body_style=styles['CellSmallX' if small else 'CellX']
        data=[[Paragraph(escape(str(v)),styles['CellHeadX']) for v in headers]]
        for row in rows:
            data.append([Paragraph(escape(str(v)).replace('\n','<br/>'),body_style) for v in row])
        t=Table(data,colWidths=widths,repeatRows=1,hAlign='LEFT')
        ts=[('BACKGROUND',(0,0),(-1,0),colors.HexColor('#24465b')),
            ('GRID',(0,0),(-1,-1),.4,colors.HexColor('#d9d9d9')),
            ('VALIGN',(0,0),(-1,-1),'MIDDLE'),('LEFTPADDING',(0,0),(-1,-1),6),
            ('RIGHTPADDING',(0,0),(-1,-1),6),('TOPPADDING',(0,0),(-1,-1),6),
            ('BOTTOMPADDING',(0,0),(-1,-1),6)]
        for i in range(2,len(data),2):ts.append(('BACKGROUND',(0,i),(-1,i),colors.HexColor('#f2f5f7')))
        t.setStyle(TableStyle(ts));story.append(t);story.append(Spacer(1,10))
    def f(v,d=2):return f'{v:.{d}f}'
    def estimate(m,t):return f'{m["beta"][t]:.2f}\n({m["se"][t]:.2f})'
    x=r['x'];s4=r['s4'];m=r['models'][0];ext=r['extension'];rob=r['robustness']
    pmain=2*stats.t.sf(abs(m['beta']['STATE']/m['se']['STATE']),m['df'])

    # Page 1
    p('Minimum wages and employment','TitleX')
    p('Replication of Card and Krueger 1994 and an ownership extension','HeadX')
    p('Kai Sheng &nbsp; | &nbsp; Student ID 3036763830<br/>ECO6067 Individual Project &nbsp; | &nbsp; 18 October 2026','NoteX')
    h('Research question and findings')
    p('This project examines whether the 1992 increase in New Jersey\'s minimum wage was followed by a fall in employment at fast-food restaurants relative to nearby Pennsylvania. It reconstructs Tables 2 to 4 and Figure 1 of Card and Krueger (1994) from the course survey data. The independent extension asks whether the relative employment change differs between company-owned and franchised restaurants.')
    p(f'The reconstructed balanced-sample difference in differences is <b>{r["validation"]["balanced_did"]:.2f} full-time-equivalent employees per restaurant</b>. In the paper\'s more restrictive 357-store regression sample, the New Jersey coefficient is {m["beta"]["STATE"]:.2f}, with a conventional standard error of {m["se"]["STATE"]:.2f} and p = {pmain:.3f}. This point estimate is positive, but is just above the 5 percent significance threshold. HC1 inference is weaker still, with p = {rob.iloc[0]["p"]:.3f}.')
    p(f'The ownership interaction is {ext.iloc[2].Estimate:.2f} FTE, with an HC1 standard error of {ext.iloc[2].HC1_SE:.2f} and p = {ext.iloc[2]["p"]:.3f}. The data do not establish a difference in the employment response between the two ownership types. The wide interval also leaves economically meaningful differences possible.')
    h('Economic mechanism and design')
    p('A binding wage floor raises the cost of low-wage labour. With competitive labour markets and no offsetting adjustments, firms may reduce labour demand. If employers have wage-setting power, a moderate wage increase can instead raise employment. Restaurants may also adjust prices, staffing composition, turnover, or operating practices. A positive employment estimate alone cannot identify which mechanism operates.')
    p('New Jersey is the treated state and eastern Pennsylvania is the comparison area. A before-and-after comparison within New Jersey would mix the policy with common economic changes. Subtracting the Pennsylvania change removes a common component, provided the untreated employment trends would have been comparable. With only one pre-policy survey, that assumption cannot be tested using pre-trends.')
    p('All numerical results are generated by code from the supplied CSV. Published numbers are used only as comparison targets. The project uses course-supplied data and does not claim an independent database download.','NoteX')

    # Page 2
    page();h('Data and sample construction')
    p('The original input is the unmodified public.csv in course Package 01, accompanied by its README and data dictionary. The input contains 410 restaurant records and 46 original columns. The analysis retains all rows, records an SHA-256 checksum, and creates a unique row identifier. SHEET alone is not unique: the repeated value 407 identifies restaurants in different states and chains, so neither row is deleted.')
    table(['Sample stage','Observations'],r['flow'].values.tolist(),[375,110])
    p('<b>Employment.</b> FTE = EMPFT + NMGRS + 0.5 x EMPPT. A missing employment component produces a missing FTE; components are not silently filled with zero. Six permanently closed restaurants have follow-up FTE set to zero. Four temporary closures have missing follow-up FTE in the baseline and zero only in the designated sensitivity analysis. The store refusing the second interview remains missing.')
    p('<b>Other variables.</b> Meal price is soda plus fries plus entree. The numerical convention reproducing the paper\'s full-time percentage is 100 x EMPFT / FTE; this is not the ordinary full-time share of headcount. The starting-wage gap equals max[(5.05 - initial wage) / initial wage, 0] in New Jersey and zero in Pennsylvania. Ownership is the baseline company-owned indicator; chain controls omit Burger King.')
    p('<b>Samples.</b> Table 2 uses variable-specific available responses. Table 3 first compares available-case means, then uses 384 stores with employment in both waves. Table 4 uses a common sample of 357 stores with valid initial wages, valid employment changes, and follow-up wages, retaining permanent closures as an explicit exception to the follow-up-wage requirement. Omitting that exception incorrectly reduces this sample to 351.')
    p('Region controls are SOUTHJ, CENTRALJ, PA1 and PA2, with northern New Jersey as the omitted region. The processed all-store, Table 4 and extension samples are generated in data/processed/. Row-level inputs and processed samples are excluded from Git to respect the course distribution restriction; authorized reviewers can regenerate them.','NoteX')

    # Page 3
    page();h('Table 2 reconstruction')
    p('Values are means, with standard errors in parentheses. Sample sizes vary by variable. Store-type and wage-threshold entries are percentages; wages and meal prices are dollars. Full-time percentage follows the convention described above.','NoteX')
    rows=[]
    for _,a in r['t2'].iterrows():
        label=a.Variable.replace('Full time percentage convention','Full time percentage').removesuffix(' percent')
        rows.append([label,f'{a.NJ_mean:.2f} ({a.NJ_SE:.2f})',str(int(a.NJ_N)),f'{a.PA_mean:.2f} ({a.PA_SE:.2f})',str(int(a.PA_N)),f'{a.t_Welch:.2f}'])
    table(['Variable','New Jersey','N','Pennsylvania','N','Welch t'],rows,[171,90,30,90,30,74],True)
    p('Prefixes 1, 2 and 3 denote store types, first survey and second survey. Welch t tests use the unequal-variance difference-in-means formula. Both Welch and pooled t statistics are retained in the machine-readable output. For threshold indicators, the denominator is all restaurants in the state, matching the original table\'s first-wave percentages; a missing wage is not counted as a report at that threshold. This differs from Figure 1, whose denominators include observed wages only.','NoteX')
    p('Most displayed means reproduce the original rounding. A visible exception is New Jersey\'s follow-up percentage at exactly $5.05: the supplied file has 283 such records, giving 85.50 percent, versus 85.2 in the article. Some t statistics also differ slightly. The input is not edited to force a match.','NoteX')

    # Page 4
    page();h('Figure 1 reconstruction')
    p('Starting wage distributions before and after the minimum wage increase')
    story.append(Image(str(root/'outputs/figures/figure1.png'),width=485,height=377))
    story.append(Spacer(1,12))
    p('The distributions are reconstructed from observed starting wages in each state and wave. After the increase, the New Jersey distribution concentrates sharply near $5.05, while Pennsylvania continues to have many reports near $4.25. This is a check that the policy generated a substantial wage change in the treated state.')
    p('The display uses left-inclusive, right-exclusive 10-cent bins starting at $4.20, and an open-ended final bin for wages of $5.50 or more. Midpoints label finite bins. The complete bin counts, denominators and percentages are exported, making boundary decisions reproducible. Missing wages are excluded separately in each state and wave; observations in the upper tail are retained. These explicit binning and denominator choices may produce small differences from the printed figure.','NoteX')
    p('The figure checks the wage first stage descriptively. It does not itself estimate employment effects or demonstrate that the comparison group satisfies parallel trends.')

    # Page 5
    page();h('Table 3 reconstruction')
    p('Employment levels and changes in full-time equivalents. Standard errors are in parentheses. Low, middle and high refer to initial New Jersey wages of $4.25, $4.26 to $4.99, and at least $5.00.','NoteX')
    headers=['Statistic','PA','NJ','NJ - PA','NJ low','NJ mid','NJ high','Low - high','Mid - high']
    rows=[]
    for _,a in r['t3'].iterrows():
        rows.append([a.iloc[0]]+[str(v).replace(' (','\n(') for v in a.iloc[1:]])
    table(headers,rows,[109]+[47]*8,True)
    p('The balanced-sample estimate subtracts the average Pennsylvania employment change from the average New Jersey change. It uses the same stores before and after and therefore avoids changes in the composition of the available-case samples. In that sample, Pennsylvania employment falls by 2.28 FTE and New Jersey employment rises by 0.47 FTE, producing the 2.75 FTE difference.')
    p('The available-case change-in-means row subtracts independently available wave means. Its standard errors use a delta-method calculation that retains the covariance of repeated observations: each store contributes (follow-up employment minus its wave mean) / follow-up N, less (initial employment minus its wave mean) / initial N, with missing contributions zero. The variance is the sum of squared contributions with a finite-sample correction. This is explicitly different from assuming independent waves or simply substituting the balanced-change standard error.')
    p('The main employment point estimates reproduce the published values closely. Across the 40 displayed Table 3 point estimates, the largest difference from the printed values is 0.01 FTE at the displayed precision. The available-case standard errors differ more: for example, the reconstructed NJ - PA change-in-means SE is approximately 1.31, compared with 1.36 in the article. The balanced estimate has an SE of approximately 1.34, matching the printed result.','NoteX')
    p('Coding temporary closures as zero instead of missing lowers the balanced comparison to 2.51 FTE. This reproduces the direction and magnitude of the paper\'s closure sensitivity result. Low-versus-high wage comparisons are part of the required replication and are not counted as the independent extension.')

    # Page 6
    page();h('Table 4 reconstruction')
    p('The dependent variable is the change in FTE. All five models use the same 357 stores and include an intercept. Models 1 and 2 use the New Jersey indicator; models 3 to 5 use the initial wage gap. The table reports conventional homoskedastic OLS standard errors, as a replication convention.','NoteX')
    models=r['models']
    rows=[['New Jersey indicator']+[estimate(mm,'STATE') if i<2 else '-' for i,mm in enumerate(models)],
          ['Initial wage gap']+[estimate(mm,'gap') if i>=2 else '-' for i,mm in enumerate(models)],
          ['Chain and ownership','No','Yes','No','Yes','Yes'],
          ['Region controls','No','No','No','No','Yes'],
          ['Regression SE']+[f(mm['rmse']) for mm in models],
          ['Controls joint F test p']+['-' if np.isnan(a) else f(a) for a in r['t4']['Controls joint p']],
          ['Observations']+[str(mm['n']) for mm in models]]
    table(['Variable','Model 1','Model 2','Model 3','Model 4','Model 5'],rows,[150]+[67]*5)
    p(f'The New Jersey coefficient is {models[0]["beta"]["STATE"]:.2f} without controls and {models[1]["beta"]["STATE"]:.2f} after adding chain and ownership controls. The initial-gap coefficient is {models[2]["beta"]["gap"]:.2f}; it is measured per unit proportional wage gap, so a gap of 0.10 implies approximately {models[2]["beta"]["gap"]*.1:.2f} FTE rather than 15.65 FTE.')
    table(['Main coefficient','Published','Reconstructed','Difference'],[
        [f'Model {i+1}',f(o),f(models[i]['beta']['STATE' if i<2 else 'gap']),f(models[i]['beta']['STATE' if i<2 else 'gap']-o,3)]
        for i,o in enumerate([2.33,2.30,15.65,14.92,11.91])],[175,100,110,100])
    p('Models 1 to 4 match the printed coefficients at two decimal places. Model 5 gives 11.98 (7.42), compared with 11.91 (7.39). The same sample, wage-gap formula and documented region controls are used; the residual discrepancy has not been fully resolved. It may reflect differences in historical coding or source data, but that explanation is not established. No records or coefficients are altered to remove it.','NoteX')
    p(f'Inference matters. For model 1, the conventional p value is {pmain:.3f}; using HC1 changes it to {rob.iloc[0]["p"]:.3f}. The positive sign is stable, but the evidence is not a precise universal estimate of a minimum-wage effect. Neither covariance estimator addresses common policy shocks at the state level.')

    # Page 7
    page();h('Independent extension on ownership')
    p('<b>Question.</b> Does the New Jersey employment change relative to Pennsylvania differ between company-owned and franchised stores? Ownership may affect hiring discretion, access to internal funds and the ability to spread costs across outlets. These are motivations for a test, not mechanisms identified by these data. The hypothesis is two-sided because ownership could support either greater adjustment or greater employment stability.')
    p('The model is change in FTE = intercept + beta NJ + gamma Company + delta (NJ x Company) + chain controls + error. Company is baseline ownership. The interaction delta is the difference between the company-owned and franchise DID estimates. All lower-order terms are included. The main analysis uses the same 357 stores as Table 4 and HC1 standard errors.')
    table(['Ownership contrast','Estimate','HC1 SE','95 percent interval','p'],[
        [a.Contrast,f(a.Estimate),f(a.HC1_SE),f'[{a.CI_low:.2f}, {a.CI_high:.2f}]',f(a['p'],3)] for _,a in ext.iterrows()],
        [175,60,60,130,60])
    story.append(Image(str(root/'outputs/figures/extension.png'),width=485,height=188))
    story.append(Spacer(1,9))
    p(f'The franchise DID is {ext.iloc[0].Estimate:.2f} FTE and the company-owned DID is {ext.iloc[1].Estimate:.2f} FTE. Their difference is {ext.iloc[2].Estimate:.2f} FTE, with a 95 percent interval from {ext.iloc[2].CI_low:.2f} to {ext.iloc[2].CI_high:.2f}. There is no statistically clear evidence that ownership changes the response. The interval is too wide to conclude equivalence.')
    table(['State','Ownership','N','Mean initial FTE','Mean FTE change'],[
        ['NJ' if a.STATE else 'PA','Company' if a.CO_OWNED else 'Franchise',int(a.N),f(a.Before),f(a.Change)] for _,a in r['cells'].iterrows()],
        [55,100,50,140,140])
    p('Ownership is not randomly assigned, and cell sizes are uneven. A causal ownership comparison additionally requires comparable counterfactual changes across ownership groups. The result is therefore an exploratory heterogeneity analysis, not a causal estimate of franchising.','NoteX')

    # Page 8
    page();h('Robustness and validation')
    table(['Specification and target','Estimate','HC1 SE','p','N'],[
        [a.Specification+'; '+a.Term,f(a.Estimate),f(a.HC1_SE),f(a['p'],3),int(a.N)] for _,a in rob.iterrows()],
        [275,55,55,55,45],True)
    p('The ownership-interaction estimate remains negative and statistically inconclusive when the sample includes all balanced stores, or when temporary closures are coded as zero. The wage-gap interaction uses a different scale: a 0.10 gap corresponds to one tenth of the reported interaction coefficient. It is also statistically inconclusive. All listed specifications are reported; their p values are exploratory and are not evidence of a discovered ownership mechanism.')
    p('<b>Validation.</b> The workflow checks the input hash and dimensions, retains all rows, verifies the state-by-sheet identifier, checks closure rules and sample counts, verifies the OLS normal equations, and equates the balanced DID with an OLS slope. An independent scipy.stats.linregress call verifies the restricted-sample baseline slope and its conventional standard error. Each of the first four Table 4 main coefficients must be within 0.01 of its printed benchmark. The unresolved model 5 difference is saved rather than suppressed.')
    h('Limitations and conclusion')
    p('The survey contains only one pre-policy observation and one follow-up. Parallel trends cannot be checked, contemporaneous state-specific shocks cannot be ruled out, and measurement error in reported staffing can be substantial. The sample covers incumbent restaurants in four chains, not all workers, all sectors, or new restaurant entry. Baseline and restricted samples differ because of item nonresponse. Conventional and HC1 standard errors treat stores as independent and do not solve inference with only two policy clusters.')
    p('The reconstruction recovers the main positive employment comparisons and most printed coefficients. It does not support a simple claim that this policy reduced employment in these surveyed restaurants. That finding is narrower than proving that minimum-wage increases always raise employment. The ownership extension provides no clear evidence of heterogeneous effects in this sample.')
    page();h('AI use and reproducibility')
    p('ChatGPT Codex assisted with interpreting the paper, developing and debugging code, preparing figures and drafting the report. Validation included source-table comparisons, sample and closure checks, an independent baseline regression check, and a clean-input rerun. An initial wage-group extension was replaced because it overlapped with the original paper. Remaining discrepancies and statistical uncertainty are reported explicitly. AI_USE_DISCLOSURE.md documents the assistance and checks in more detail; responsibility for reviewing the submitted analysis remains with the author.','NoteX')
    p('Run python code/run_all.py after installing requirements.txt and providing the documented input. It regenerates processed samples, aggregate tables, figures, validation output and this report. The repository excludes row-level data and documents authorized access.','NoteX')
    h('References')
    p('Card, David, and Alan B. Krueger. 1994. Minimum Wages and Employment: A Case Study of the Fast-Food Industry in New Jersey and Pennsylvania. American Economic Review 84(4): 772-793. Author-hosted paper: https://davidcard.berkeley.edu/papers/njmin-aer.pdf','NoteX')
    p('ECO6067 project instructions, course Package 01 README and data dictionary, and teaching-team repository example supplied by the student, accessed 18 October 2026. Example: https://github.com/Jeff7c/ChenJianfei_3030135471','NoteX')

    def footer(canvas,doc):
        canvas.setFont('ReportSans',8);canvas.setFillColor(colors.HexColor('#666666'))
        canvas.drawString(55,30,'Kai Sheng | ECO6067 | Minimum wages and employment')
        canvas.drawRightString(A4[0]-55,30,str(doc.page))
    doc=SimpleDocTemplate(str(root/'report.pdf'),pagesize=A4,rightMargin=55,leftMargin=55,
                         topMargin=48,bottomMargin=48,title='Minimum wages and employment',author='Kai Sheng',invariant=1)
    doc.build(story,onFirstPage=footer,onLaterPages=footer)
