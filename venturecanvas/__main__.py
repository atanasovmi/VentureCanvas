"""Package entrypoint — ``py -m venturecanvas``."""

from .application import VentureCanvasApplication

if __name__ in {"__main__", "__mp_main__"}:
    VentureCanvasApplication().run()
