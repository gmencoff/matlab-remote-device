import time
from adi import ad936x
from interfaces import ConfigSync, CommandService

class PlutoEdgeController:
    def __init__(self, pluto, cfg_sync: ConfigSync, cmd_service: CommandService):
        self.pluto = pluto
        self.cfg_sync = cfg_sync
        self.cmd_service = cmd_service

    def _snapshot_config(self):
        return {
            "rx_lo": self.pluto.rx_lo,
            "sample_rate": self.pluto.sample_rate,
            "rx_buffer_size": self.pluto.rx_buffer_size,
            "gain_control_mode": self.pluto.gain_control_mode,
            "rx_hardwaregain": self.pluto.rx_hardwaregain,
            "last_updated": time.time(),
        }

    def run(self):
        self.cfg_sync.write_config(self._snapshot_config())

        def handler(cmd):
            if cmd["type"] == "property":
                try:
                    setattr(self.pluto, cmd["name"], cmd["value"])
                    self.cfg_sync.write_config(self._snapshot_config())
                    result = {"ok": True, "value": getattr(self.pluto, cmd["name"])}
                except Exception as e:
                    result = {"ok": False, "error": str(e)}
            elif cmd["type"] == "method":
                try:
                    method = getattr(self.pluto, cmd["name"])
                    val = method(*cmd.get("args", []), **cmd.get("kwargs", {}))
                    self.cfg_sync.write_config(self._snapshot_config())
                    result = {"ok": True, "result": str(val)}
                except Exception as e:
                    result = {"ok": False, "error": str(e)}
            else:
                result = {"ok": False, "error": f"Unknown type {cmd['type']}"}

            self.cmd_service.ack_command(cmd["id"], result)

        self.cmd_service.run(handler)
