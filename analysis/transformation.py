"""Data transformation (PDF section 3.4 and Unit 1 infographic section 5).

Covers derived measures, binning, normalization (0 to 1), standardization
(mean 0, standard deviation 1), and one-hot encoding of categories.
"""
import numpy as np
import pandas as pd

from analysis.cleaning import SUBJECT_COLS

PASS_MARK = 40
LOW_ATTENDANCE = 75
# Binning: average marks converted into grade bands. right=False means [lower, upper).
GRADE_EDGES = [-np.inf, 40, 55, 70, 85, np.inf]
GRADE_LABELS = ["F", "D", "C", "B", "A"]


def add_derived_columns(df):
    """Average marks, grade (binning), pass or fail, and a low-attendance flag."""
    df = df.copy()
    df["Average_Marks"] = df[SUBJECT_COLS].mean(axis=1).round(2)
    df["Grade"] = pd.cut(df["Average_Marks"], bins=GRADE_EDGES, labels=GRADE_LABELS, right=False).astype(str)
    df["Result"] = np.where(df["Average_Marks"] >= PASS_MARK, "Pass", "Fail")
    df["Low_Attendance"] = df["Attendance_Pct"] < LOW_ATTENDANCE
    return df


def min_max_scale(values):
    """Normalization: rescale values to the range 0 to 1 (infographic: 10 -> 0.00, 40 -> 1.00)."""
    values = np.asarray(values, dtype=float)
    low, high = values.min(), values.max()
    if high == low:
        return np.zeros_like(values)
    return (values - low) / (high - low)


def standardize(values):
    """Standardization: rescale to mean 0 and standard deviation 1."""
    values = np.asarray(values, dtype=float)
    sd = values.std()
    if sd == 0:
        return np.zeros_like(values)
    return (values - values.mean()) / sd


def one_hot_encode(df, column):
    """One-hot encoding of a categorical column: one 0/1 dummy column per category."""
    return pd.get_dummies(df[[column]], prefix=column, dtype=int)


def transformation_preview(df, rows=5):
    """Small table showing the original values next to their transformed versions."""
    head = df.head(rows).reset_index(drop=True)
    preview = pd.DataFrame({
        "Student_ID": head["Student_ID"].to_numpy(),
        "Study_Hours": head["Study_Hours"].to_numpy(),
        "Study_Hours_0to1": np.round(min_max_scale(df["Study_Hours"])[:rows], 2),
        "Final_Score": head["Final_Score"].to_numpy(),
        "Final_Score_z": np.round(standardize(df["Final_Score"])[:rows], 2),
    })
    dummies = one_hot_encode(head, "Gender").reset_index(drop=True)
    return pd.concat([preview, dummies], axis=1)
