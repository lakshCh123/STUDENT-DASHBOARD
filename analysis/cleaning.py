"""Data cleansing.

Follows PDF section 3.1 ('Cleansing Data'): errors from data entry, redundant
whitespace, capital-letter mismatches, impossible values, outliers and missing
values. The missing-value methods (mean, median, forward fill) come from the
Unit 1 infographic, section 4.
"""
import numpy as np
import pandas as pd

SUBJECT_COLS = ["Mathematics", "Science", "English"]
SCORE_COLS = SUBJECT_COLS + ["Assignment_Score", "Final_Score"]
TEXT_COLS = ["Student_ID", "Gender", "Class", "Section"]
NUMERIC_COLS = SCORE_COLS + ["Attendance_Pct", "Study_Hours"]
REQUIRED_COLS = TEXT_COLS + NUMERIC_COLS

# Sanity-check ranges. Values outside them are impossible (PDF: check 0 <= age <= 120).
VALID_RANGES = {col: (0, 100) for col in SCORE_COLS + ["Attendance_Pct"]}
VALID_RANGES["Study_Hours"] = (0, 24)

OUTLIER_SD = 3.0                     # more than this many SDs from the mean is suspicious
FILL_METHODS = ("median", "mean", "forward")


def load_csv(path):
    """Read a CSV. Class is read as text so '10' is not treated as a number."""
    return pd.read_csv(path, dtype={"Class": str})


def check_required_columns(df):
    missing = [col for col in REQUIRED_COLS if col not in df.columns]
    if missing:
        raise ValueError("CSV is missing required columns: " + ", ".join(missing))


def fix_text(df):
    """Remove redundant whitespace and fix capital-letter mismatches (strip() and lower())."""
    df = df.copy()
    for col in TEXT_COLS:
        df[col] = df[col].astype("string").str.strip()
    gender = df["Gender"].str.lower().fillna("")
    df["Gender"] = gender.where(gender != "", "unknown")
    df["Section"] = df["Section"].str.lower()
    return df


def remove_bad_and_duplicate_rows(df):
    """Drop rows with no Student ID and duplicate records. Returns (df, number_removed)."""
    ids = df["Student_ID"].fillna("")
    cleaned = df[ids != ""]
    cleaned = cleaned.drop_duplicates().drop_duplicates(subset="Student_ID", keep="first")
    return cleaned, len(df) - len(cleaned)


def convert_numbers(df):
    """Text typed into a numeric column becomes missing (PDF: errors from data entry)."""
    df = df.copy()
    for col in NUMERIC_COLS:
        df[col] = pd.to_numeric(df[col], errors="coerce").astype(float)
    return df


def blank_impossible_values(df):
    """Values outside the valid range become missing. Returns (df, counts_per_column)."""
    df = df.copy()
    counts = {}
    for col, (low, high) in VALID_RANGES.items():
        values = df[col]
        bad = values.notna() & ~values.between(low, high)
        counts[col] = int(bad.sum())
        df.loc[bad, col] = np.nan
    return df, counts


def flag_outliers(df):
    """Values far from the column mean are set to missing so they can be reviewed and filled.
    Returns (df, counts_per_column)."""
    df = df.copy()
    counts = {}
    for col in SCORE_COLS + ["Study_Hours"]:
        values = df[col]
        sd = values.std()
        if not sd or np.isnan(sd):
            counts[col] = 0
            continue
        outlier = ((values - values.mean()) / sd).abs() > OUTLIER_SD
        counts[col] = int(outlier.sum())
        df.loc[outlier, col] = np.nan
    return df, counts


def fill_missing(df, method="median"):
    """Fill missing numbers with the mean, the median, or the previous value (forward fill).
    Returns (df, counts_per_column)."""
    if method not in FILL_METHODS:
        raise ValueError(f"Unknown fill method: {method}")
    df = df.copy()
    counts = {}
    for col in NUMERIC_COLS:
        missing = int(df[col].isna().sum())
        if missing == 0:
            continue
        counts[col] = missing
        if method == "forward":
            df[col] = df[col].ffill()
        fill_value = df[col].mean() if method == "mean" else df[col].median()
        df[col] = df[col].fillna(fill_value)
    return df, counts
