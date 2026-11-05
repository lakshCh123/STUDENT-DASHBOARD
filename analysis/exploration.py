"""Exploratory data analysis (PDF section 3.5 and 'Describing data' in section 3.7 of the process).

Uses the Unit 1 NumPy and pandas operations: arrays, indexing, slicing, search,
sort, and aggregation.
"""
import numpy as np
import pandas as pd

from analysis.cleaning import SUBJECT_COLS


def frequency_table(values):
    """How often each value appears. Useful for spotting typos such as 'Godo' vs 'Good'."""
    counts = pd.Series(values).value_counts().sort_index()
    total = counts.sum()
    return pd.DataFrame({
        "Value": counts.index,
        "Count": counts.to_numpy(),
        "Percent": np.round(counts.to_numpy() / total * 100, 1),
    })


def describe_column(values):
    """Mean, median, mode and standard deviation (PDF: summarizing data)."""
    arr = np.asarray(values, dtype=float)
    arr = arr[~np.isnan(arr)]
    return {
        "Mean": float(np.mean(arr)),
        "Median": float(np.median(arr)),
        "Mode": float(pd.Series(arr).mode().iloc[0]),
        "Std dev": float(np.std(arr, ddof=1)),
        "Min": float(arr.min()),
        "Max": float(arr.max()),
    }


def summary_table(df, columns):
    rows = []
    for col in columns:
        stats = describe_column(df[col].to_numpy())
        rows.append({"Column": col, **{name: round(value, 2) for name, value in stats.items()}})
    return pd.DataFrame(rows)


def subject_means(df):
    """Column means computed on a 2-D NumPy array (one column per subject)."""
    means = df[SUBJECT_COLS].to_numpy(dtype=float).mean(axis=0)
    return dict(zip(SUBJECT_COLS, np.round(means, 2)))


def histogram(values, bins=10):
    """Counts per equal-width bin (PDF: histograms). Returns (labels, counts)."""
    counts, edges = np.histogram(np.asarray(values, dtype=float), bins=bins)
    labels = [f"{edges[i]:.0f}-{edges[i + 1]:.0f}" for i in range(len(counts))]
    return labels, counts


def pass_rate(df):
    if df.empty:
        return 0.0
    return float(np.mean(df["Result"].to_numpy() == "Pass") * 100)


def overview_metrics(df):
    marks = df[SUBJECT_COLS].to_numpy(dtype=float)
    return {
        "Total students": len(df),
        "Average marks": float(df["Average_Marks"].mean()),
        "Average attendance": float(df["Attendance_Pct"].mean()),
        "Highest subject mark": float(marks.max()),
        "Lowest subject mark": float(marks.min()),
        "Overall pass rate": pass_rate(df),
    }


def class_summary(df):
    """Aggregation (PDF: aggregating data) per class and section."""
    summary = df.groupby(["Class", "Section"]).agg(
        Students=("Student_ID", "count"),
        Avg_Marks=("Average_Marks", "mean"),
        Avg_Attendance=("Attendance_Pct", "mean"),
        Pass_Rate=("Result", lambda results: float(np.mean(results.to_numpy() == "Pass") * 100)),
    )
    return summary.round(2).reset_index()


def sort_rows(df, column, descending=False):
    """Sort rows by one column using NumPy's argsort (Unit 1: sort)."""
    order = np.argsort(df[column].to_numpy(), kind="stable")
    if descending:
        order = order[::-1]
    return df.iloc[order]


def top_and_bottom(df, n=5):
    ordered = sort_rows(df, "Average_Marks", descending=True)
    return ordered.head(n), ordered.tail(n).iloc[::-1]


def find_student(df, student_id):
    """Search by ID with a boolean mask (Unit 1: search and indexing). Returns a row or None."""
    key = student_id.strip().lower()
    matches = df[df["Student_ID"].str.lower().to_numpy() == key]
    return None if matches.empty else matches.iloc[0]


def filter_rows(df, classes=None, sections=None, min_marks=0, min_attendance=0):
    """Combine boolean masks. None means 'no filter'; an empty list matches nothing."""
    mask = np.ones(len(df), dtype=bool)
    if classes is not None:
        mask &= np.isin(df["Class"].to_numpy(), list(classes))
    if sections is not None:
        mask &= np.isin(df["Section"].to_numpy(), list(sections))
    mask &= df["Average_Marks"].to_numpy() >= min_marks
    mask &= df["Attendance_Pct"].to_numpy() >= min_attendance
    return df[mask]
