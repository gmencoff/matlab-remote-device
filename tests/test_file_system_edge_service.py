import os
import json
import tempfile
import shutil
import time
import unittest
from src.filesystem.file_system_edge_service  import FileSystemEdgeService
from src.commands.commands import PropertyCommand, MethodCommand, Ack, PropertyAck
from src.filesystem.file_system_paths import FileSystemPaths

class TestFileSystemEdgeService(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for tests
        self.tmpdir = tempfile.mkdtemp()
        self.paths = FileSystemPaths(self.tmpdir)

        # Create callbacks for post-write and pre-read operations
        def post_write_callback(filepath):
            self.post_write_calls.append(filepath)
            
        def pre_read_callback(filepath):
            self.pre_read_calls.append(filepath)

        # Store callback calls
        self.post_write_calls = []
        self.pre_read_calls = []

        # Create service
        self.service = FileSystemEdgeService(self.tmpdir, poll_s=0.1,post_write_file_cb=post_write_callback,pre_read_file_cb=pre_read_callback)
    
    def tearDown(self):
        # Clean up after test
        shutil.rmtree(self.tmpdir)
    
    def test_publish_config(self):
        """Test that publish_config writes the config to the correct file."""
        # Create a test config
        test_config = {
            "rx_lo": 2.4e9,
            "sample_rate": 30e6,
            "rx_buffer_size": 192
        }
        
        # Publish the config
        self.service.publish_config(test_config)
        
        # Verify the config file was created
        self.assertTrue(os.path.exists(self.paths.config_path))

        # Verify callback was called
        self.assertEqual(len(self.post_write_calls), 1)
        self.assertEqual(self.post_write_calls[0], self.paths.config_path)
        
        # Read the config file and verify its contents
        with open(self.paths.config_path, "r") as f:
            saved_config = json.load(f)
        
        self.assertEqual(saved_config, test_config)
    
    def test_subscribe_commands_property(self):
        """Test that subscribe_commands correctly processes property commands."""
        # Create a command handler that returns a success acknowledgment
        def command_handler(cmd):
            self.received_command = cmd
            return PropertyAck(cmd.id, True, value=cmd.value)
        
        # Subscribe to commands
        self.service.subscribe_commands(command_handler)
        
        # Create a property command
        cmd = PropertyCommand("rx_lo", 2.5e9)
        cmd_dict = cmd.to_dict()
        
        # Write the command to the commands file
        with open(self.paths.commands_path, "w") as f:
            f.write(json.dumps(cmd_dict) + "\n")
        
        # Wait for the command to be processed
        time.sleep(0.3)

        # Verify that the pre-read callback was called with commands path
        self.assertTrue(len(self.pre_read_calls) > 0)
        self.assertEqual(self.pre_read_calls[0], self.paths.commands_path)
        
        # Verify the command was received by the handler
        self.assertEqual(self.received_command.type, "property")
        self.assertEqual(self.received_command.name, "rx_lo")
        self.assertEqual(self.received_command.value, 2.5e9)
        
        # Verify the acknowledgment file was created
        ack_path = self.paths.get_ack_path(cmd.id)
        self.assertTrue(os.path.exists(ack_path))
        
        # Read the acknowledgment file and verify its contents
        with open(ack_path, "r") as f:
            ack_dict = json.load(f)

        # Verify that the write callback was called with ack path
        self.assertEqual(len(self.post_write_calls), 1)
        self.assertEqual(self.post_write_calls[0], ack_path)
        
        self.assertEqual(ack_dict["id"], cmd.id)
        self.assertTrue(ack_dict["ok"])
        self.assertEqual(ack_dict["value"], 2.5e9)
    
    def test_subscribe_commands_method(self):
        """Test that subscribe_commands correctly processes method commands."""
        # Create a command handler that returns a success acknowledgment
        def command_handler(cmd):
            self.received_command = cmd
            return PropertyAck(cmd.id, True, value="method_result")
        
        # Subscribe to commands
        self.service.subscribe_commands(command_handler)
        
        # Create a method command
        cmd = MethodCommand("rx", [512])
        cmd_dict = cmd.to_dict()
        
        # Write the command to the commands file
        with open(self.paths.commands_path, "w") as f:
            f.write(json.dumps(cmd_dict) + "\n")
        
        # Wait for the command to be processed
        time.sleep(0.3)
        
        # Verify the command was received by the handler
        self.assertEqual(self.received_command.type, "method")
        self.assertEqual(self.received_command.name, "rx")
        self.assertEqual(self.received_command.args, [512])
        
        # Verify the acknowledgment file was created
        ack_path = self.paths.get_ack_path(cmd.id)
        self.assertTrue(os.path.exists(ack_path))
    
    def test_multiple_commands(self):
        """Test processing multiple commands in sequence."""
        # Create a list to store received commands
        received_commands = []
        
        # Create a command handler that stores commands and returns success acknowledgments
        def command_handler(cmd):
            received_commands.append(cmd)
            return PropertyAck(cmd.id, True, value=cmd.value if hasattr(cmd, "value") else None)
        
        # Subscribe to commands
        self.service.subscribe_commands(command_handler)
        
        # Create multiple commands
        cmd1 = PropertyCommand("rx_lo", 2.5e9)
        cmd2 = PropertyCommand("sample_rate", 40e6)
        cmd3 = MethodCommand("rx", [1024])
        
        # Write the commands to the commands file
        with open(self.paths.commands_path, "w") as f:
            f.write(json.dumps(cmd1.to_dict()) + "\n")
            f.write(json.dumps(cmd2.to_dict()) + "\n")
            f.write(json.dumps(cmd3.to_dict()) + "\n")
        
        # Wait for the commands to be processed
        time.sleep(0.5)
        
        # Verify all commands were received
        self.assertEqual(len(received_commands), 3)
        
        # Verify the commands were received in order
        self.assertEqual(received_commands[0].type, "property")
        self.assertEqual(received_commands[0].name, "rx_lo")
        self.assertEqual(received_commands[0].value, 2.5e9)
        
        self.assertEqual(received_commands[1].type, "property")
        self.assertEqual(received_commands[1].name, "sample_rate")
        self.assertEqual(received_commands[1].value, 40e6)
        
        self.assertEqual(received_commands[2].type, "method")
        self.assertEqual(received_commands[2].name, "rx")
        self.assertEqual(received_commands[2].args, [1024])
        
        # Verify acknowledgment files were created for all commands
        for cmd in [cmd1, cmd2, cmd3]:
            ack_path = self.paths.get_ack_path(cmd.id)
            self.assertTrue(os.path.exists(ack_path))
    
    def test_invalid_command_json(self):
        """Test handling of invalid JSON in the commands file."""
        # Create a flag to track if the command handler was called
        self.handler_called = False
        
        # Create a command handler
        def command_handler(cmd):
            self.handler_called = True
            return PropertyAck(cmd.id, True)
        
        # Subscribe to commands
        self.service.subscribe_commands(command_handler)
        
        # Write invalid JSON to the commands file
        with open(self.paths.commands_path, "w") as f:
            f.write("this is not valid JSON\n")
        
        # Wait for the command to be processed
        time.sleep(0.3)
        
        # Verify the handler was not called
        self.assertFalse(self.handler_called)

if __name__ == "__main__":
    unittest.main()
