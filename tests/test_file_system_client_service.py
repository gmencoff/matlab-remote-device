import os, json, tempfile, shutil, time, threading, unittest
from src.filesystem.file_system_client_service import FileSystemClientService
from src.filesystem.file_system_paths import FileSystemPaths
from src.utils.utils import atomic_write_json

class TestFileSystemClientService(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for tests
        self.tmpdir = tempfile.mkdtemp()
        self.service = FileSystemClientService(self.tmpdir, poll_s=0.1)
        self.paths = FileSystemPaths(self.tmpdir)

    def tearDown(self):
        # Clean up after test
        shutil.rmtree(self.tmpdir)

    def test_send_command_and_ack(self):
        cmd = {"id": "123", "type": "property", "name": "sample_rate", "value": 2000000}
        ack_path = os.path.join(self.tmpdir, "commands", "acks", "123.json")

        def delayed_ack():
            time.sleep(0.2)
            with open(ack_path, "w") as f:
                json.dump({"id": "123", "ok": True, "ts": time.time(), "value": 2000000}, f)

        threading.Thread(target=delayed_ack).start()

        ack = self.service.send_command(cmd, timeout=2.0)
        self.assertTrue(ack["ok"])
        self.assertEqual(ack["value"], 2000000)

    def test_subscribe_config(self):
        config_path = self.paths.config_path

        updates = []
        def on_change(cfg):
            updates.append(cfg)

        self.service.subscribe_config(on_change)

        atomic_write_json(config_path, {"sample_rate": 2000000})
        time.sleep(0.3)
        atomic_write_json(config_path, {"sample_rate": 4000000})
        time.sleep(0.3)

        self.assertIn({"sample_rate": 2000000}, updates)
        self.assertIn({"sample_rate": 4000000}, updates)

    def test_multiple_commands_and_acks(self):
        commands = [
            {"id": "c1", "type": "property", "name": "rx_lo", "value": 915000000},
            {"id": "c2", "type": "property", "name": "sample_rate", "value": 2000000},
            {"id": "c3", "type": "method", "name": "rx", "args": [], "kwargs": {}},
        ]

        def make_ack(cmd):
            ack_path = os.path.join(self.tmpdir, "commands", "acks", f"{cmd['id']}.json")
            time.sleep(0.1)
            with open(ack_path, "w") as f:
                json.dump({"id": cmd["id"], "ok": True, "ts": time.time(), "payload": {"echo": cmd}}, f)

        # Fire off threads that will produce acks
        for cmd in commands:
            threading.Thread(target=make_ack, args=(cmd,)).start()

        # Send commands sequentially and verify acks are matched by ID
        results = {}
        for cmd in commands:
            ack = self.service.send_command(cmd, timeout=2.0)
            results[cmd["id"]] = ack

        self.assertEqual(set(results.keys()), {"c1", "c2", "c3"})
        for cid, ack in results.items():
            self.assertTrue(ack["ok"])
            self.assertEqual(ack["id"], cid)
            # echo payload check
            self.assertIn("payload", ack)
            self.assertEqual(ack["payload"]["echo"]["id"], cid)

    def test_send_command_timeout(self):
        """Test that send_command raises TimeoutError when no ack is received within timeout."""
        cmd = {"id": "timeout_test", "type": "property", "name": "sample_rate", "value": 2000000}
        
        # Use a very short timeout to make the test run quickly
        with self.assertRaises(TimeoutError) as context:
            self.service.send_command(cmd, timeout=0.2)
        
        # Verify the error message contains the command ID
        self.assertIn("timeout_test", str(context.exception))
        
        # Verify the command was actually written to the commands file
        with open(self.paths.commands_path, "r") as f:
            commands = f.readlines()
            self.assertTrue(any("timeout_test" in cmd for cmd in commands))


if __name__ == "__main__":
    unittest.main()
