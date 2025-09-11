from src.edge.edge_pluto_controller import EdgePlutoController
from src.filesystem.file_system_edge_service import FileSystemEdgeService

def startEdgeController(pluto,path):
    service = FileSystemEdgeService(path)
    return EdgePlutoController(pluto, service)
