import threading
import time
from typing import Dict, Any, Callable, Optional
import firebase_admin
from firebase_admin import credentials, firestore
from src.services.edge_service import EdgeService
from src.commands.commands import Command, Ack, decode_command


class FirebaseEdgeService(EdgeService):
    """
    Firebase-based edge service.
    Uses Firestore to publish config and receive commands.
    Counterpart to FirebaseClientService.
    """

    def __init__(self, device_id: str, 
                 credential_path: Optional[str] = None,
                 project_id: Optional[str] = None):
        """
        Initialize Firebase Edge Service.
        
        Args:
            device_id: Unique identifier for this device
            credential_path: Path to Firebase service account key JSON file
            project_id: Firebase project ID (optional, can be inferred from credentials)
        """
        self.device_id = device_id
        
        # Initialize Firebase Admin SDK if not already initialized
        if not firebase_admin._apps:
            if credential_path:
                cred = credentials.Certificate(credential_path)
                if project_id:
                    firebase_admin.initialize_app(cred, {'projectId': project_id})
                else:
                    firebase_admin.initialize_app(cred)
            else:
                # Use default credentials (e.g., from environment or metadata server)
                firebase_admin.initialize_app()
        
        self.db = firestore.client()
        
        # Collection paths
        self.config_collection = "devices"
        self.commands_collection = f"commands/{device_id}/commands"
        self.acks_collection = f"acks/{device_id}/acks"

    # ---- EdgeService API ----

    def publish_config(self, config: Dict[str, Any]) -> None:
        """Write the current configuration to Firestore."""
        try:
            config_doc_ref = self.db.collection(self.config_collection).document(self.device_id)
            config_doc_ref.set(config)
            print(f"Published config for device {self.device_id}")
        except Exception as e:
            print(f"Error publishing config: {e}")
            raise

    def subscribe_commands(self, on_command: Callable[[Command], Ack]) -> None:
        """Listen for new command documents and invoke callback for each."""
        def command_listener():
            print(f"Starting command listener for device {self.device_id}")
            
            # Listen for new documents in the commands collection
            commands_ref = self.db.collection(self.commands_collection)
            
            def on_snapshot(col_snapshot, changes, read_time):
                """Handle real-time updates to the commands collection."""
                for change in changes:
                    if change.type.name == 'ADDED':  # New command
                        try:
                            command_doc = change.document
                            command_data = command_doc.to_dict()
                            
                            # Extract command from the document structure
                            # Based on sendCommand.ts, the structure is:
                            # { deviceId, commandId, command, timestamp }
                            if 'command' in command_data:
                                cmd_dict = command_data['command']
                                cmd = decode_command(cmd_dict)
                                
                                # Process command and get acknowledgment
                                ack = on_command(cmd)
                                
                                # Write acknowledgment to Firestore
                                ack_doc_ref = self.db.collection(self.acks_collection).document(cmd.id)
                                ack_data = {
                                    'deviceId': self.device_id,
                                    'commandId': cmd.id,
                                    'response': ack.to_dict(),
                                    'timestamp': int(time.time() * 1000)  # milliseconds
                                }
                                ack_doc_ref.set(ack_data)
                                
                                print(f"Processed command {cmd.id} and sent ack")
                                
                        except Exception as e:
                            print(f"Error processing command: {e}")
            
            # Start listening for real-time updates
            col_watch = commands_ref.on_snapshot(on_snapshot)
            
            # Keep the listener alive
            try:
                while True:
                    time.sleep(0.1)
            except KeyboardInterrupt:
                col_watch.unsubscribe()
                print("Command listener stopped")

        # Start the command listener in a separate thread
        threading.Thread(target=command_listener, daemon=True).start()
