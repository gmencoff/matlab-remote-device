from start_edge_controller import startEdgeController
import time

def startRaspiEdge():
    local = "/home/gmencoff/PlutoSync"
    onedrive = "OneDrive:PlutoSync"
    return startEdgeController(local,onedrive)

ec = startRaspiEdge()

while True:
    time.sleep(0.1)