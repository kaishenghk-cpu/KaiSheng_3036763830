"""Reconstruct Card and Krueger (1994) from unmodified restaurant survey rows.

Published values below are comparison targets only. All estimates are computed
from the CSV. NumPy least squares and explicit covariance formulas avoid an
additional regression dependency; validation cross-checks the baseline slope.
"""
from pathlib import Path
import hashlib
import json
import platform
import importlib.metadata
import numpy as np
import pandas as pd
from scipy import stats
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

CONTROL = ['KFC', 'ROY', 'WENDYS', 'CO_OWNED']
REGION = ['SOUTHJ', 'CENTRALJ', 'PA1', 'PA2']


def ols(df, outcome, terms, robust=False):
    s = df.dropna(subset=[outcome] + terms)
    X = np.column_stack([np.ones(len(s)), s[terms].to_numpy(float)])
    y = s[outcome].to_numpy(float)
    n, k = X.shape
    if np.linalg.matrix_rank(X) != k:
        raise ValueError('Rank deficient design')
    b = np.linalg.lstsq(X, y, rcond=None)[0]
    e = y - X @ b
    bread = np.linalg.inv(X.T @ X)
    cov = bread * (e @ e / (n-k))
    if robust:
        cov = (n/(n-k)) * bread @ (X.T @ (X * e[:, None]**2)) @ bread
    se = np.sqrt(np.diag(cov))
    names = ['constant'] + terms
    return dict(n=n, k=k, df=n-k, beta=dict(zip(names, b)),
                se=dict(zip(names, se)), cov=cov, terms=names,
                residual=e, sse=float(e@e), rmse=float(np.sqrt(e@e/(n-k))),
                sample=s, robust=robust)


def contrast(model, weights):
    v = np.array([weights.get(t, 0) for t in model['terms']])
    b = float(sum(weights.get(t, 0)*model['beta'][t] for t in model['terms']))
    se = float(np.sqrt(v @ model['cov'] @ v))
    p = float(2*stats.t.sf(abs(b/se), model['df']))
    q = stats.t.ppf(.975, model['df'])
    return dict(estimate=b, se=se, p=p, low=b-q*se, high=b+q*se, n=model['n'])


def mean_se(x):
    x = pd.Series(x).dropna()
    return (float(x.mean()), float(x.sem()), len(x))


def fmt(b, se=None, digits=2):
    return f'{b:.{digits}f}' if se is None else f'{b:.{digits}f} ({se:.{digits}f})'


def export_table(root, name, frame):
    out = root/'outputs/tables'
    frame.to_csv(out/f'{name}.csv', index=False, float_format='%.10g')
    # No optional tabulate dependency.
    lines = ['| ' + ' | '.join(map(str, frame.columns)) + ' |',
             '| ' + ' | '.join(['---']*len(frame.columns)) + ' |']
    lines += ['| ' + ' | '.join(str(v).replace('\n', ' ') for v in row) + ' |'
              for row in frame.itertuples(index=False, name=None)]
    (out/f'{name}.md').write_text('\n'.join(lines)+'\n')


def run(root):
    for d in ['outputs/tables', 'outputs/figures', 'data/processed']:
        (root/d).mkdir(parents=True, exist_ok=True)
    paths = [root/'data/raw/01_DID/data/public.csv', root/'01_DID/data/public.csv']
    available = [p for p in paths if p.exists()]
    if not available:
        raise FileNotFoundError('Extract Package 01 into data/raw/ or the project root. See README.md.')
    hashes = [hashlib.sha256(p.read_bytes()).hexdigest() for p in available]
    if len(set(hashes)) > 1:
        raise ValueError('The two accepted input locations contain different files.')
    manifest = json.loads((root/'input_manifest.json').read_text())
    if hashes[0] != manifest['sha256']:
        raise ValueError('Input hash differs from the supplied course CSV. Review provenance before analysis.')
    x = pd.read_csv(available[0])
    assert x.shape == (410, 46)
    x.insert(0, 'row_id', np.arange(1, len(x)+1))
    assert set(x.STATE.unique()) == {0, 1}
    assert set(x.CHAIN.unique()) == {1, 2, 3, 4}
    assert x[['STATE','SHEET']].duplicated().sum() == 0
    for term, code in [('KFC', 2), ('ROY', 3), ('WENDYS', 4)]:
        x[term] = (x.CHAIN == code).astype(int)
    for s in ['', '2']:
        x['fte'+s] = x['EMPFT'+s]+x['NMGRS'+s]+.5*x['EMPPT'+s]
        # This is the original table's numerical convention, not a headcount share.
        x['pctft'+s] = 100*x['EMPFT'+s]/x['fte'+s].replace(0, np.nan)
        x['meal'+s] = x['PSODA'+s]+x['PFRY'+s]+x['PENTREE'+s]
        # Published wage-at-threshold percentages use all state rows: a missing
        # wage is not a positive threshold report. Figure 1 excludes missing wages.
        x['at425'+s] = 100*x['WAGE_ST'+s].eq(4.25).astype(float)
        x['at505'+s] = 100*x['WAGE_ST'+s].eq(5.05).astype(float)
    x.loc[x.STATUS2.eq(3), 'fte2'] = 0
    x.loc[x.STATUS2.isin([0,2,4,5]), 'fte2'] = np.nan
    x['fte2_tempzero'] = x.fte2
    x.loc[x.STATUS2.isin([2,4,5]), 'fte2_tempzero'] = 0
    x['change'] = x.fte2-x.fte
    x['change_tempzero'] = x.fte2_tempzero-x.fte
    x['gap'] = np.where(x.STATE.eq(0), 0, np.maximum(5.05/x.WAGE_ST-1, 0))
    x['nj_owner'] = x.STATE*x.CO_OWNED
    x['gap_owner'] = x.gap*x.CO_OWNED
    x['table4'] = (x.fte.notna() & x.fte2.notna() & x.WAGE_ST.notna()
                   & (x.WAGE_ST2.notna() | x.STATUS2.eq(3)))
    s4 = x[x.table4].copy()
    assert len(s4) == 357
    assert x.change.notna().sum() == 384
    assert x.loc[x.STATUS2.eq(3), 'fte2'].eq(0).all()
    assert x.loc[x.STATUS2.isin([2,4,5]), 'fte2'].isna().all()
    x.to_csv(root/'data/processed/analysis_all.csv', index=False)
    s4.to_csv(root/'data/processed/table4_sample.csv', index=False)
    flow = pd.DataFrame([
        ['Raw survey rows', len(x)], ['New Jersey rows', int(x.STATE.sum())],
        ['Pennsylvania rows', int((x.STATE==0).sum())],
        ['Wave 1 observed FTE', int(x.fte.notna().sum())],
        ['Wave 2 FTE after closure rules', int(x.fte2.notna().sum())],
        ['Both waves FTE', int(x.change.notna().sum())],
        ['Table 4 with valid wages and closure exception', len(s4)],
        ['Permanent closures retained at zero', int(x.STATUS2.eq(3).sum())],
        ['Temporary closures', int(x.STATUS2.isin([2,4,5]).sum())],
        ['Refused second interview', int(x.STATUS2.eq(0).sum())],
    ], columns=['Stage','N'])
    export_table(root, 'sample_flow', flow)

    # Table 2: all rows, variable-specific nonmissing responses.
    specs = [(f'1{chr(97+i)} {label}', 100*x.CHAIN.eq(i+1))
             for i,label in enumerate(['Burger King','KFC','Roy Rogers','Wendys'])]
    specs += [('1e Company owned',100*x.CO_OWNED)]
    for wave,s in [(2,''),(3,'2')]:
        specs += [(f'{wave}a FTE employment',x['fte'+s]),
                  (f'{wave}b Full time percentage convention',x['pctft'+s]),
                  (f'{wave}c Starting wage',x['WAGE_ST'+s]),
                  (f'{wave}d Wage equals 4.25 percent',x['at425'+s])]
        if s: specs += [('3e Wage equals 5.05 percent',x.at5052)]
        letter = 'f' if s else 'e'
        specs += [(f'{wave}{letter} Full meal price',x['meal'+s]),
                  (f'{wave}{chr(ord(letter)+1)} Hours open',x['HRSOPEN'+s]),
                  (f'{wave}{chr(ord(letter)+2)} Recruiting bonus percent',100*x['SPECIAL2' if s else 'BONUS'])]
    t2rows=[]
    for label,series in specs:
        a=series[x.STATE.eq(1)].dropna();b=series[x.STATE.eq(0)].dropna()
        ma,sa,na=mean_se(a);mb,sb,nb=mean_se(b)
        # Both versions make inference convention differences transparent.
        t_w=(ma-mb)/np.sqrt(sa*sa+sb*sb) if sa*sa+sb*sb>0 else np.nan
        t_p=float(stats.ttest_ind(a,b,equal_var=True).statistic)
        t2rows.append([label,ma,sa,na,mb,sb,nb,t_w,t_p])
    t2=pd.DataFrame(t2rows,columns=['Variable','NJ_mean','NJ_SE','NJ_N','PA_mean','PA_SE','PA_N','t_Welch','t_pooled'])
    export_table(root,'table2',t2)

    # Table 3: full eight-column layout, including within-NJ wage groups.
    groups=[x.STATE.eq(0),x.STATE.eq(1),
            x.STATE.eq(1)&x.WAGE_ST.eq(4.25),
            x.STATE.eq(1)&x.WAGE_ST.gt(4.25)&x.WAGE_ST.lt(5),
            x.STATE.eq(1)&x.WAGE_ST.ge(5)]
    labels=['PA','NJ','NJ_low','NJ_mid','NJ_high']
    t3rows=[]; t3long=[]
    for row,label in enumerate(['Before all available','After all available','Change in means','Change balanced','Change temporary zero']):
        vals=[]
        for mask,gname in zip(groups,labels):
            g=x[mask]
            if row in [0,1]: b,se,n=mean_se(g['fte' if row==0 else 'fte2'])
            elif row==2:
                m1,se1,n1=mean_se(g.fte);m2,se2,n2=mean_se(g.fte2)
                # Delta-method SE for the difference of two available-case
                # means, retaining covariance of repeated observations.
                b=m2-m1
                influence=((g.fte2-m2)/n2).fillna(0)-((g.fte-m1)/n1).fillna(0)
                n=int((g.fte.notna()|g.fte2.notna()).sum())
                se=float(np.sqrt(np.sum(influence**2)*n/(n-1)))
            else: b,se,n=mean_se(g['change' if row==3 else 'change_tempzero'])
            vals.append((b,se,n));t3long.append([row+1,label,gname,b,se,n])
        pa,nj,low,mid,high=vals
        def difference(a,b):return a[0]-b[0],np.hypot(a[1],b[1])
        entries=[pa[:2],nj[:2],difference(nj,pa),low[:2],mid[:2],high[:2],difference(low,high),difference(mid,high)]
        t3rows.append([label]+[fmt(*v) for v in entries])
    t3=pd.DataFrame(t3rows,columns=['Statistic','PA','NJ','NJ minus PA','NJ low','NJ mid','NJ high','Low minus high','Mid minus high'])
    export_table(root,'table3',t3)
    export_table(root,'table3_numeric',pd.DataFrame(t3long,columns=['Row','Statistic','Group','Mean','SE','N']))

    # Table 4 uses a common 357-store sample for all five models.
    model_specs=[['STATE'],['STATE']+CONTROL,['gap'],['gap']+CONTROL,['gap']+CONTROL+REGION]
    models=[ols(s4,'change',terms) for terms in model_specs]
    t4rows=[];t4long=[]
    for i,m in enumerate(models):
        main='STATE' if i<2 else 'gap'
        p_controls=np.nan
        if i in [1,3,4]:
            restricted=ols(s4,'change',[main]);q=m['k']-restricted['k']
            f=((restricted['sse']-m['sse'])/q)/(m['sse']/m['df'])
            p_controls=float(stats.f.sf(f,q,m['df']))
        t4rows.append([f'({i+1})',main,fmt(m['beta'][main],m['se'][main]),
                       'Yes' if i in [1,3,4] else 'No','Yes' if i==4 else 'No',m['rmse'],p_controls,m['n']])
        for term in m['terms']:
            t4long.append([i+1,term,m['beta'][term],m['se'][term],m['n']])
    t4=pd.DataFrame(t4rows,columns=['Model','Main variable','Estimate SE','Chain ownership','Region','RMSE','Controls joint p','N'])
    export_table(root,'table4',t4)
    export_table(root,'table4_coefficients',pd.DataFrame(t4long,columns=['Model','Term','Estimate','SE','N']))

    # Original-vs-replication checks for Table 3 and every Table 4 main slope.
    original_t3=np.array([
        [23.33,20.44,-2.89,19.56,20.08,22.25,-2.69,-2.17],
        [21.17,21.03,-.14,20.88,20.96,20.21,.67,.75],
        [-2.16,.59,2.76,1.32,.87,-2.04,3.36,2.91],
        [-2.28,.47,2.75,1.21,.71,-2.16,3.36,2.87],
        [-2.28,.23,2.51,.90,.49,-2.39,3.29,2.88]])
    comparisons=[]
    for i,row in t3.iterrows():
        for j,col in enumerate(t3.columns[1:]):
            b=float(row[col].split(' ')[0]);orig=original_t3[i,j]
            comparisons.append(['Table3',str(i+1),col,orig,b,b-orig])
    # Table 2 targets, transcribed from p. 776 of the published paper.
    orig_nj=[41.1,20.5,24.8,13.6,34.1,20.4,32.8,4.61,30.5,3.35,14.4,23.6,21.0,35.9,5.08,0,85.2,3.41,14.4,20.3]
    orig_pa=[44.3,15.2,21.5,19.0,35.4,23.3,35.0,4.63,32.9,3.04,14.5,29.1,21.2,30.4,4.62,25.3,1.3,3.03,14.7,23.4]
    for i,row in t2.iterrows():
        for st,original in [('NJ',orig_nj[i]),('PA',orig_pa[i])]:
            b=row[st+'_mean'];comparisons.append(['Table2',row.Variable,st,original,b,b-original])
    originals=[2.33,2.30,15.65,14.92,11.91]
    for i,m in enumerate(models):
        main='STATE' if i<2 else 'gap';b=m['beta'][main]
        comparisons.append(['Table4',str(i+1),main,originals[i],b,b-originals[i]])
    comparison=pd.DataFrame(comparisons,columns=['Table','Row model','Statistic','Published','Replicated','Difference'])
    export_table(root,'original_comparison',comparison)

    # Figure 1: explicit bins, missing wages excluded and tail preserved.
    edges=np.r_[np.round(np.arange(4.2,5.51,.1),2),np.inf]
    ticklabels=[f'{v+.05:.2f}' for v in edges[:-2]]+['5.50+']
    fig,axes=plt.subplots(2,1,figsize=(9,7),constrained_layout=True)
    histrows=[]
    for ax,wave,col in zip(axes,[1,2],['WAGE_ST','WAGE_ST2']):
        for state,label,offset,color in [(1,'New Jersey',-.19,'#24465b'),(0,'Pennsylvania',.19,'#b97443')]:
            w=x.loc[x.STATE.eq(state),col].dropna().to_numpy()
            assert (w>=edges[0]).all()
            counts,_=np.histogram(w,bins=edges);shares=100*counts/len(w)
            ax.bar(np.arange(len(counts))+offset,shares,width=.38,label=f'{label} (n={len(w)})',color=color)
            for lo,hi,ct,pct in zip(edges[:-1],edges[1:],counts,shares):
                histrows.append([wave,label,lo,hi,int(ct),len(w),pct])
        ax.set_title('Before the increase' if wave==1 else 'After the increase',loc='left')
        ax.set_ylabel('Percent of observed wages');ax.set_xticks(range(len(ticklabels)),ticklabels,rotation=45)
        ax.legend(frameon=False);ax.spines[['top','right']].set_visible(False)
        ax.set_xlabel('Hourly starting wage bin midpoint in dollars; final bin is 5.50+')
    fig.savefig(root/'outputs/figures/figure1.png',dpi=180);plt.close(fig)
    export_table(root,'figure1_bins',pd.DataFrame(histrows,columns=['Wave','State','Lower inclusive','Upper exclusive','Count','Denominator','Percent']))

    # Independent extension: ownership heterogeneity, common Table 4 sample.
    # Full lower-order terms are retained, as are chain fixed effects.
    extension=ols(s4,'change',['STATE','CO_OWNED','nj_owner','KFC','ROY','WENDYS'],robust=True)
    exrows=[]
    for label,w in [('Franchise NJ minus PA',{'STATE':1}),
                    ('Company NJ minus PA',{'STATE':1,'nj_owner':1}),
                    ('Company minus franchise difference',{'nj_owner':1})]:
        r=contrast(extension,w);exrows.append([label]+list(r.values()))
    ext=pd.DataFrame(exrows,columns=['Contrast','Estimate','HC1_SE','p','CI_low','CI_high','N'])
    export_table(root,'extension',ext)
    cells=s4.groupby(['STATE','CO_OWNED']).agg(N=('change','size'),Before=('fte','mean'),After=('fte2','mean'),Change=('change','mean')).reset_index()
    export_table(root,'extension_cells',cells)
    s4.to_csv(root/'data/processed/extension_sample.csv',index=False)
    # Robustness: every specification is declared, including nonsignificant ones.
    robrows=[]
    for label,df,outcome,terms,target in [
        ('Table4 baseline with HC1',s4,'change',['STATE'],'STATE'),
        ('Ownership interaction HC1',s4,'change',['STATE','CO_OWNED','nj_owner','KFC','ROY','WENDYS'],'nj_owner'),
        ('All balanced stores interaction HC1',x,'change',['STATE','CO_OWNED','nj_owner','KFC','ROY','WENDYS'],'nj_owner'),
        ('Temporary closures zero interaction HC1',x,'change_tempzero',['STATE','CO_OWNED','nj_owner','KFC','ROY','WENDYS'],'nj_owner'),
        ('Gap ownership interaction HC1',s4,'change',['gap','CO_OWNED','gap_owner','KFC','ROY','WENDYS'],'gap_owner')]:
        m=ols(df,outcome,terms,robust=True);r=contrast(m,{target:1})
        robrows.append([label,target]+list(r.values()))
    robustness=pd.DataFrame(robrows,columns=['Specification','Term','Estimate','HC1_SE','p','CI_low','CI_high','N'])
    export_table(root,'robustness',robustness)
    fig,ax=plt.subplots(figsize=(8,3.1),constrained_layout=True)
    y=np.arange(len(ext))
    ax.errorbar(ext.Estimate,y,xerr=np.array([ext.Estimate-ext.CI_low,ext.CI_high-ext.Estimate]),fmt='o',color='#24465b',capsize=4)
    ax.axvline(0,color='gray',ls='--',lw=1);ax.set_yticks(y,['Franchise DID','Company DID','Company minus franchise'])
    ax.invert_yaxis();ax.set_xlabel('FTE employees and 95 percent HC1 intervals');ax.spines[['top','right']].set_visible(False)
    fig.savefig(root/'outputs/figures/extension.png',dpi=180);plt.close(fig)

    # Independent algebraic checks; do not hard-code estimated results.
    balance=x.dropna(subset=['change'])
    simple=balance.groupby('STATE').change.mean();did=float(simple.loc[1]-simple.loc[0])
    b=ols(balance,'change',['STATE'])['beta']['STATE']
    assert np.isclose(did,b,atol=1e-10)
    scipy_check=stats.linregress(s4.STATE,s4.change)
    assert np.isclose(scipy_check.slope,models[0]['beta']['STATE'],atol=1e-10)
    assert np.isclose(scipy_check.stderr,models[0]['se']['STATE'],atol=1e-10)
    # Verify OLS normal equations and exact reconstruction of the FTE variable.
    for m in models:
        xx=np.column_stack([np.ones(m['n']),m['sample'][m['terms'][1:]].to_numpy(float)])
        assert np.max(np.abs(xx.T@m['residual']))<1e-7
    assert all(abs(models[i]['beta']['STATE' if i<2 else 'gap']-originals[i])<.01 for i in range(4))
    # A persistent, disclosed discrepancy in model V is not treated as a failure.
    validation=dict(input_sha256=hashes[0],input_shape=[410,46],rows_preserved=True,
                    repeated_sheet_ids=int(x.SHEET.duplicated().sum()),
                    balanced_n=len(balance),table4_n=len(s4),balanced_did=did,
                    normal_equations_passed=True,mean_difference_equals_ols=True,scipy_slope_and_se_match=True,
                    model5_published=11.91,model5_replicated=models[4]['beta']['gap'],
                    model5_difference=models[4]['beta']['gap']-11.91,
                    table3_max_difference=float(comparison[comparison.Table.eq('Table3')].Difference.abs().max()),
                    python=platform.python_version(),packages={n:importlib.metadata.version(n) for n in ['numpy','pandas','scipy','matplotlib','reportlab']})
    (root/'outputs/validation.json').write_text(json.dumps(validation,indent=2)+'\n')
    return dict(x=x,s4=s4,t2=t2,t3=t3,t4=t4,models=models,extension=ext,
                cells=cells,robustness=robustness,flow=flow,comparison=comparison,validation=validation)
