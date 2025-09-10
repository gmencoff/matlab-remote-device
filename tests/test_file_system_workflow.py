import os
import json
import tempfile
import shutil
import time
import threading
import unittest
from src.filesystem.file_system_client_service import FileSystemClientService
from src.filesystem.file_system_edge_service import FileSystemEdgeService
from src.filesystem.file_system_paths import FileSystemPaths
from src.client.remote_pluto import RemotePluto
from src.edge.edge_pluto_controller import EdgePlutoController
from src.utils.utils import atomic_write_json

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

class TestEndToEndWorkflow(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for tests
        self.tmpdir = tempfile.mkdtemp()
        
        # Create the services with faster polling for tests
        self.client_service = FileSystemClientService(self.tmpdir, poll_s=0.1)
        self.edge_service = FileSystemEdgeService(self.tmpdir, poll_s=0.1)
        
        # Create the mock Pluto
        self.mock_pluto = MockPluto()
        
        # Create the controller
        self.controller = EdgePlutoController(self.mock_pluto, self.edge_service, poll_s=0.1)
        
        # Wait for initial config to be published by the controller
        time.sleep(0.3)
        
        # Create RemotePluto instance
        self.remote_pluto = RemotePluto(self.client_service)
        
        # Wait for initial config to be loaded by RemotePluto
        time.sleep(0.3)

    def tearDown(self):
        # Clean up after test
        shutil.rmtree(self.tmpdir)

    def test_initial_config_sync(self):
        """Test that initial configuration is correctly synchronized."""
        # Verify RemotePluto has the same properties as MockPluto
        self.assertEqual(self.remote_pluto.rx_lo, self.mock_pluto.rx_lo)
        self.assertEqual(self.remote_pluto.sample_rate, self.mock_pluto.sample_rate)
        self.assertEqual(self.remote_pluto.rx_buffer_size, self.mock_pluto.rx_buffer_size)
        self.assertEqual(self.remote_pluto.gain, self.mock_pluto.gain)

    def test_client_to_edge_property_update(self):
        """Test property updates from client to edge."""
        # Update a property on RemotePluto
        new_rx_lo = 2.5e9
        self.remote_pluto.rx_lo = new_rx_lo
        
        # Wait for the command to be processed
        time.sleep(0.5)
        
        # Verify the property was updated on MockPluto
        self.assertEqual(self.mock_pluto.rx_lo, new_rx_lo)

    def test_edge_to_client_property_update(self):
        """Test property updates from edge to client."""
        # Update a property on MockPluto
        new_sample_rate = 40e6
        self.mock_pluto.sample_rate = new_sample_rate
        
        # Wait for the config change to be detected
        time.sleep(0.5)
        
        # Verify the property was updated on RemotePluto
        self.assertEqual(self.remote_pluto.sample_rate, new_sample_rate)

    def test_multiple_property_updates(self):
        """Test multiple property updates in both directions."""
        # Update properties on RemotePluto
        self.remote_pluto.rx_lo = 2.6e9
        self.remote_pluto.rx_buffer_size = 256
        
        # Wait for the commands to be processed
        time.sleep(0.5)
        
        # Verify properties were updated on MockPluto
        self.assertEqual(self.mock_pluto.rx_lo, 2.6e9)
        self.assertEqual(self.mock_pluto.rx_buffer_size, 256)
        
        # Update properties on MockPluto
        self.mock_pluto.gain = 60
        self.mock_pluto.sample_rate = 45e6
        
        # Wait for the config change to be detected
        time.sleep(0.5)
        
        # Verify properties were updated on RemotePluto
        self.assertEqual(self.remote_pluto.gain, 60)
        self.assertEqual(self.remote_pluto.sample_rate, 45e6)
        
        # Verify all properties match between RemotePluto and MockPluto
        self.assertEqual(self.remote_pluto.rx_lo, self.mock_pluto.rx_lo)
        self.assertEqual(self.remote_pluto.sample_rate, self.mock_pluto.sample_rate)
        self.assertEqual(self.remote_pluto.rx_buffer_size, self.mock_pluto.rx_buffer_size)
        self.assertEqual(self.remote_pluto.gain, self.mock_pluto.gain)

    def test_concurrent_bidirectional_updates(self):
        """Test concurrent property updates in both directions."""
        
        self.remote_pluto.rx_lo = 2.7e9
        time.sleep(0.2)
        self.remote_pluto.rx_buffer_size = 512
    
        time.sleep(0.1)  # Slight delay to ensure interleaved execution
        self.mock_pluto.gain = 70
        
        time.sleep(0.2)
        self.mock_pluto.sample_rate = 50e6
        
        # Wait for all updates to be processed
        time.sleep(1.0)
        
        # Verify all properties match between RemotePluto and MockPluto
        self.assertEqual(self.remote_pluto.rx_lo, self.mock_pluto.rx_lo)
        self.assertEqual(self.remote_pluto.sample_rate, self.mock_pluto.sample_rate)
        self.assertEqual(self.remote_pluto.rx_buffer_size, self.mock_pluto.rx_buffer_size)
        self.assertEqual(self.remote_pluto.gain, self.mock_pluto.gain)
        
        # Verify specific values
        self.assertEqual(self.remote_pluto.rx_lo, 2.7e9)
        self.assertEqual(self.remote_pluto.rx_buffer_size, 512)
        self.assertEqual(self.remote_pluto.gain, 70)
        self.assertEqual(self.remote_pluto.sample_rate, 50e6)

if __name__ == "__main__":
    unittest.main()
