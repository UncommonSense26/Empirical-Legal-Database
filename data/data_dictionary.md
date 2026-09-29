# Data dictionary: Florida_Jury_Management_Indices_MASTER_corrected.csv

One row per county-quarter. 4,422 rows, 67 counties, 66 quarters (2008 Q4 through 2025 Q4; 2022 Q4, 2023 Q1, 2023 Q2 not recovered in any edition).

| Column | Type | Meaning |
|---|---|---|
| County | text | Florida county name, 67 values, "Miami-Dade" and "DeSoto" spellings |
| Year | integer | Calendar year of the quarter |
| Quarter # | integer | 1 = Jan-Mar, 2 = Apr-Jun, 3 = Jul-Sep, 4 = Oct-Dec |
| Quarter | text | Quarter label as printed by OSCA |
| Average Panel Size | numeric | OSCA index: prospective jurors sent to voir dire per jury empaneled |
| Juror Days / Trial | numeric | OSCA index: jurors reporting daily plus carry-overs, divided by jury trials |
| Number of Trials | numeric | OSCA index: six-person plus twelve-person jury trials, all divisions |
| People Brought In / Trial | numeric | OSCA index: jurors reporting daily divided by jury trials |
| Percent to Voir Dire | numeric | OSCA index: persons sent to voir dire divided by jurors reporting daily, as a percentage |
| Summoning Yield | numeric | OSCA index: prospective jurors available on day one divided by prospective jurors summoned, as a percentage |
| APS State Median | numeric | Statewide median printed by OSCA beside the county's Average Panel Size, reproduced not recomputed |
| JDPT State Median | numeric | Same, for Juror Days / Trial |
| Trials State Median | numeric | Same, for Number of Trials |
| PBI State Median | numeric | Same, for People Brought In / Trial |
| PVD State Median | numeric | Same, for Percent to Voir Dire |
| SY State Median | numeric | Same, for Summoning Yield |
| Source File | text | Filename of the OSCA edition from which this row's values were taken under the first-publication vintage rule (see README) |
| QA Flags | text | Semicolon-separated flags. Values: aps_placeholder_corrected_from_later_edition; aps_placeholder_uncorrected_in_source; aps_identity_failure_uncorrected_in_source; osca_note_missing_month_<month_year>; and source-condition flags such as summoning yield or percent to voir dire above 100 percent. Empty when no flag applies. Populated on 97 rows. |
| Data Status | text | reported (4,039): values as published. reported_all_zero (380): OSCA publishes zero for all six indices because no jury trials were held; per-trial and per-panel indices are mechanically zero, not measured; exclude before computing means or estimating on those indices. reported_partial_quarter (2): Baker and Hendry, 2012 Q3, computed by OSCA from two months. not_submitted (1): Okaloosa 2025 Q4, all six index fields empty. |

Missing values: empty string. Juror Days / Trial, People Brought In / Trial, and Percent to Voir Dire are empty for 2011 through 2013 rows sourced from three editions that publish only three of the six charts (603 rows), and for the not_submitted row.

# Data dictionary: jury_indices_all_editions.csv

One row per (edition, unit, quarter, index). 46,956 rows. Every value published in every edition, before any vintage rule.

| Column | Meaning |
|---|---|
| source_file | OSCA edition filename |
| unit_type | county or circuit |
| unit_name | As printed on the page header |
| county | County name, normalized (67 values for county rows) |
| circuit | Circuit number for circuit rows |
| year, quarter, quarter_start | Calendar quarter of the value |
| index | One of the six index names, snake_case |
| is_percent | Whether the index is printed as a percentage |
| value | The published value at printed precision |
| comparison_median | The median printed beside it (state median on county pages, circuit median on circuit pages) |
| source_row_label_mismatch | Non-empty when the row label on the page did not match the unit (see README, Second Circuit label defect) |
| source_note | partial_month_missing for the 48 Baker and Hendry rows OSCA marked with an asterisk; empty otherwise |
