import colorsys
import mss
import pyautogui as _pg
import customtkinter as ctk

def main():
    # Update frequency (ms)
    CAPTURE_INTERVAL_MS = 50  # 0.05 s

    ctk.set_appearance_mode("dark")

    # --- Window setup ---
    root = ctk.CTk()
    root.title("MouseUtils")
    root.resizable(False, False)
    root.overrideredirect(True)        # no title bar / controls
    root.wm_attributes("-topmost", True)
    root.configure(borderwidth=0)
    root.pack_propagate(False)
    root.geometry("300x160+0+0")

    # --- Clipboard + beep helper ---
    def copy_to_clipboard(text: str):
        """Copy text to clipboard and play a short confirmation sound."""
        if not text:
            root.bell()
            return
        root.clipboard_clear()
        root.clipboard_append(text)
        root.update()
        root.bell()

    # --- Close button (macOS-style round red) ---
    # macOS traffic-light close color is roughly #FF605C
    close_btn = ctk.CTkButton(
        root,
        text="",                 # no glyph; use solid circle look
        width=16, height=16,     # small round button
        corner_radius=8,         # half of width/height -> circle
        fg_color="#FF605C",      # red (close)
        hover_color="#E04E4A",   # darker on hover
        border_width=1,
        border_color="#3A3A3A",  # subtle border to match dark theme
        command=root.destroy
    )
    # Slight insets from top-left for a native feel
    close_btn.place(x=8, y=8)

    # --- Title label (also acts as draggable area) ---
    title_label = ctk.CTkLabel(
        root,
        text="MouseUtils",
        font=ctk.CTkFont(size=20, weight="bold")
    )
    title_label.place(x=150, y=22, anchor=ctk.CENTER)

    # Optional: allow dragging the window by grabbing the title
    _drag = {"x": 0, "y": 0}
    def start_drag(e):
        _drag["x"], _drag["y"] = e.x_root, e.y_root

    def while_drag(e):
        dx, dy = e.x_root - _drag["x"], e.y_root - _drag["y"]
        _drag["x"], _drag["y"] = e.x_root, e.y_root
        # Move window by delta
        # Current geometry is like "WxH+X+Y"; we just adjust X/Y
        geom = root.winfo_geometry()
        # Extract X and Y from geometry
        try:
            _, pos = geom.split("+", 1)
            x_str, y_str = pos.split("+", 1)
            x, y = int(x_str), int(y_str)
        except Exception:
            x, y = 0, 0
        root.geometry(f"+{x + dx}+{y + dy}")

    title_label.bind("<Button-1>", start_drag)
    title_label.bind("<B1-Motion>", while_drag)

    # --- Info labels ---
    label_position = ctk.CTkLabel(root, text="", width=220)
    label_position.place(x=150, y=45, anchor=ctk.CENTER)

    label_rgb = ctk.CTkLabel(root, text="", width=160)
    label_rgb.place(x=150, y=72, anchor=ctk.CENTER)

    label_hex = ctk.CTkLabel(root, text="", width=160)
    label_hex.place(x=150, y=95, anchor=ctk.CENTER)

    label_hsl = ctk.CTkLabel(root, text="", width=160)
    label_hsl.place(x=150, y=117, anchor=ctk.CENTER)

    hint_label = ctk.CTkLabel(root, text="Press 1, 2, or 3 to copy.")
    hint_label.place(x=150, y=145, anchor=ctk.CENTER)

    # --- Values to copy (updated on each tick) ---
    c_rgb = c_hex = c_hsl = ""

    # Create a single MSS instance (faster than creating each tick)
    _sct = mss.mss()

    def tick():
        """Main UI-safe loop: reads mouse pixel color and updates labels."""
        global c_rgb, c_hex, c_hsl

        # Current mouse position
        x, y = _pg.position()

        # Grab a 1x1 region at the mouse (virtual monitor coordinates)
        region = {"left": int(x), "top": int(y), "width": 1, "height": 1}
        px = _sct.grab(region)          # returns BGRA
        b, g, r, *_ = px.pixel(0, 0)    # ignore alpha if present

        # Format HEX and HSL
        hex_color = f"#{r:02x}{g:02x}{b:02x}"
        h, l, s = colorsys.rgb_to_hls(r/255.0, g/255.0, b/255.0)
        h, s, l = int(h * 360), int(s * 100), int(l * 100)

        # Store copy strings
        c_rgb = f"({r}, {g}, {b})"
        c_hex = hex_color
        c_hsl = f"({h}, {s}, {l})"

        # Update labels
        label_position.configure(text=f"X: {x:>5}   Y: {y:>5}")
        label_rgb.configure(text=f"RGB {r:>3},{g:>3},{b:>3}")
        label_hex.configure(text=f"HEX {hex_color}")
        label_hsl.configure(text=f"HSL {h:>3},{s:>3}%,{l:>3}%")

        # If you want the window to reflect the sampled color, uncomment:
        # root.configure(fg_color=hex_color)

        root.after(CAPTURE_INTERVAL_MS, tick)

    def on_key(event):
        """Handle 1/2/3 (also keypad variants) to copy values + beep."""
        ks = event.keysym  # e.g., '1', '2', '3', or 'KP_1', 'KP_2', 'KP_3'
        if ks in ("1", "KP_1"):
            copy_to_clipboard(c_rgb)
        elif ks in ("2", "KP_2"):
            copy_to_clipboard(c_hex)
        elif ks in ("3", "KP_3"):
            copy_to_clipboard(c_hsl)

    # Bind globally so any widget receives the keypress
    root.bind_all("<KeyPress>", on_key)

    # Ensure focus even with overrideredirect on macOS
    root.after(150, lambda: (root.lift(), root.focus_force()))

    # Start the safe update loop
    tick()

    root.mainloop()

if __name__ == "__main__":
    main()
