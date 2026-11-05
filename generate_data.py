"""Generate a randomised sample student CSV.

Every run produces new data. Pass a seed to generate_random_csv() only if you
need the same file each time.

Run with:  python generate_data.py [number_of_students]
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

OUTPUT = Path(__file__).parent / "data" / "students.csv"
DEFAULT_STUDENTS = 200


def build_students(n, rng):
    """Create random student records. Each student has an underlying 'ability' level
    so that marks, attendance, study hours and assignments are realistically related."""
    ability = rng.normal(60, 12, size=n)

    def marks(subject_shift):
        return np.clip(rng.normal(ability + subject_shift, 8), 0, 100).round(0)

    mathematics = marks(-3)
    science = marks(0)
    english = marks(3)
    attendance = np.clip(rng.normal(82, 9, size=n) + (ability - 60) * 0.2, 40, 100).round(1)
    study_hours = np.clip(rng.normal(3.5, 1.2, size=n) + (ability - 60) * 0.03, 0.5, 10).round(1)
    assignment = np.clip(ability + rng.normal(0, 6, size=n), 0, 100).round(0)
    average = (mathematics + science + english) / 3
    final = np.clip(0.5 * average + 0.25 * assignment + 0.25 * attendance + rng.normal(0, 3, n), 0, 100).round(1)

    return pd.DataFrame({
        "Student_ID": [f"STU{i:03d}" for i in range(1, n + 1)],
        "Gender": rng.choice(["Male", "Female"], size=n),
        "Class": rng.choice(["9", "10", "11", "12"], size=n),
        "Section": rng.choice(["A", "B", "C"], size=n),
        "Mathematics": mathematics,
        "Science": science,
        "English": english,
        "Attendance_Pct": attendance,
        "Study_Hours": study_hours,
        "Assignment_Score": assignment,
        "Final_Score": final,
    })


def add_messy_records(df, rng):
    """Add data-quality problems at random positions, scaled to the dataset size."""
    df = df.copy()
    n = len(df)
    per_issue = max(2, n // 40)
    df.loc[rng.choice(n, per_issue, replace=False), "Mathematics"] = np.nan
    df.loc[rng.choice(n, per_issue, replace=False), "Attendance_Pct"] = np.nan
    df.loc[rng.choice(n, max(1, per_issue // 2), replace=False), "Gender"] = np.nan
    df.loc[int(rng.integers(n)), "English"] = 150    # impossible mark
    df.loc[int(rng.integers(n)), "Science"] = -5     # impossible mark
    duplicates = df.sample(max(2, n // 50), random_state=int(rng.integers(1_000_000)))
    df = pd.concat([df, duplicates], ignore_index=True)
    row_without_id = df.iloc[[0]].copy()
    row_without_id["Student_ID"] = np.nan
    return pd.concat([df, row_without_id], ignore_index=True)


def generate_random_csv(output_path=OUTPUT, n_students=DEFAULT_STUDENTS, seed=None):
    """Write a randomised student CSV and return (path, number_of_rows)."""
    rng = np.random.default_rng(seed)
    df = add_messy_records(build_students(n_students, rng), rng)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    return output_path, len(df)


def main():
    count = int(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_STUDENTS
    path, rows = generate_random_csv(n_students=count)
    print(f"Wrote {rows} rows to {path}")


if __name__ == "__main__":
    main()
