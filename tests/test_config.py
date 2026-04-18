import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from linkvault.config import data_path_from_env, host_and_port_from_env, load_environment_file, parse_env_line


class ConfigTest(unittest.TestCase):
    def test_parse_env_line_handles_comments_quotes_and_plain_values(self):
        self.assertEqual(parse_env_line("# comment"), ("", ""))
        self.assertEqual(parse_env_line("LINKVAULT_PORT=3080"), ("LINKVAULT_PORT", "3080"))
        self.assertEqual(parse_env_line('LINKVAULT_HOST="0.0.0.0"'), ("LINKVAULT_HOST", "0.0.0.0"))
        self.assertEqual(parse_env_line("LINKVAULT_DATA_DIR='/var/lib/linkvault'"), ("LINKVAULT_DATA_DIR", "/var/lib/linkvault"))

    def test_load_environment_file_does_not_override_existing_env(self):
        with tempfile.TemporaryDirectory() as tmp:
            env_file = Path(tmp) / "linkvault.env"
            env_file.write_text("LINKVAULT_PORT=3080\nLINKVAULT_HOST=0.0.0.0\n", encoding="utf-8")
            with patch.dict(os.environ, {"LINKVAULT_ENV_FILE": str(env_file), "LINKVAULT_PORT": "9999"}, clear=True):
                loaded = load_environment_file()

                self.assertEqual(loaded, env_file)
                self.assertEqual(os.environ["LINKVAULT_PORT"], "9999")
                self.assertEqual(os.environ["LINKVAULT_HOST"], "0.0.0.0")

    def test_host_port_and_data_path_can_use_service_env(self):
        with patch.dict(
            os.environ,
            {"LINKVAULT_ADDR": "0.0.0.0:3080", "LINKVAULT_DATA_DIR": "/var/lib/linkvault"},
            clear=True,
        ):
            self.assertEqual(host_and_port_from_env(), ("0.0.0.0", 3080))
            self.assertEqual(data_path_from_env(), Path("/var/lib/linkvault/linkvault.sqlite3"))

    def test_explicit_data_path_wins(self):
        with patch.dict(
            os.environ,
            {"LINKVAULT_DATA": "/tmp/custom.sqlite3", "LINKVAULT_DATA_DIR": "/var/lib/linkvault"},
            clear=True,
        ):
            self.assertEqual(data_path_from_env(), Path("/tmp/custom.sqlite3"))


if __name__ == "__main__":
    unittest.main()
