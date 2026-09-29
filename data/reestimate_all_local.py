#!/usr/bin/env python3
"""
reestimate_all_local.py   (run on think@penguin; 2026-08-15)
Re-estimates every model in Part IV on the corrected panel, with the pandemic-suspension ladder,
the seasonal interaction model (hand list), and phase-defined exposure groups built from QCEW.

Inputs: Florida_Jury_Management_Indices_MASTER_corrected.csv ; seasonal_counties.txt (one county per line,
        the twenty-county hand classification used in Table 4) ; ~/jurydata/jury.db (qcew_county_month)
Outputs: appendix_A_main_models.csv, table4_seasonal_interaction.csv, phase_classes.csv, phase_defined_models.csv
"""
import pandas as pd, numpy as np, sqlite3, os, warnings
import statsmodels.formula.api as smf
warnings.filterwarnings('ignore')
PANEL='Florida_Jury_Management_Indices_MASTER_corrected.csv'; SEAS='seasonal_counties.txt'; DB=os.path.expanduser('~/jurydata/jury.db')
LH_INDUSTRY='1026'   # QCEW supersector: Leisure and hospitality (NAICS 71+72); own_code 5 = private
OUT={'Summoning Yield':'sy','Juror Days / Trial':'jdpt','People Brought In / Trial':'pbi','Percent to Voir Dire':'pvd','Average Panel Size':'aps','Number of Trials':'trials'}
d=pd.read_csv(PANEL).rename(columns={'Quarter #':'q'})
# outcome-specific sample rule: Number of Trials retains reported_all_zero; the five other indices do not
d=d[d['Data Status'].isin(['reported','reported_all_zero'])]
def samp(df,col): return df if col=='Number of Trials' else df[df['Data Status']=='reported']
def wald(m,terms):
    names=list(m.params.index); R=np.zeros((len(terms),len(names)))
    for i,t in enumerate(terms): R[i,names.index(t)]=1
    w=m.wald_test(R,scalar=False,use_f=True); return float(np.squeeze(w.statistic)),float(w.pvalue),int(w.df_num),int(w.df_denom)
def main_model(dd,col,tag):
    dd=samp(dd,col).dropna(subset=[col]).rename(columns={col:'y'})
    m=smf.ols("y ~ C(q, Treatment(reference=3)) + C(County) + C(Year)",data=dd).fit(cov_type='cluster',cov_kwds={'groups':dd['County']})
    T=[f"C(q, Treatment(reference=3))[T.{k}]" for k in (1,2,4)]; F,p,dn,dd_=wald(m,T); rows=[]
    for k,t in zip(('Jan-Mar','Apr-Jun','Oct-Dec'),T):
        lo,hi=m.conf_int().loc[t]; rows.append(dict(sample=tag,outcome=col,term=k,coef=m.params[t],se=m.bse[t],ci_lo=lo,ci_hi=hi,p=m.pvalues[t],n=int(m.nobs),r2=m.rsquared,jointF=F,jointF_p=p,df=f"F({dn},{dd_})"))
    return rows
ladder={'B full corrected':d,'F 2020 Q2-Q3 excluded':d[~((d.Year==2020)&d.q.isin([2,3]))],'E calendar 2020 excluded':d[d.Year!=2020],
        'I 2020-2021 excluded':d[~d.Year.isin([2020,2021])],'G 2008Q4-2019Q4':d[d.Year<2020],'H 2021-2025':d[d.Year>=2021],'J 2022-2025':d[d.Year>=2022]}
rows=[]
for tag,dd in ladder.items():
    for col in OUT: rows+=main_model(dd,col,tag)
pd.DataFrame(rows).to_csv('appendix_A_main_models.csv',index=False); print('main models done')
# ---- Table 4: seasonal x quarter interaction with county FE + year-quarter FE ----
if os.path.exists(SEAS):
    seas=[s.strip() for s in open(SEAS) if s.strip()]; d['seasonal']=d.County.isin(seas).astype(int); d['yq']=d.Year.astype(str)+'Q'+d.q.astype(str)
    def inter(dd,col,tag):
        dd=dd.dropna(subset=[col]).rename(columns={col:'y'})
        m=smf.ols("y ~ seasonal:C(q, Treatment(reference=3)) + C(County) + C(yq)",data=dd).fit(cov_type='cluster',cov_kwds={'groups':dd['County']})
        T=[t for t in m.params.index if t.startswith('seasonal:')]; F,p,dn,dd_=wald(m,T); out=[]
        for t in T:
            lo,hi=m.conf_int().loc[t]; out.append(dict(sample=tag,outcome=col,term=t,coef=m.params[t],se=m.bse[t],ci_lo=lo,ci_hi=hi,p=m.pvalues[t],n=int(m.nobs),jointF=F,jointF_p=p,df=f"F({dn},{dd_})"))
        return out
    t4=[]
    for tag,dd in {'full corrected':d,'2020 Q2-Q3 excluded':d[~((d.Year==2020)&d.q.isin([2,3]))],'pre-2020':d[d.Year<2020],'2020 onward':d[d.Year>=2020],'2021 onward':d[d.Year>=2021]}.items():
        for col in ['Summoning Yield','Number of Trials']: t4+=inter(dd,col,tag)
    pd.DataFrame(t4).to_csv('table4_seasonal_interaction.csv',index=False); print('table 4 done')
else: print('seasonal_counties.txt not found; Table 4 skipped')
# ---- phase-defined exposure from QCEW leisure and hospitality ----
try:
    con=sqlite3.connect(DB)
    q=pd.read_sql(f"select county_fips, year, month, employment from qcew_county_month where state_fips='12' and county_fips<>'12999' and industry_code='{LH_INDUSTRY}' and own_code='5' and employment is not null",con)
    names=pd.read_sql("select distinct county_fips, county from county_seasonality where st='12'",con)
    q=q.merge(names,on='county_fips',how='left')
    q['county_name']=q['county'].astype(str).str.strip()
    q['County']=q.county_name.replace({'Desoto':'DeSoto','Miami-Dade':'Miami-Dade','Dade':'Miami-Dade','St Johns':'St. Johns','St Lucie':'St. Lucie'})
    # within-county monthly index: employment / county-year mean, averaged over years
    q['idx']=q.employment/q.groupby(['County','year']).employment.transform('mean')
    prof=q.groupby(['County','month']).idx.mean().unstack()
    ph=pd.DataFrame({'peak_month':prof.idxmax(axis=1),'trough_month':prof.idxmin(axis=1),'amplitude':prof.max(axis=1)-prof.min(axis=1)})
    ph['phase']=np.where(ph.amplitude<0.06,'flat',np.where(ph.peak_month.isin([12,1,2,3]),'winter_peak',np.where(ph.peak_month.isin([6,7,8]),'summer_peak','other')))
    ph.to_csv('phase_classes.csv'); print(ph.phase.value_counts().to_dict())
    d2=d.merge(ph[['phase']],left_on='County',right_index=True,how='left'); d2['yq']=d2.Year.astype(str)+'Q'+d2.q.astype(str)
    res=[]
    for cls in ['winter_peak','summer_peak']:
        d2['g']=(d2.phase==cls).astype(int)
        for tag,dd in {'full corrected':d2,'2020 Q2-Q3 excluded':d2[~((d2.Year==2020)&d2.q.isin([2,3]))],'pre-2020':d2[d2.Year<2020]}.items():
            for col in ['Summoning Yield','Number of Trials']:
                dd2=samp(dd,col).dropna(subset=[col]).rename(columns={col:'y'})
                m=smf.ols("y ~ g*C(q, Treatment(reference=3)) + C(County) + C(yq)",data=dd2).fit(cov_type='cluster',cov_kwds={'groups':dd2['County']})
                T=[t for t in m.params.index if t.startswith('g:C(q')]; F,p,dn,dd_=wald(m,T)
                for t in T:
                    lo,hi=m.conf_int().loc[t]; res.append(dict(exposure=cls,sample=tag,outcome=col,term=t,coef=m.params[t],se=m.bse[t],ci_lo=lo,ci_hi=hi,p=m.pvalues[t],n=int(m.nobs),jointF=F,jointF_p=p,df=f"F({dn},{dd_})"))
    pd.DataFrame(res).to_csv('phase_defined_models.csv',index=False); print('phase-defined models done')
except Exception as e: print('QCEW step skipped:',e)
