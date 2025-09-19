
import unittest
from src.client.remote_pluto import RemotePluto
from mock_client_service import MockClientService

class TestRemotePluto(unittest.TestCase):
    def setUp(self):
        self.cfg = {
            "rx_lo": 2.4e9,
            "sample_rate": 30e6,
            "rx_buffer_size": 192,
        }
        self.client_service = MockClientService(self.cfg)
        self.pluto = RemotePluto(self.client_service)
    
    def test_init_and_refresh(self):
        # Test that the initial state is correctly loaded
        self.assertEqual(self.pluto.rx_lo, self.cfg["rx_lo"])
        self.assertEqual(self.pluto.sample_rate, self.cfg["sample_rate"])
        self.assertEqual(self.pluto.rx_buffer_size, self.cfg["rx_buffer_size"])
        
        # Test refresh
        self.client_service.update_config("rx_lo", 2.5e9)
        self.assertEqual(self.pluto.rx_lo, 2.5e9)
    
    def test_get_attribute(self):
        # Test getting existing attribute
        self.assertEqual(self.pluto.rx_lo, 2.4e9)
        
        # Test getting non-existent attribute
        with self.assertRaises(AttributeError):
            value = self.pluto.non_existent_attribute
    
    def test_set_attribute(self):
        # Test setting an attribute with a success ack
        self.client_service.send_property_ack = {"id":"123","ok":True,"ts":123,"value":2.5e9}
        self.pluto.rx_lo = 2.5e9
        self.assertEqual(self.pluto.rx_lo, 2.5e9)
        self.assertEqual(self.client_service.last_command["type"], "property")
        self.assertEqual(self.client_service.last_command["name"], "rx_lo")
        self.assertEqual(self.client_service.last_command["value"], 2.5e9)

    def test_set_attribute(self):
        # Test setting an attribute with a fail ack
        self.client_service.send_property_ack = {"id":"123","ok":False,"error":"this is an error","ts":123,"value":2.5e9}
        with self.assertRaises(RuntimeError) as context:
            self.pluto.rx_lo = 3.0e9
    
    def test_config_update_callback(self):
        # Test that the callback updates the state
        new_config = {
            "rx_lo": 2.6e9,
            "sample_rate": 40e6,
            "rx_buffer_size": 8192,
        }
        self.client_service.cfg = new_config
        self.client_service.send_config_change()
        
        self.assertEqual(self.pluto.rx_lo, 2.6e9)
        self.assertEqual(self.pluto.sample_rate, 40e6)
        self.assertEqual(self.pluto.rx_buffer_size, 8192)

if __name__ == "__main__":
    unittest.main()