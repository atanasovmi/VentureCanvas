"""Package entrypoint — ``py -m venturecanvas``."""

from .application import VentureCanvasApplication

# "__mp_main__" is included because NiceGUI/uvicorn re-imports this module in a
# worker subprocess; both names must trigger the app so reload mode still works.
if __name__ in {"__main__", "__mp_main__"}:
    VentureCanvasApplication().run()
