from src.client.remote_pluto import RemotePluto
from src.filesystem.file_system_client_service import FileSystemClientService

def startClient():
    local_dir = "C:\\Users\\gmencoff\\OneDrive - MathWorks\\PlutoSync\\LiEWnBFVcn"
    client_service = FileSystemClientService(local_dir)
    return RemotePluto(client_service=client_service)