from random_dirname import random_dirname
from mock_pluto import MockPluto
from src.edge.edge_pluto_controller import EdgePlutoController
from src.onedrive.one_drive_edge_service import OneDriveEdgeService

def startEdgeController(base_local_path,base_onedrive_path):
    dirname = random_dirname(10)
    local_path = base_local_path + "\\" + dirname
    onedrive_path = base_onedrive_path + "\\" + dirname
    pluto = MockPluto()
    service = OneDriveEdgeService(local_folder=local_path,onedrive_folder=onedrive_path)
    return EdgePlutoController(pluto, service)
