#!/usr/bin/env python3
"""Direct winter-peaked vs summer-peaked contrast, county and year-quarter FE, clustered by county."""
import pandas as pd, statsmodels.formula.api as smf, warnings
warnings.filterwarnings('ignore')
d=pd.read_csv("Florida_Jury_Management_Indices_MASTER_corrected.csv")
d=d.rename(columns={'Quarter #':'q'})
d=d[d['Data Status'].isin(['reported','reported_all_zero'])]
def samp(df,col): return df if col=='Number of Trials' else df[df['Data Status']=='reported']
ph=pd.read_csv("phase_classes.csv").set_index("County")
d=d.merge(ph[['phase']],left_on='County',right_index=True,how='left')
d=d[d.phase.isin(['winter_peak','summer_peak'])].copy()
d['g']=(d.phase=='winter_peak').astype(int); d['yq']=d.Year.astype(str)+'Q'+d.q.astype(str)
rows=[]
for col in ['Summoning Yield','Number of Trials','Average Panel Size','Percent to Voir Dire','Juror Days / Trial','People Brought In / Trial']:
    dd=samp(d,col).dropna(subset=[col]).rename(columns={col:'y'})
    m=smf.ols("y ~ g*C(q, Treatment(reference=3)) + C(County) + C(yq)",data=dd).fit(cov_type='cluster',cov_kwds={'groups':dd['County']})
    T=[t for t in m.params.index if t.startswith('g:C(q')]
    for t,lab in zip(T,['Jan-Mar','Apr-Jun','Oct-Dec']):
        lo,hi=m.conf_int().loc[t]
        rows.append(dict(outcome=col,term=lab,coef=m.params[t],se=m.bse[t],ci_lo=lo,ci_hi=hi,p=m.pvalues[t],n=int(m.nobs),counties=dd.County.nunique()))
pd.DataFrame(rows).to_csv("phase_direct_contrast.csv",index=False)
print(pd.DataFrame(rows).to_string(index=False))
