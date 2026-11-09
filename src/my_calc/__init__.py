"""Kleine rekenmachine in de stijl van de Mac-rekenmachine, met Tkinter."""

import math
import tkinter as tk
from functools import partial

BG = "#1c1c1c"
DARK = "#505050"  # cijfertoetsen
LIGHT = "#a5a5a5"  # functietoetsen
ORANGE = "#ff9f0a"  # bewerkingen
SCI = "#2e2e2e"  # wetenschappelijke toetsen

OPS = {
    "+": lambda a, b: a + b,
    "−": lambda a, b: a - b,
    "×": lambda a, b: a * b,
    "÷": lambda a, b: a / b,
}


def fmt(value: float) -> str:
    """Zet een getal om naar een nette weergave."""
    if not math.isfinite(value):
        return "Fout"
    if value == int(value) and abs(value) < 1e15:
        return str(int(value))
    return f"{value:.10g}"


class Calculator(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Rekenmachine")
        self.configure(bg=BG)
        self.resizable(False, False)

        self.current = "0"  # wat er op het scherm staat
        self.acc: float | None = None
        self.op: str | None = None
        self.fresh = True  # volgende cijfer begint een nieuw getal
        self.degrees = True

        self.display = tk.Label(
            self,
            text="0",
            anchor="e",
            bg=BG,
            fg="white",
            font=("Helvetica Neue", 44),
            padx=16,
            pady=14,
        )
        self.display.grid(row=0, column=0, columnspan=4, sticky="ew")

        self.mode_btn = self._button(1, 0, "Deg", SCI, self.toggle_mode, fg="#ff9f0a")
        self._button(1, 1, "√", SCI, lambda: self.unary(math.sqrt))
        self._button(1, 2, "x²", SCI, lambda: self.unary(lambda x: x * x))
        self._button(1, 3, "1/x", SCI, lambda: self.unary(lambda x: 1 / x))
        self._button(
            2, 0, "sin", SCI, lambda: self.unary(lambda x: math.sin(self.rad(x)))
        )
        self._button(
            2, 1, "cos", SCI, lambda: self.unary(lambda x: math.cos(self.rad(x)))
        )
        self._button(
            2, 2, "tan", SCI, lambda: self.unary(lambda x: math.tan(self.rad(x)))
        )
        self._button(2, 3, "π", SCI, self.insert_pi)

        rows = [
            [
                ("AC", LIGHT, self.clear),
                ("±", LIGHT, self.negate),
                ("%", LIGHT, lambda: self.unary(lambda x: x / 100)),
                ("÷", ORANGE, lambda: self.operator("÷")),
            ],
            [
                ("7", DARK, None),
                ("8", DARK, None),
                ("9", DARK, None),
                ("×", ORANGE, lambda: self.operator("×")),
            ],
            [
                ("4", DARK, None),
                ("5", DARK, None),
                ("6", DARK, None),
                ("−", ORANGE, lambda: self.operator("−")),
            ],
            [
                ("1", DARK, None),
                ("2", DARK, None),
                ("3", DARK, None),
                ("+", ORANGE, lambda: self.operator("+")),
            ],
            [("0", DARK, None), (",", DARK, self.decimal), ("=", ORANGE, self.equals)],
        ]
        for r, row in enumerate(rows, start=3):
            col = 0
            for text, color, cmd in row:
                if cmd is None:
                    cmd = partial(self.digit, text)
                span = 1
                if text == "0":
                    span = 2
                self._button(
                    r,
                    col,
                    text,
                    color,
                    cmd,
                    span=span,
                    fg="black" if color == LIGHT else "white",
                )
                col += span
        self.bind("<Key>", self.on_key)

    # --- interface -------------------------------------------------------
    def _button(self, row, col, text, color, cmd, span=1, fg="white"):
        # tk.Label i.p.v. tk.Button: macOS negeert kleuren bij tk.Button.
        lbl = tk.Label(
            self,
            text=text,
            bg=color,
            fg=fg,
            cursor="hand2",
            font=("Helvetica Neue", 20),
            width=4 * span,
            height=2,
        )
        lbl.grid(row=row, column=col, columnspan=span, padx=1, pady=1, sticky="nsew")
        lbl.bind("<Button-1>", lambda e: cmd())
        return lbl

    def show(self, text: str) -> None:
        self.current = text
        size = 44 if len(text) <= 9 else max(20, 44 - 3 * (len(text) - 9))
        self.display.config(text=text.replace(".", ","), font=("Helvetica Neue", size))

    # --- logica ----------------------------------------------------------
    def value(self) -> float:
        try:
            return float(self.current)
        except ValueError:
            return 0.0

    def rad(self, x: float) -> float:
        return math.radians(x) if self.degrees else x

    def digit(self, d: str) -> None:
        if self.fresh or self.current in ("0", "Fout"):
            self.show(d)
        elif len(self.current) < 15:
            self.show(self.current + d)
        self.fresh = False

    def decimal(self) -> None:
        if self.fresh:
            self.show("0.")
            self.fresh = False
        elif "." not in self.current:
            self.show(self.current + ".")

    def clear(self) -> None:
        self.acc, self.op, self.fresh = None, None, True
        self.show("0")

    def negate(self) -> None:
        if self.current not in ("0", "Fout"):
            self.show(
                self.current[1:] if self.current.startswith("-") else "-" + self.current
            )

    def unary(self, fn) -> None:
        try:
            result = fmt(fn(self.value()))
        except (ValueError, ZeroDivisionError, OverflowError):
            result = "Fout"
        self.show(result)
        self.fresh = True

    def insert_pi(self) -> None:
        self.show(fmt(math.pi))
        self.fresh = True

    def toggle_mode(self) -> None:
        self.degrees = not self.degrees
        self.mode_btn.config(text="Deg" if self.degrees else "Rad")

    def compute(self) -> None:
        if self.op is not None and self.acc is not None:
            try:
                self.show(fmt(OPS[self.op](self.acc, self.value())))
            except ZeroDivisionError:
                self.show("Fout")

    def operator(self, op: str) -> None:
        if not self.fresh:
            self.compute()
        self.acc = self.value() if self.current != "Fout" else None
        self.op = op
        self.fresh = True

    def equals(self) -> None:
        self.compute()
        self.acc, self.op, self.fresh = None, None, True

    def on_key(self, e: tk.Event) -> None:
        k = e.char
        if k.isdigit():
            self.digit(k)
        elif k in ".,":
            self.decimal()
        elif k in "+-*/":
            self.operator({"+": "+", "-": "−", "*": "×", "/": "÷"}[k])
        elif k in ("=", "\r"):
            self.equals()
        elif k == "%":
            self.unary(lambda x: x / 100)
        elif e.keysym in ("Escape", "c", "C"):
            self.clear()
        elif e.keysym == "BackSpace" and not self.fresh and len(self.current) > 1:
            self.show(self.current[:-1])


def main() -> None:
    Calculator().mainloop()
