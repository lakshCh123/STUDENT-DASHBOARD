"""Charts drawn directly on a tkinter Canvas. No plotting library is used."""
import numpy as np

WIDTH = 640
HEIGHT = 380
LEFT, RIGHT, TOP, BOTTOM = 60, WIDTH - 20, 45, HEIGHT - 50
BAR_COLOR = "#4C72B0"
PASS_COLOR = "#2A9D8F"
FAIL_COLOR = "#E76F51"


def _axes(canvas, title, x_label, y_label):
    canvas.create_text(WIDTH / 2, 18, text=title, font=("Helvetica", 12, "bold"))
    canvas.create_text(LEFT, TOP - 14, text=y_label, anchor="w")
    canvas.create_line(LEFT, TOP, LEFT, BOTTOM)
    canvas.create_line(LEFT, BOTTOM, RIGHT, BOTTOM)
    canvas.create_text(WIDTH / 2, HEIGHT - 12, text=x_label)


def _format(value):
    return f"{value:.1f}" if isinstance(value, float) else str(value)


def draw_bar_chart(canvas, labels, values, title, y_label, x_label="", y_max=None):
    canvas.delete("all")
    _axes(canvas, title, x_label, y_label)
    if len(labels) == 0:
        canvas.create_text(WIDTH / 2, HEIGHT / 2, text="No data to show")
        return
    top_value = y_max or (max(values) * 1.1 if max(values) > 0 else 1)
    slot = (RIGHT - LEFT) / len(labels)
    bar_width = slot * 0.6
    for index, (label, value) in enumerate(zip(labels, values)):
        x0 = LEFT + index * slot + (slot - bar_width) / 2
        x1 = x0 + bar_width
        y0 = BOTTOM - (value / top_value) * (BOTTOM - TOP)
        canvas.create_rectangle(x0, y0, x1, BOTTOM, fill=BAR_COLOR, outline="")
        canvas.create_text((x0 + x1) / 2, y0 - 8, text=_format(value), font=("Helvetica", 9))
        canvas.create_text((x0 + x1) / 2, BOTTOM + 14, text=str(label), font=("Helvetica", 9))


def _span(values):
    low, high = float(values.min()), float(values.max())
    if high == low:
        high = low + 1
    return low, high


def draw_scatter(canvas, xs, ys, colors, title, x_label, y_label):
    canvas.delete("all")
    _axes(canvas, title, x_label, y_label)
    xs = np.asarray(xs, dtype=float)
    ys = np.asarray(ys, dtype=float)
    if xs.size == 0:
        canvas.create_text(WIDTH / 2, HEIGHT / 2, text="No data to show")
        return
    x_low, x_high = _span(xs)
    y_low, y_high = _span(ys)
    for x, y, color in zip(xs, ys, colors):
        px = LEFT + (x - x_low) / (x_high - x_low) * (RIGHT - LEFT)
        py = BOTTOM - (y - y_low) / (y_high - y_low) * (BOTTOM - TOP)
        canvas.create_oval(px - 3, py - 3, px + 3, py + 3, fill=color, outline="")
    canvas.create_text(LEFT, BOTTOM + 14, text=f"{x_low:.0f}", anchor="w")
    canvas.create_text(RIGHT, BOTTOM + 14, text=f"{x_high:.0f}", anchor="e")
    canvas.create_text(LEFT - 6, BOTTOM, text=f"{y_low:.0f}", anchor="e")
    canvas.create_text(LEFT - 6, TOP, text=f"{y_high:.0f}", anchor="e")
