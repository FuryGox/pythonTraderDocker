import subprocess
import json


def restart_container(container_name: str) -> str:
    """Start an existing (stopped) container or restart a running one."""
    result = subprocess.run(
        ["docker", "start", container_name],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        raise RuntimeError(f"docker start failed: {result.stderr.strip()}")
    return result.stdout.strip()


def stop_container(container_id: str) -> str:
    result = subprocess.run(
        ["docker", "stop", container_id],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        raise RuntimeError(f"docker stop failed: {result.stderr.strip()}")
    return result.stdout.strip()


def get_containers_status() -> list[dict]:
    cmd = [
        "docker", "ps", "-a",
        "--filter", "name=mt4_bot_",
        "--filter", "name=mt5_bot_",
        "--filter", "name=ctrader_bot_",
        "--format", "{{json .}}",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"docker ps failed: {result.stderr.strip()}")

    containers = []
    for line in result.stdout.strip().splitlines():
        if line:
            containers.append(json.loads(line))
    return containers


def start_mt4_docker(account: str, password: str, server: str):
    container_name = f"mt4_bot_{account}"
    cmd = [
        "docker", "run", "-d",
        "--name", container_name,
        "mt4-beq-auto",
        account,
        password,
        server,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"MT4 docker failed: {result.stderr.strip()}")
    return result.stdout.strip()


def start_mt5_docker(account: str, password: str, server: str):
    container_name = f"mt5_bot_{account}"
    cmd = [
        "docker", "run", "-d",
        "--name", container_name,
        "mt5-beq-auto",
        account,
        password,
        server,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"MT5 docker failed: {result.stderr.strip()}")
    return result.stdout.strip()


def start_ctrader_docker(account: str, password: str, server: str):
    container_name = f"ctrader_bot_{account}"
    cmd = [
        "docker", "run", "-d",
        "--name", container_name,
        "ctrader-beq-auto",
        account,
        password,
        server,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"cTrader docker failed: {result.stderr.strip()}")
    return result.stdout.strip()
