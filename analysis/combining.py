"""Combining data (PDF section 3.3): appending (stacking) tables and aggregated measures."""
import pandas as pd


def append_tables(first, second):
    """Stack the rows of two tables that have the same columns (PDF: appending or stacking)."""
    mismatched = set(first.columns) ^ set(second.columns)
    if mismatched:
        raise ValueError("Cannot append: column names differ: " + ", ".join(sorted(mismatched)))
    return pd.concat([first, second], ignore_index=True)


def add_class_averages(df):
    """Aggregated measure (PDF: 'add calculated information to the table to enrich the data').
    Adds the average marks of each student's class and section to every row."""
    df = df.copy()
    df["Class_Avg_Marks"] = df.groupby(["Class", "Section"])["Average_Marks"].transform("mean").round(2)
    return df
