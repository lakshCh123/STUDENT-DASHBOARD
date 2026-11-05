# Student Performance Dashboard

A Tkinter desktop dashboard for analysing student marks, attendance and study habits. Tkinter is the only interface library. All data work follows the methods in the Unit 1 notes (Data Science introduction, facets of data, the data science process and the NumPy/Pandas topics).

## Run it

```bash
pip install -r requirements.txt   # pandas and numpy only
python app.py
```

`generate_data.py` creates a random sample (`python generate_data.py 300` for a different size). Each run gives new data.

## Where each PDF topic is used

| PDF topic | Code |
|---|---|
| 3.1 Cleansing: whitespace, capital letters | `cleaning.fix_text` (strip, lower) |
| 3.1 Errors from data entry (text in numbers) | `cleaning.convert_numbers` |
| 3.1 Impossible values, sanity checks | `cleaning.blank_impossible_values` |
| 3.1 Outliers: validate, then treat as missing | `cleaning.flag_outliers` |
| 3.1 Missing values: remove, constant, mean/median, forward fill | `cleaning.fill_missing` |
| Infographic 4: fill with mean/median, forward fill | `cleaning.fill_missing` |
| 3.1 Duplicate records and data-entry errors | `cleaning.remove_bad_and_duplicate_rows` |
| 3.3 Appending or stacking tables | `combining.append_tables` |
| 3.3 Aggregated measures | `combining.add_class_averages` |
| 3.4 Derived measures and binning | `transformation.add_derived_columns` (grade bands) |
| 3.4 Creating dummies, one-hot encoding | `transformation.one_hot_encode` |
| Infographic 5: normalization 0 to 1 | `transformation.min_max_scale` |
| Infographic 5: standardization (mean 0, SD 1) | `transformation.standardize` |
| 3.5 Exploratory analysis: frequency tables, histograms, graphs | `exploration.frequency_table`, `exploration.histogram`, `dashboard/canvas_charts.py` |
| Describing data: mean, median, mode, SD | `exploration.describe_column` |
| Aggregation by group | `exploration.class_summary` |
| Unit 1 NumPy: arrays, indexing, slicing, search, sort | `exploration.sort_rows`, `exploration.find_student`, `exploration.filter_rows` |
| Unit 1 Pandas: loading CSV files | `cleaning.load_csv` |

Pipeline order (PDF section 3): cleansing, then transformation, then combining. See `analysis/pipeline.py`.

## Project structure

```
student-performance-dashboard/
├── app.py                  # Entry point
├── generate_data.py        # Random sample generator
├── data/students.csv       # Sample data
├── analysis/               # All data work (no GUI code)
│   ├── cleaning.py
│   ├── transformation.py
│   ├── combining.py
│   ├── exploration.py
│   └── pipeline.py         # Runs the steps in PDF order
├── dashboard/              # Tkinter only
│   ├── app_window.py       # Window, filters, tabs, events
│   └── canvas_charts.py    # Bar, histogram and scatter charts drawn on a Canvas
├── requirements.txt
└── README.md
```

## Features

- **Overview:** total students, average marks, highest and lowest subject marks, average attendance, pass rate and grade counts.
- **Students:** sortable table with a column chosen from a dropdown.
- **Student Details:** lookup by ID, with a subject table compared against class averages.
- **Charts:** subject averages, mark histogram, grade counts, attendance vs marks scatter, class averages.
- **Pipeline:** a log of every cleaning step, the raw missing-value counts, and a transformation preview.
- **Filters:** class, section, minimum average marks and minimum attendance.
- **Files:** open a CSV, append another CSV (stacking), generate a random CSV, save the cleaned data.
- **Missing values:** choose median, mean or forward fill from the toolbar.

## Assumptions

- Pass: average of the three subject marks is at least 40.
- Grades: F below 40, D 40 to 54, C 55 to 69, B 70 to 84, A 85 and above.
- Low attendance: below 75%.
- Valid ranges: marks and attendance 0 to 100; study hours 0 to 24.
- Outliers: more than 3 standard deviations from the column mean.

## Limitations

- The PDFs describe methods without naming code. Pandas and NumPy calls are the standard equivalents of the concepts listed.
- Random generation uses NumPy's random generator. Random number generation is not covered in the PDFs, so this is the one step that goes beyond them.
- The data is synthetic. The analysis is descriptive only, with no predictive model.
