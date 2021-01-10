from pfo_passage_monitor.debugger import initialize_debugger_if_needed

initialize_debugger_if_needed()

# import debugpy
# debugpy.listen(("0.0.0.0", 5678))
# debugpy.wait_for_client()  # blocks execution until client is attached

from pfo_passage_monitor.main import app
app()
