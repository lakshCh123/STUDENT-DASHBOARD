"""Tkinter window for the Student Performance Dashboard.

This file only handles layout and events. The data work lives in analysis/.
"""
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, scrolledtext, ttk

import pandas as pd

from analysis import combining, exploration
from analysis.cleaning import SUBJECT_COLS, load_csv
from analysis.pipeline import FILL_METHODS, prepare_data
from analysis.transformation import LOW_ATTENDANCE, transformation_preview
from dashboard import canvas_charts
from dashboard.canvas_charts import HEIGHT, PASS_COLOR, FAIL_COLOR, WIDTH
from generate_data import OUTPUT as DATA_PATH, generate_random_csv

DEFAULT_COUNT = 200
CHART_OPTIONS = ["Subject averages", "Mark histogram", "Grade counts",
                 "Attendance vs marks", "Class averages"]
METRIC_NAMES = ["Total students", "Average marks", "Average attendance",
                "Highest subject mark", "Lowest subject mark", "Overall pass rate"]
TABLE_COLUMNS = ["Student_ID", "Gender", "Class", "Section", "Average_Marks", "Grade",
                 "Result", "Attendance_Pct", "Study_Hours", "Final_Score", "Class_Avg_Marks"]
READ_ERRORS = (OSError, ValueError, pd.errors.ParserError, pd.errors.EmptyDataError)


class DashboardWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Student Performance Dashboard")
        self.geometry("1200x760")
        self.minsize(980, 640)

        self.raw_df = None
        self.clean_df = None
        self.filtered_df = None
        self.pipeline_log = []

        self.student_count_var = tk.StringVar(value=str(DEFAULT_COUNT))
        self.fill_var = tk.StringVar(value="median")
        self.class_var = tk.StringVar(value="All")
        self.section_var = tk.StringVar(value="All")
        self.min_marks_var = tk.StringVar(value="0")
        self.min_attendance_var = tk.StringVar(value="0")
        self.sort_var = tk.StringVar(value="Average_Marks")
        self.descending_var = tk.BooleanVar(value=True)
        self.student_id_var = tk.StringVar()
        self.chart_var = tk.StringVar(value=CHART_OPTIONS[0])
        self.status_var = tk.StringVar(value="Ready")
        self.grade_var = tk.StringVar(value="")
        self.metric_vars = {name: tk.StringVar(value="-") for name in METRIC_NAMES}

        self._build_toolbar()
        self._build_statusbar()
        self._build_body()

        if DATA_PATH.exists():
            self.open_path(DATA_PATH)
        else:
            self.generate_and_open(DEFAULT_COUNT)

    # ---------- Layout ----------

    def _build_toolbar(self):
        bar = ttk.Frame(self, padding=(10, 8))
        bar.pack(side="top", fill="x")
        ttk.Button(bar, text="Generate random CSV", command=self.on_generate).pack(side="left")
        ttk.Label(bar, text="Students:").pack(side="left", padx=(8, 4))
        ttk.Spinbox(bar, from_=20, to=2000, increment=10, width=6,
                    textvariable=self.student_count_var).pack(side="left")
        ttk.Button(bar, text="Open CSV...", command=self.on_open).pack(side="left", padx=(16, 0))
        ttk.Button(bar, text="Append CSV...", command=self.on_append).pack(side="left", padx=6)
        ttk.Label(bar, text="Missing numbers:").pack(side="left", padx=(16, 4))
        method = ttk.Combobox(bar, textvariable=self.fill_var, values=list(FILL_METHODS),
                              state="readonly", width=9)
        method.pack(side="left")
        method.bind("<<ComboboxSelected>>", lambda event: self.reprocess())
        ttk.Button(bar, text="Save cleaned CSV...", command=self.on_save).pack(side="left", padx=(16, 0))

    def _build_statusbar(self):
        ttk.Label(self, textvariable=self.status_var, anchor="w", relief="sunken",
                  padding=(8, 3)).pack(side="bottom", fill="x")

    def _build_body(self):
        body = ttk.Frame(self, padding=(10, 0, 10, 10))
        body.pack(side="top", fill="both", expand=True)
        self._build_filters(body)

        self.notebook = ttk.Notebook(body)
        self.notebook.pack(side="left", fill="both", expand=True, padx=(10, 0))
        self.tabs = {}
        for name in ["Overview", "Students", "Student Details", "Charts", "Pipeline"]:
            frame = ttk.Frame(self.notebook, padding=10)
            self.notebook.add(frame, text=name)
            self.tabs[name] = frame

        self._build_overview(self.tabs["Overview"])
        self._build_students(self.tabs["Students"])
        self._build_details(self.tabs["Student Details"])
        self._build_charts(self.tabs["Charts"])
        self._build_pipeline(self.tabs["Pipeline"])

    def _build_filters(self, parent):
        panel = ttk.LabelFrame(parent, text="Filters", padding=10)
        panel.pack(side="left", fill="y")

        self.class_combo = self._labelled_combo(panel, 0, "Class", self.class_var)
        self.section_combo = self._labelled_combo(panel, 1, "Section", self.section_var)
        self._labelled_spin(panel, 2, "Min average marks", self.min_marks_var)
        self._labelled_spin(panel, 3, "Min attendance (%)", self.min_attendance_var)

        buttons = ttk.Frame(panel)
        buttons.grid(row=4, column=0, columnspan=2, pady=(8, 0))
        ttk.Button(buttons, text="Apply", command=self.apply_filters).pack(side="left")
        ttk.Button(buttons, text="Reset", command=self.reset_filters).pack(side="left", padx=6)

        ttk.Separator(panel).grid(row=5, column=0, columnspan=2, sticky="ew", pady=12)
        ttk.Label(panel, text="Sort table by").grid(row=6, column=0, sticky="w")
        sort_combo = ttk.Combobox(panel, textvariable=self.sort_var, values=TABLE_COLUMNS,
                                  state="readonly", width=16)
        sort_combo.grid(row=6, column=1, sticky="w")
        sort_combo.bind("<<ComboboxSelected>>", lambda event: self._update_table())
        ttk.Checkbutton(panel, text="Descending", variable=self.descending_var,
                        command=self._update_table).grid(row=7, column=0, columnspan=2, sticky="w", pady=4)

        ttk.Separator(panel).grid(row=8, column=0, columnspan=2, sticky="ew", pady=12)
        ttk.Label(panel, text="Find student by ID").grid(row=9, column=0, columnspan=2, sticky="w")
        id_entry = ttk.Entry(panel, textvariable=self.student_id_var, width=16)
        id_entry.grid(row=10, column=0, pady=4, sticky="w")
        id_entry.bind("<Return>", lambda event: self.find_student())
        ttk.Button(panel, text="Find", command=self.find_student).grid(row=10, column=1, pady=4)

    def _labelled_combo(self, parent, row, text, variable):
        ttk.Label(parent, text=text).grid(row=row, column=0, sticky="w", pady=4)
        combo = ttk.Combobox(parent, textvariable=variable, state="readonly", width=12)
        combo.grid(row=row, column=1, pady=4)
        combo.bind("<<ComboboxSelected>>", lambda event: self.apply_filters())
        return combo

    def _labelled_spin(self, parent, row, text, variable):
        ttk.Label(parent, text=text).grid(row=row, column=0, sticky="w", pady=4)
        spin = ttk.Spinbox(parent, from_=0, to=100, increment=5, width=8,
                           textvariable=variable, command=self.apply_filters)
        spin.grid(row=row, column=1, pady=4)
        spin.bind("<Return>", lambda event: self.apply_filters())

    def _build_overview(self, parent):
        grid = ttk.Frame(parent)
        grid.pack(anchor="nw")
        for index, name in enumerate(METRIC_NAMES):
            card = ttk.LabelFrame(grid, text=name, padding=12)
            card.grid(row=index // 3, column=index % 3, padx=8, pady=8, sticky="nsew")
            ttk.Label(card, textvariable=self.metric_vars[name], font=("Helvetica", 18, "bold")).pack()
        ttk.Label(parent, text="Grade counts", font=("Helvetica", 12, "bold")).pack(anchor="w", pady=(20, 4))
        ttk.Label(parent, textvariable=self.grade_var).pack(anchor="w")

    def _build_students(self, parent):
        frame = ttk.Frame(parent)
        frame.pack(fill="both", expand=True)
        self.table = ttk.Treeview(frame, columns=TABLE_COLUMNS, show="headings")
        for column in TABLE_COLUMNS:
            self.table.heading(column, text=column.replace("_", " "))
            self.table.column(column, width=105, anchor="center")
        vertical = ttk.Scrollbar(frame, orient="vertical", command=self.table.yview)
        horizontal = ttk.Scrollbar(frame, orient="horizontal", command=self.table.xview)
        self.table.configure(yscrollcommand=vertical.set, xscrollcommand=horizontal.set)
        self.table.grid(row=0, column=0, sticky="nsew")
        vertical.grid(row=0, column=1, sticky="ns")
        horizontal.grid(row=1, column=0, sticky="ew")
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)

    def _build_details(self, parent):
        self.details_text = tk.Text(parent, height=11, wrap="none", font=("Courier", 10), state="disabled")
        self.details_text.pack(fill="x")
        self.details_canvas = tk.Canvas(parent, width=WIDTH, height=HEIGHT, bg="white", highlightthickness=0)
        self.details_canvas.pack(pady=(10, 0))

    def _build_charts(self, parent):
        controls = ttk.Frame(parent)
        controls.pack(fill="x")
        ttk.Label(controls, text="Chart:").pack(side="left")
        combo = ttk.Combobox(controls, textvariable=self.chart_var, values=CHART_OPTIONS,
                             state="readonly", width=24)
        combo.pack(side="left", padx=6)
        combo.bind("<<ComboboxSelected>>", lambda event: self.update_chart())
        self.chart_canvas = tk.Canvas(parent, width=WIDTH, height=HEIGHT, bg="white", highlightthickness=0)
        self.chart_canvas.pack(pady=10)

    def _build_pipeline(self, parent):
        self.pipeline_text = scrolledtext.ScrolledText(parent, wrap="none", font=("Courier", 10), state="disabled")
        self.pipeline_text.pack(fill="both", expand=True)

    def _build_statusbar_text(self, text):
        self.status_var.set(text)

    # ---------- Loading and saving ----------

    def open_path(self, path):
        try:
            self.raw_df = load_csv(path)
        except READ_ERRORS as error:
            messagebox.showerror("Could not open CSV", str(error), parent=self)
            return
        self.class_var.set("All")
        self.section_var.set("All")
        self.reprocess(source=Path(path).name)

    def on_open(self):
        path = filedialog.askopenfilename(parent=self, filetypes=[("CSV files", "*.csv"), ("All files", "*.*")])
        if path:
            self.open_path(path)

    def on_append(self):
        if self.raw_df is None:
            self.on_open()
            return
        path = filedialog.askopenfilename(parent=self, filetypes=[("CSV files", "*.csv"), ("All files", "*.*")])
        if not path:
            return
        try:
            new_rows = load_csv(path)
            self.raw_df = combining.append_tables(self.raw_df, new_rows)
        except READ_ERRORS as error:
            messagebox.showerror("Could not append CSV", str(error), parent=self)
            return
        self.reprocess(source=f"{Path(path).name} appended")

    def on_save(self):
        if self.clean_df is None:
            messagebox.showinfo("Nothing to save", "Open a CSV first.", parent=self)
            return
        path = filedialog.asksaveasfilename(parent=self, defaultextension=".csv",
                                            initialfile="students_cleaned.csv",
                                            filetypes=[("CSV files", "*.csv")])
        if path:
            self.clean_df.to_csv(path, index=False)
            self.status_var.set(f"Saved cleaned data to {path}")

    def on_generate(self):
        try:
            count = int(self.student_count_var.get())
        except ValueError:
            messagebox.showerror("Invalid number", "Enter a whole number of students.", parent=self)
            return
        count = max(20, min(count, 2000))
        self.student_count_var.set(str(count))
        if DATA_PATH.exists() and not messagebox.askyesno(
            "Overwrite data?", f"Replace {DATA_PATH.name} with a new random dataset?", parent=self
        ):
            return
        self.generate_and_open(count)

    def generate_and_open(self, count):
        generate_random_csv(DATA_PATH, n_students=count)
        self.open_path(DATA_PATH)

    def reprocess(self, source=None):
        """Run the preparation pipeline on the raw data and refresh every view."""
        if self.raw_df is None:
            return
        try:
            self.clean_df, self.pipeline_log = prepare_data(self.raw_df, self.fill_var.get())
        except ValueError as error:
            messagebox.showerror("Cleaning failed", str(error), parent=self)
            return
        classes = sorted(self.clean_df["Class"].unique().tolist(), key=lambda c: (len(c), c))
        sections = sorted(self.clean_df["Section"].unique().tolist())
        self.class_combo["values"] = ["All"] + classes
        self.section_combo["values"] = ["All"] + sections
        self.apply_filters()
        self._update_pipeline()
        prefix = f"{source}: " if source else ""
        self.status_var.set(f"{prefix}{len(self.raw_df)} raw rows, {len(self.clean_df)} after cleaning")

    # ---------- Filtering and views ----------

    def apply_filters(self):
        if self.clean_df is None:
            return
        try:
            min_marks = float(self.min_marks_var.get())
            min_attendance = float(self.min_attendance_var.get())
        except ValueError:
            messagebox.showerror("Invalid filter", "Minimum marks and attendance must be numbers.", parent=self)
            return
        classes = None if self.class_var.get() == "All" else [self.class_var.get()]
        sections = None if self.section_var.get() == "All" else [self.section_var.get()]
        self.filtered_df = exploration.filter_rows(self.clean_df, classes, sections, min_marks, min_attendance)
        self._update_overview()
        self._update_table()
        self.update_chart()
        self.status_var.set(f"Showing {len(self.filtered_df)} of {len(self.clean_df)} students")

    def reset_filters(self):
        self.class_var.set("All")
        self.section_var.set("All")
        self.min_marks_var.set("0")
        self.min_attendance_var.set("0")
        self.apply_filters()

    def _update_overview(self):
        df = self.filtered_df
        if df.empty:
            for var in self.metric_vars.values():
                var.set("-")
            self.grade_var.set("No students match the current filters.")
            return
        metrics = exploration.overview_metrics(df)
        self.metric_vars["Total students"].set(f"{metrics['Total students']:,}")
        self.metric_vars["Average marks"].set(f"{metrics['Average marks']:.1f}")
        self.metric_vars["Average attendance"].set(f"{metrics['Average attendance']:.1f}%")
        self.metric_vars["Highest subject mark"].set(f"{metrics['Highest subject mark']:.0f}")
        self.metric_vars["Lowest subject mark"].set(f"{metrics['Lowest subject mark']:.0f}")
        self.metric_vars["Overall pass rate"].set(f"{metrics['Overall pass rate']:.1f}%")
        counts = exploration.frequency_table(df["Grade"])
        self.grade_var.set("     ".join(f"{g}: {c}" for g, c in zip(counts["Value"], counts["Count"])))

    def _update_table(self):
        self.table.delete(*self.table.get_children())
        if self.filtered_df is None:
            return
        ordered = exploration.sort_rows(self.filtered_df, self.sort_var.get(), self.descending_var.get())
        for row in ordered[TABLE_COLUMNS].itertuples(index=False):
            values = [f"{value:.1f}" if isinstance(value, float) else value for value in row]
            self.table.insert("", "end", values=values)

    def update_chart(self):
        df = self.filtered_df
        canvas = self.chart_canvas
        if df is None or df.empty:
            canvas.delete("all")
            canvas.create_text(WIDTH / 2, HEIGHT / 2, text="No students match the current filters.")
            return
        name = self.chart_var.get()
        if name == "Subject averages":
            means = exploration.subject_means(df)
            canvas_charts.draw_bar_chart(canvas, list(means), list(means.values()),
                                         "Average marks by subject", "Average marks",
                                         x_label="Subject", y_max=100)
        elif name == "Mark histogram":
            labels, counts = exploration.histogram(df["Average_Marks"], bins=10)
            canvas_charts.draw_bar_chart(canvas, labels, list(counts), "Distribution of average marks",
                                         "Students", x_label="Average marks")
        elif name == "Grade counts":
            table = exploration.frequency_table(df["Grade"])
            canvas_charts.draw_bar_chart(canvas, list(table["Value"]), list(table["Count"]),
                                         "Grade counts", "Students", x_label="Grade")
        elif name == "Attendance vs marks":
            colors = [PASS_COLOR if result == "Pass" else FAIL_COLOR for result in df["Result"]]
            canvas_charts.draw_scatter(canvas, df["Attendance_Pct"], df["Average_Marks"], colors,
                                       "Attendance vs average marks (green = pass)",
                                       "Attendance (%)", "Average marks")
        elif name == "Class averages":
            summary = exploration.class_summary(df)
            labels = [f"{c}-{s}" for c, s in zip(summary["Class"], summary["Section"])]
            canvas_charts.draw_bar_chart(canvas, labels, list(summary["Avg_Marks"]),
                                         "Average marks by class and section", "Average marks",
                                         x_label="Class-section", y_max=100)

    def find_student(self):
        if self.clean_df is None:
            return
        query = self.student_id_var.get().strip()
        if not query:
            messagebox.showinfo("Find student", "Enter a Student ID.", parent=self)
            return
        row = exploration.find_student(self.clean_df, query)
        if row is None:
            self._write(self.details_text, f"No student found with ID {query}.")
            self.details_canvas.delete("all")
        else:
            self._show_student(row)
        self.notebook.select(self.tabs["Student Details"])

    def _show_student(self, row):
        averages = exploration.subject_means(self.clean_df)
        lines = [
            f"Student {row['Student_ID']}   Class {row['Class']}-{row['Section']}   Gender: {row['Gender']}",
            f"Average marks: {row['Average_Marks']:.1f}   Grade: {row['Grade']}   Result: {row['Result']}",
            f"Attendance: {row['Attendance_Pct']:.1f}%   Study hours/day: {row['Study_Hours']:.1f}"
            f"   Final score: {row['Final_Score']:.1f}",
            "",
            f"{'Subject':<14}{'Student':>9}{'Class average':>16}",
        ]
        for subject in SUBJECT_COLS:
            lines.append(f"{subject:<14}{row[subject]:>9.0f}{averages[subject]:>16.1f}")
        if row["Low_Attendance"]:
            lines.append(f"Flag: attendance is below {LOW_ATTENDANCE}%")
        self._write(self.details_text, "\n".join(lines))
        canvas_charts.draw_bar_chart(self.details_canvas, SUBJECT_COLS,
                                     [row[s] for s in SUBJECT_COLS],
                                     f"Subject marks: {row['Student_ID']}", "Marks",
                                     x_label="Subject", y_max=100)

    def _update_pipeline(self):
        lines = ["CLEANING AND PREPARATION LOG"]
        lines += [f"  - {entry}" for entry in self.pipeline_log]
        lines += ["", f"Rows: {len(self.raw_df)} raw -> {len(self.clean_df)} analysis-ready", "",
                  "MISSING VALUES IN RAW DATA", self.raw_df.isna().sum().to_string(), "",
                  "TRANSFORMATION PREVIEW (normalization 0 to 1, standardization, one-hot Gender)",
                  transformation_preview(self.clean_df).to_string(index=False)]
        self._write(self.pipeline_text, "\n".join(lines))

    @staticmethod
    def _write(widget, text):
        widget.configure(state="normal")
        widget.delete("1.0", "end")
        widget.insert("1.0", text)
        widget.configure(state="disabled")


def main():
    DashboardWindow().mainloop()
