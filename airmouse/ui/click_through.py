def make_click_through(window) -> None:
    """Windows only: make `window` ignore mouse input. Silently skipped elsewhere."""
    try:
        import ctypes

        window.update_idletasks()
        user32 = ctypes.windll.user32
        hwnd = user32.GetParent(window.winfo_id())
        GWL_EXSTYLE = -20
        WS_EX_LAYERED = 0x80000
        WS_EX_TRANSPARENT = 0x20
        style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        user32.SetWindowLongW(
            hwnd, GWL_EXSTYLE, style | WS_EX_LAYERED | WS_EX_TRANSPARENT
        )
    except Exception:
        pass
