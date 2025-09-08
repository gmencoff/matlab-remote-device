import os, json, tempfile, shutil, time, threading, unittest
from src.services.file_system_client_service import FileSystemClientService
from src.client.remote_pluto import RemotePluto
from src.utils.utils import atomic_write_json
from src.commands.commands import PropertyAck

class TestRemotePlutoIntegration(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for tests
        self.tmpdir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.tmpdir, "config", "config.json")
        self.acks_dir = os.path.join(self.tmpdir, "commands", "acks")
        
        # Create initial config
        self.initial_config = {
            "rx_lo": 2.4e9,
            "sample_rate": 30e6,
            "rx_buffer_size": 192,
        }
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        atomic_write_json(self.config_path, self.initial_config)
        
        # Create client service with faster polling for tests
        self.client_service = FileSystemClientService(self.tmpdir, poll_s=0.1)
        
        # Create RemotePluto instance
        self.pluto = RemotePluto(self.client_service)
        
        # Wait for initial config to be loaded
        time.sleep(0.2)

    def tearDown(self):
        # Clean up after test
        shutil.rmtree(self.tmpdir)

    def test_initial_config_loading(self):
        """Test that RemotePluto correctly loads the initial configuration."""
        self.assertEqual(self.pluto.rx_lo, self.initial_config["rx_lo"])
        self.assertEqual(self.pluto.sample_rate, self.initial_config["sample_rate"])
        self.assertEqual(self.pluto.rx_buffer_size, self.initial_config["rx_buffer_size"])

    def test_property_change_success(self):
        """Test that property changes are correctly sent and processed with successful acks."""
        # Set up a thread to simulate the server responding with a success ack
        def respond_with_success_ack():
            # Wait for command file to be created
            cmd_path = self.client_service.commands_path
            while not os.path.exists(cmd_path):
                time.sleep(0.05)
                
            # Read the command
            with open(cmd_path, "r") as f:
                cmd_line = f.readline().strip()
                cmd = json.loads(cmd_line)
                
            # Create a success ack
            ack_path = os.path.join(self.acks_dir, f"{cmd['id']}.json")
            ack_data = {
                "id": cmd["id"],
                "ok": True,
                "ts": time.time(),
                "value": cmd["value"]
            }
            atomic_write_json(ack_path, ack_data)

        # Start the response thread
        thread = threading.Thread(target=respond_with_success_ack)
        thread.daemon = True
        thread.start()
        
        # Change a property
        new_rx_lo = 2.5e9
        self.pluto.rx_lo = new_rx_lo
        
        # Verify the property was updated
        self.assertEqual(self.pluto.rx_lo, new_rx_lo)

    def test_property_change_failure(self):
        """Test that property changes handle failure acks correctly."""
        # Set up a thread to simulate the server responding with a failure ack
        def respond_with_failure_ack():
            # Wait for command file to be created
            cmd_path = self.client_service.commands_path
            while not os.path.exists(cmd_path):
                time.sleep(0.05)
                
            # Read the command
            with open(cmd_path, "r") as f:
                cmd_line = f.readline().strip()
                cmd = json.loads(cmd_line)
                
            # Create a failure ack
            ack_path = os.path.join(self.acks_dir, f"{cmd['id']}.json")
            ack_data = {
                "id": cmd["id"],
                "ok": False,
                "ts": time.time(),
                "error": "Value out of range"
            }
            atomic_write_json(ack_path, ack_data)

        # Start the response thread
        thread = threading.Thread(target=respond_with_failure_ack)
        thread.daemon = True
        thread.start()
        
        # Try to change a property and expect a RuntimeError
        with self.assertRaises(RuntimeError) as context:
            self.pluto.rx_lo = 3.0e9
            
        # Verify the error message
        self.assertIn("Failed to set rx_lo", str(context.exception))
        
        # Verify the property was not updated
        self.assertEqual(self.pluto.rx_lo, self.initial_config["rx_lo"])

    def test_config_update_from_file(self):
        """Test that RemotePluto updates when the config file changes."""
        # Update the config file
        new_config = {
            "rx_lo": 2.6e9,
            "sample_rate": 40e6,
            "rx_buffer_size": 8192,
            "new_property": "test_value"
        }
        atomic_write_json(self.config_path, new_config)
        
        # Wait for the config change to be detected
        time.sleep(0.3)
        
        # Verify the properties were updated
        self.assertEqual(self.pluto.rx_lo, new_config["rx_lo"])
        self.assertEqual(self.pluto.sample_rate, new_config["sample_rate"])
        self.assertEqual(self.pluto.rx_buffer_size, new_config["rx_buffer_size"])
        self.assertEqual(self.pluto.new_property, new_config["new_property"])

    def test_multiple_property_changes(self):
        """Test changing multiple properties in sequence."""
        def respond_with_success_ack():
            cmd_path = self.client_service.commands_path
            
            # Keep checking for new commands
            last_size = 0
            while True:
                if os.path.exists(cmd_path):
                    current_size = os.path.getsize(cmd_path)
                    if current_size > last_size:
                        with open(cmd_path, "r") as f:
                            lines = f.readlines()
                            # Process only the new command
                            cmd_line = lines[-1].strip()
                            cmd = json.loads(cmd_line)
                            
                        # Create a success ack
                        ack_path = os.path.join(self.acks_dir, f"{cmd['id']}.json")
                        ack_data = {
                            "id": cmd["id"],
                            "ok": True,
                            "ts": time.time(),
                            "value": cmd["value"]
                        }
                        atomic_write_json(ack_path, ack_data)
                        last_size = current_size
                time.sleep(0.05)
                
                # Break after a reasonable time to avoid infinite loop in tests
                if threading.current_thread().name == "test_thread" and not threading.current_thread().is_alive():
                    break

        # Start the response thread
        thread = threading.Thread(target=respond_with_success_ack, name="test_thread")
        thread.daemon = True
        thread.start()
        
        # Change multiple properties
        self.pluto.rx_lo = 2.7e9
        self.pluto.sample_rate = 50e6
        self.pluto.rx_buffer_size = 4096
        
        # Verify all properties were updated
        self.assertEqual(self.pluto.rx_lo, 2.7e9)
        self.assertEqual(self.pluto.sample_rate, 50e6)
        self.assertEqual(self.pluto.rx_buffer_size, 4096)
        
        # Signal the thread to stop
        thread._is_stopped = True

if __name__ == "__main__":
    unittest.main()
