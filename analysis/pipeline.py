"""Data preparation pipeline: the order of steps in PDF section 3.

Cleansing, then transformation, then combining. The raw input is never changed,
so every step can be checked against the original data.
"""
from analysis import combining, transformation
from analysis.cleaning import (
    FILL_METHODS,
    blank_impossible_values,
    check_required_columns,
    convert_numbers,
    fill_missing,
    fix_text,
    flag_outliers,
    remove_bad_and_duplicate_rows,
)


def _describe(counts):
    nonzero = {name: value for name, value in counts.items() if value}
    return ", ".join(f"{name} {value}" for name, value in nonzero.items()) or "none"


def prepare_data(raw, fill_method="median"):
    """Return (analysis_ready_df, log_lines)."""
    if fill_method not in FILL_METHODS:
        raise ValueError(f"Fill method must be one of: {', '.join(FILL_METHODS)}")
    check_required_columns(raw)

    log = []
    df = raw.copy()
    df.columns = df.columns.str.strip()
    df = fix_text(df)
    log.append("Fixed whitespace and capital letters in text columns; blank gender set to 'unknown'.")

    df, removed = remove_bad_and_duplicate_rows(df)
    log.append(f"Removed {removed} rows with no Student ID or duplicate records.")

    df = convert_numbers(df)
    df, impossible = blank_impossible_values(df)
    log.append("Impossible values set to missing: " + _describe(impossible))

    df, outliers = flag_outliers(df)
    log.append(f"Outliers over {transformation_sd()} SD set to missing: " + _describe(outliers))

    df, filled = fill_missing(df, fill_method)
    log.append(f"Missing numbers filled (method: {fill_method}): " + _describe(filled))

    df = transformation.add_derived_columns(df)
    df = combining.add_class_averages(df)
    return df.reset_index(drop=True), log


def transformation_sd():
    from analysis.cleaning import OUTLIER_SD
    return int(OUTLIER_SD)
