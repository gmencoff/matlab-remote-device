from src.client.remote_pluto import RemotePluto
from src.filesystem.file_system_client_service import FileSystemClientService

def startRemotePluto(path):
    service = FileSystemClientService(path)
    return RemotePluto(service)
