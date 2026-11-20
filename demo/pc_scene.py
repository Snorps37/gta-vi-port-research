"""Run the original keyboard scene, or verify its input path with --smoke."""

import argparse
import tkinter as tk

WIDTH, HEIGHT = 480, 300
STEP = 12
DIRECTIONS = {"Left": (-STEP, 0), "Right": (STEP, 0),
              "Up": (0, -STEP), "Down": (0, STEP)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--smoke", action="store_true")
    args = parser.parse_args()

    root = tk.Tk()
    root.title("Project NATIVE | Arrow keys to move")
    root.resizable(False, False)
    canvas = tk.Canvas(root, width=WIDTH, height=HEIGHT, bg="#101c2c",
                       highlightthickness=0)
    canvas.pack()
    square = canvas.create_rectangle(224, 134, 256, 166, fill="#6cdacb", outline="")

    def move(event):
        dx, dy = DIRECTIONS[event.keysym]
        left, top, right, bottom = canvas.coords(square)
        dx = max(-left, min(dx, WIDTH - right))
        dy = max(-top, min(dy, HEIGHT - bottom))
        canvas.move(square, dx, dy)

    for key in DIRECTIONS:
        canvas.bind(f"<KeyPress-{key}>", move)
    canvas.focus_set()

    if args.smoke:
        try:
            root.wait_visibility(canvas)
            canvas.focus_force()
            root.update()
            x, y, _, _ = canvas.coords(square)
            for key in ("Right", "Down", "Left", "Up"):
                canvas.event_generate(f"<KeyPress-{key}>", when="tail")
                root.update()
                dx, dy = DIRECTIONS[key]
                x, y = x + dx, y + dy
                if canvas.coords(square)[:2] != [x, y]:
                    raise RuntimeError(f"Square failed to move {key} to ({x}, {y})")
            print("PASS: Tk canvas rendered and all four arrow keys moved the square.")
        finally:
            root.destroy()
    else:
        root.mainloop()


if __name__ == "__main__":
    main()
