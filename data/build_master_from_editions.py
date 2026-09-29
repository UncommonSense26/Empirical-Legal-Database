import pandas as pd, numpy as np
DEFECTIVE = '20250328-jury-mgmt-qe-202412-ada.pdf'
IDX = {'summoning_yield':'Summoning Yield','juror_days_per_trial':'Juror Days / Trial',
       'people_brought_in_per_trial':'People Brought In / Trial','percent_to_voir_dire':'Percent to Voir Dire',
       'average_panel_size':'Average Panel Size','number_of_trials':'Number of Trials'}
MED = {'Summoning Yield':'SY State Median','Juror Days / Trial':'JDPT State Median',
       'People Brought In / Trial':'PBI State Median','Percent to Voir Dire':'PVD State Median',
       'Average Panel Size':'APS State Median','Number of Trials':'Trials State Median'}
QN = {'Jan-Mar':1,'Apr-Jun':2,'Jul-Sep':3,'Oct-Dec':4}

a = pd.read_csv('jury_indices_all_editions.csv')
a = a[a.unit_type=='county'].copy()
a['County'] = (a.county.astype(str)
               .str.replace(r'^\s*J\s+M\s+I\s+R\s+', '', regex=True)
               .str.replace(r'^[\*\s]+', '', regex=True)
               .str.strip()
               .replace({'Desoto':'DeSoto','Dade':'Miami-Dade','St Johns':'St. Johns','St Lucie':'St. Lucie'}))
a['q'] = a.quarter.map(QN); a['col'] = a['index'].map(IDX)
ed = pd.read_csv('jury_mgmt_editions.csv')
a = a.merge(ed[['filename','quarter_ending_date']], left_on='source_file', right_on='filename', how='left')

clean = a[a.source_file != DEFECTIVE].sort_values('quarter_ending_date')
first = clean.groupby(['County','year','q','col'], as_index=False).first()
last  = clean.groupby(['County','year','q','col'], as_index=False).last()
rev = first.merge(last, on=['County','year','q','col'], suffixes=('_first','_last'))
rev = rev[rev.value_first != rev.value_last].copy()
rev['rel_change'] = (rev.value_last - rev.value_first).abs() / rev.value_first.replace(0, np.nan)
rev.to_csv('out/native_edition_revisions.csv', index=False)
print(f"native revisions: {len(rev)} cells | median |rel change| {rev.rel_change.median():.3f} | counties {rev.County.nunique()}")

w = first.pivot_table(index=['County','year','q'], columns='col', values='value')
m = first.pivot_table(index=['County','year','q'], columns='col', values='comparison_median')
src = first.groupby(['County','year','q']).source_file.first()
M = w.join(m.rename(columns=MED)).join(src).reset_index()
M = M.rename(columns={'year':'Year','q':'Quarter #','source_file':'Source File'})
M['Quarter'] = M['Quarter #'].map({v:k for k,v in QN.items()})
M['QA Flags'] = ''
M.loc[M['Summoning Yield']>100,'QA Flags'] += 'summoning_yield_gt_100_reported; '
M.loc[M['Percent to Voir Dire']>100,'QA Flags'] += 'percent_to_voir_dire_gt_100_reported; '
M['Data Status'] = 'reported'
M = M.sort_values(['Year','Quarter #','County'])
M.to_csv('Florida_Jury_Management_Indices_MASTER_corrected.csv', index=False)

print(f"\nrows {len(M)} | counties {M.County.nunique()} | quarters {M.groupby(['Year','Quarter #']).ngroups}")
print("rows sourced from defective edition:", int((M['Source File']==DEFECTIVE).sum()))
print("\n2024 rows by quarter and source:")
print(M[M.Year==2024].groupby(['Quarter #','Source File']).size().to_string())
odd = ['Columbia','Dixie','Hamilton','Lafayette','Madison','Monroe','Suwannee','Taylor']
print("\neight-county check, Summoning Yield 2023-2024:")
print(M[M.County.isin(odd) & M.Year.isin([2023,2024])].pivot_table(
      index='County', columns=['Year','Quarter #'], values='Summoning Yield').to_string())
