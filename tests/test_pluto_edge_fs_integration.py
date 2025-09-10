import os
import json
import tempfile
import shutil
import time
import unittest
from src.filesystem.file_system_edge_service import FileSystemEdgeService
from src.edge.edge_pluto_controller import EdgePlutoController
from src.filesystem.file_system_paths import FileSystemPaths
from src.commands.commands import PropertyCommand

class MockPluto:
    """Mock Pluto SDR for testing."""
    def __init__(self):
        self.rx_lo = 2.4e9
        self.sample_rate = 30e6
        self.rx_buffer_size = 192
        self.gain = 50
        
    def rx(self, num_samples=1024):
        """Mock rx method."""
        return [0] * num_samples
    
    def tx(self, samples):
        """Mock tx method."""
        return len(samples)

class TestEdgeIntegration(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for tests
        self.tmpdir = tempfile.mkdtemp()
        self.paths = FileSystemPaths(self.tmpdir)
        
        # Create the edge service
        self.edge_service = FileSystemEdgeService(self.tmpdir, poll_s=0.1)
        
        # Create the mock Pluto
        self.mock_pluto = MockPluto()
        
        # Create the controller
        self.controller = EdgePlutoController(self.mock_pluto, self.edge_service, poll_s=0.1)
        
        # Wait for initial setup
        time.sleep(0.2)
    
    def tearDown(self):
        # Clean up after test
        shutil.rmtree(self.tmpdir)
    
    def test_initial_config_published(self):
        """Test that the initial config is published correctly."""
        # Verify the config file was created
        self.assertTrue(os.path.exists(self.paths.config_path))
        
        # Read the config file and verify its contents
        with open(self.paths.config_path, "r") as f:
            config = json.load(f)
        
        # Verify all properties are included
        self.assertEqual(config["rx_lo"], 2.4e9)

    def test_property_command(self):
        """Test that the initial config is published correctly."""
        # Verify the initial pluto setting
        self.assertEqual(self.mock_pluto.rx_lo,2.4e9)
        
        # Create a property command
        cmd = PropertyCommand("rx_lo", 2.5e9)
        cmd_dict = cmd.to_dict()
        
        # Write the command to the commands file
        with open(self.paths.commands_path, "w") as f:
            f.write(json.dumps(cmd_dict) + "\n")
        
        # Wait for the command to be processed
        time.sleep(0.3)
        
        # Verify the command was received by the handler
        self.assertEqual(self.mock_pluto.rx_lo,2.5e9)
        
        # Verify the acknowledgment file was created
        ack_path = self.paths.get_ack_path(cmd.id)
        self.assertTrue(os.path.exists(ack_path))
        
        # Read the acknowledgment file and verify its contents
        with open(ack_path, "r") as f:
            ack_dict = json.load(f)
        
        self.assertEqual(ack_dict["id"], cmd.id)
        self.assertTrue(ack_dict["ok"])
        self.assertEqual(ack_dict["value"], 2.5e9)
        
        # Read the config file and verify its contents
        with open(self.paths.config_path, "r") as f:
            config = json.load(f)
        
        # Verify all properties are included
        self.assertEqual(config["rx_lo"], 2.5e9)
