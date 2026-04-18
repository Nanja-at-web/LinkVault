from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


DEFAULT_DATA_DIR = Path("data")
DEFAULT_ENV_FILE = Path("/etc/linkvault/linkvault.env")
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 3080


@dataclass(frozen=True)
class LinkVaultConfig:
    host: str
    port: int
    data_path: Path
    env_file: Path | None = None


def load_config() -> LinkVaultConfig:
    env_file = load_environment_file()
    host, port = host_and_port_from_env()
    return LinkVaultConfig(host=host, port=port, data_path=data_path_from_env(), env_file=env_file)


def load_environment_file() -> Path | None:
    path = configured_env_file()
    if not path or not path.exists():
        return None

    for line in path.read_text(encoding="utf-8").splitlines():
        key, value = parse_env_line(line)
        if key and key not in os.environ:
            os.environ[key] = value
    return path


def configured_env_file() -> Path | None:
    explicit = os.environ.get("LINKVAULT_ENV_FILE", "").strip()
    if explicit:
        return Path(explicit)

    local_env = Path(".env")
    if local_env.exists():
        return local_env
    return DEFAULT_ENV_FILE


def parse_env_line(line: str) -> tuple[str, str]:
    stripped = line.strip()
    if not stripped or stripped.startswith("#") or "=" not in stripped:
        return "", ""

    key, value = stripped.split("=", 1)
    key = key.strip()
    value = value.strip()
    if not key:
        return "", ""
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        value = value[1:-1]
    return key, value


def host_and_port_from_env() -> tuple[str, int]:
    addr = os.environ.get("LINKVAULT_ADDR", "").strip()
    if addr:
        host, port = parse_addr(addr)
    else:
        host = os.environ.get("LINKVAULT_HOST", DEFAULT_HOST).strip() or DEFAULT_HOST
        port = int(os.environ.get("LINKVAULT_PORT", str(DEFAULT_PORT)))

    if "LINKVAULT_HOST" in os.environ:
        host = os.environ["LINKVAULT_HOST"].strip() or DEFAULT_HOST
    if "LINKVAULT_PORT" in os.environ:
        port = int(os.environ["LINKVAULT_PORT"])
    return host, port


def parse_addr(value: str) -> tuple[str, int]:
    if ":" not in value:
        return value, DEFAULT_PORT
    host, port = value.rsplit(":", 1)
    return host or "0.0.0.0", int(port)


def data_path_from_env() -> Path:
    explicit_data = os.environ.get("LINKVAULT_DATA", "").strip()
    if explicit_data:
        return Path(explicit_data)

    data_dir = Path(os.environ.get("LINKVAULT_DATA_DIR", str(DEFAULT_DATA_DIR)).strip() or str(DEFAULT_DATA_DIR))
    return data_dir / "linkvault.sqlite3"
