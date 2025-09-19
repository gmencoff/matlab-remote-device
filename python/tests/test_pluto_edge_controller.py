import unittest, time
from unittest.mock import Mock, patch
from src.edge.edge_pluto_controller import EdgePlutoController
from src.commands.commands import PropertyCommand, MethodCommand

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

class TestEdgePlutoController(unittest.TestCase):
    def setUp(self):
        self.mock_pluto = MockPluto()
        self.mock_edge_service = Mock()
        self.controller = EdgePlutoController(self.mock_pluto, self.mock_edge_service, 0.1)
    
    def test_initial_config(self):
        """Test that the initial config contains all device properties."""
        # Verify that publish_config was called with the correct config
        self.mock_edge_service.publish_config.assert_called_once()
        
        # Get the config that was published
        published_config = self.mock_edge_service.publish_config.call_args[0][0]
        
        # Verify all properties are included
        self.assertEqual(published_config["rx_lo"], 2.4e9)
        self.assertEqual(published_config["sample_rate"], 30e6)
        self.assertEqual(published_config["rx_buffer_size"], 192)
        self.assertEqual(published_config["gain"], 50)
        
        # Verify no methods are included
        self.assertNotIn("rx", published_config)
        self.assertNotIn("tx", published_config)
    
    def test_property_command_success(self):
        """Test handling a property command that succeeds."""
        # Create a property command
        cmd = PropertyCommand("rx_lo", 2.5e9)
        
        # Handle the command
        ack = self.controller._handle_command(cmd)
        
        # Verify the device was updated
        self.assertEqual(self.mock_pluto.rx_lo, 2.5e9)
        
        # Verify the acknowledgment
        self.assertTrue(ack.ok)
        self.assertEqual(ack.value, 2.5e9)

        # Wait for config call
        time.sleep(0.3)
        
        # Verify config was updated and published
        self.mock_edge_service.publish_config.assert_called()
        latest_config = self.mock_edge_service.publish_config.call_args[0][0]
        self.assertEqual(latest_config["rx_lo"], 2.5e9)
    
    def test_property_command_nonexistent(self):
        """Test handling a property command for a nonexistent property."""
        # Create a property command for a nonexistent property
        cmd = PropertyCommand("nonexistent_property", 100)
        
        # Handle the command
        ack = self.controller._handle_command(cmd)
        
        # Verify the acknowledgment indicates failure
        self.assertFalse(ack.ok)
        self.assertIn("Property not found", ack.error)
        
        # Verify config was not republished (still at the initial publish)
        self.assertEqual(self.mock_edge_service.publish_config.call_count, 1)
    
    def test_method_command_success(self):
        """Test handling a method command that succeeds."""
        # Create a method command
        cmd = MethodCommand("rx", [512])
        
        # Handle the command
        ack = self.controller._handle_command(cmd)
        
        # Verify the acknowledgment
        self.assertTrue(ack.ok)
        self.assertEqual(len(ack.result), 512)  # Should be an array of 512 zeros
        
        # Wait for write updating
        time.sleep(0.3)

        # Verify config isn't changed
        self.assertEqual(self.mock_edge_service.publish_config.call_count, 1)
    
    def test_method_command_nonexistent(self):
        """Test handling a method command for a nonexistent method."""
        # Create a method command for a nonexistent method
        cmd = MethodCommand("nonexistent_method", [])
        
        # Handle the command
        ack = self.controller._handle_command(cmd)
        
        # Verify the acknowledgment indicates failure
        self.assertFalse(ack.ok)
        self.assertIn("Method not found", ack.error)

        # Wait for write updating
        time.sleep(0.3)
        
        # Verify config was not republished
        self.assertEqual(self.mock_edge_service.publish_config.call_count, 1)
    
    def test_update_config_from_device(self):
        """Test that _update_config_from_device correctly updates the config."""
        # Change a property on the device directly
        self.mock_pluto.rx_lo = 2.6e9

        # Wait for write updating
        time.sleep(0.3)
        
        # Verify the updated config was published
        latest_config = self.mock_edge_service.publish_config.call_args[0][0]
        self.assertEqual(latest_config["rx_lo"], 2.6e9)

if __name__ == "__main__":
    unittest.main()
