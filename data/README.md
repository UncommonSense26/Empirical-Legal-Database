# Florida Jury Management Indices Panel, 2008 Q4 through 2025 Q4
Edition-sourced county-quarter archive. Version 2.1. Deposited by Justin Lamoureux, Independent Researcher.
Companion to "The Moving Denominator: Trial Timing, Seasonal Communities, and the Unexamined Variable in Fair Cross-Section Doctrine" (manuscript in preparation, 2026).

## What changed from Version 1
1. Six Escambia County Average Panel Size cells corrected. Escambia's Average Panel Size prints as 25.9 in the most recent quarter of the first twelve editions in the archive (2009 through 2017). In six of those quarters the next edition republishes the quarter with a different value: 2009 Q4 21.3, 2010 Q2 19.3, 2011 Q1 23.3, 2011 Q4 21.8, 2012 Q3 23.7, 2014 Q2 30.4. Version 1 carried 25.9 in all six under the first-publication rule. Version 2 applies the rule stated below and takes the later value. The other six quarters (2009 Q3, 2013 Q2, 2014 Q4, 2015 Q4, 2016 Q4, 2017 Q4) were never republished with a different value; they remain 25.9 and are flagged. Nothing is imputed.
2. Data Status now has four categories (see data_dictionary.md). Version 1 read "reported" on all 4,422 rows.
3. QA Flags now populated on 97 rows, including all identity failures and all twelve Escambia placeholder cells. Version 1 had 81 flags and none of the identity failures carried one.
4. jury_indices_all_editions.csv: county names normalized (a page-header prefix "J M I R " was stripped from 1,608 rows sourced from the earliest edition; "Desoto" and "Dade" unified to "DeSoto" and "Miami-Dade"); source_note field added.
5. Estimation output regenerated on the reported-only sample. appendix_A_rebuilt.csv and table4_rebuilt.json from Version 1 were computed on a sample that included the 380 all-zero quarters as observations and, for table4, from a hand-classified county list that is not reproducible; both are retained with a SUPERSEDED suffix and should not be cited as findings.
6. Added: reestimate_all_local.py, appendix_A_main_models.csv, phase_classes.csv, phase_defined_models.csv, phase_direct_contrast.py and .csv, identity_interval.py, data_dictionary.md, source_manifest.csv, and the twenty-four source PDFs under source_editions/.

## What changed in Version 2.1
Documentation only; no data file changed. The Version 2 description of the all-zero quarters said that five of six indices are "mechanically zero" in those records. That is correct for the four per-trial and per-panel indices and wrong for Summoning Yield, which does not divide by trials. See the Data Status section below. The Escambia account is also restated with the correct counts of testable and corrected quarters.

## Panel
4,422 county-quarter records. 67 counties. 66 recovered quarters. Six indices per record. Source: Florida Office of the State Courts Administrator quarterly Jury Management Indices Reports, twenty-four editions.

## Vintage rule
Each county-quarter-index cell takes the value from the earliest edition that publishes it (first publication), with two exceptions. (a) The edition for the quarter ending December 2024 (20250328-jury-mgmt-qe-202412-ada.pdf) is excluded as a source for every quarter because it republishes the prior year's values under 2024 labels: 729 of 804 comparable cells in its third and fourth columns are identical to the prior year, state medians included, and its first two columns reconcile to neither clean 2024 edition. Calendar 2024 is therefore sourced from the June 2024, September 2024, and March 2025 editions. (b) Where a first-published value fails the internal identity APS = PBI x PVD outside the envelope permitted by published rounding, and a later edition publishes a different value for the same county-quarter, the later value governs. Exception (b) changed six cells, all Escambia Average Panel Size, listed above.

## Data Status, read before computing any average
See data_dictionary.md for the field definition. The 380 reported_all_zero rows are quarters in which OSCA publishes zero for all six indices.

Zero is a measurement only for Number of Trials. For Juror Days Per Trial, People Brought In Per Trial, Percent to Voir Dire, and Average Panel Size, zero is undefined rather than measured, because those indices divide by trial counts or by quantities that presuppose a trial.

Summoning Yield is a different case, and the Version 2 description stated it incorrectly. The index divides prospective jurors available on the first day of the term by prospective jurors summoned for the term. Neither quantity requires a trial to have occurred. This panel contains 201 records in which a county reports zero trials alongside a positive Summoning Yield, ranging from 18.0 to 68.9; those records are classified as reported and are in the estimation sample. A zero Summoning Yield inside an all-zero record is therefore not a mechanical consequence of holding no trials. It is best read as a non-report, either because no term was summoned or because the county did not file the underlying figures.

The practical consequence is the same either way: the 380 all-zero rows should be excluded from any average or model on the five non-trial indices, because a zero that means "not reported" is no more usable than a zero that means "undefined." They are also unevenly distributed across the calendar, concentrating in July through September, so including them biases quarterly contrasts as well as means.

## Known limits
1. Three quarters are absent from every recovered edition: 2022 Q4, 2023 Q1, 2023 Q2.
2. Three editions covering 2011 through 2013 publish only three of the six charts, so Juror Days Per Trial, People Brought In Per Trial, and Percent to Voir Dire are absent for 603 records in those years.
3. Twenty-four county-quarter records (the seven Third Circuit counties and Monroe, 2023 Q3, 2023 Q4, 2024 Q1) were initially misaligned in a working panel and were re-extracted from the June 2024 and September 2024 editions; see rebuild_vs_session_comparison.csv.
4. Internal identity: testable in 3,818 records, meaning those publishing all three of Average Panel Size, People Brought In Per Trial, and Percent to Voir Dire. On this panel it fails outside the rounding envelope in 6: four Escambia placeholder cells never republished (2014 Q4, 2015 Q4, 2016 Q4, 2017 Q4) and DeSoto 2019 Q4 and 2020 Q1, which print a positive Average Panel Size beside zero PBI and zero PVD. All six reproduce their printed source pages exactly.
5. The Escambia placeholder and the limits of the identity test. Of the twelve affected quarters, the identity is testable in nine and not in three (2011 Q4, 2012 Q3, 2013 Q2, whose editions omit PBI and PVD). That split does not align with the corrected split: of the six corrected quarters four are testable and two are not; of the six uncorrected quarters five are testable and one is not. The identity also fails to flag one placeholder it could reach. Escambia 2009 Q3 prints Average Panel Size 25.9 beside PBI 28.9 and PVD 89.6, whose product is 25.894 and rounds to 25.9, so the placeholder satisfies the identity that quarter and passes the test. Only cross-edition comparison establishes that 25.9 is a placeholder rather than a value. Neither check alone would have produced the correct account.
6. QA Flags mark conditions warranting source review. They are not corrections.
7. OSCA's template mislabels the Second Circuit page's Average Panel Size row as "First Circuit" in every edition inspected. County records only are deposited, so the defect does not enter the panel.
8. OSCA states that these figures are self reported by the clerk of court or the circuit court administrator and that OSCA does not confirm their accuracy, validity, or reliability. This deposit reproduces the published figures; it does not audit them.

## A note on file formats
Dataverse ingests tabular files into an archival tab-delimited format and serves them as .tab. The original CSV files are available through the "original file format" download option. The checksums in SHA256SUMS correspond to the originals, not to the ingested .tab versions.

## Files
Florida_Jury_Management_Indices_MASTER_corrected.csv   wide analysis panel, 4,422 rows, 19 variables
jury_indices_all_editions.csv              long-format extraction, all 24 editions, 46,956 rows
data_dictionary.md                         variable definitions for both files
extract_jury_indices.py                    PDF extractor
build_master_from_editions.py              vintage rule and panel construction
identity_interval.py                       internal identity test with rounding envelope
reestimate_all_local.py                    two-way FE calendar models, QCEW phase classification, phase-defined models
appendix_A_main_models.csv                 calendar models, six outcomes, seven samples, reported-only
phase_classes.csv                          QCEW-derived phase classification, 67 counties
phase_defined_models.csv                   each phase group vs all others
phase_direct_contrast.py / .csv            winter-peaked vs summer-peaked direct contrast
rebuild_vs_session_comparison.csv          panel rebuild audit
appendix_A_rebuilt_SUPERSEDED_v1.csv       Version 1 estimates, all-zero-inclusive sample; do not cite
table4_rebuilt_SUPERSEDED_v1.json          Version 1 hand-list seasonal estimates; not reproducible; do not cite
source_manifest.csv                        24 editions: filename, quarter ending, page count, official URL, SHA-256, archive URL
source_editions/                           the 24 OSCA PDFs as retrieved
SHA256SUMS                                 checksums for the originals; verify with: sha256sum -c SHA256SUMS

## License
CC0 1.0. Derived from Florida public records.
