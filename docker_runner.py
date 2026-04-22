import json
import os
import subprocess


BASE_DIR = os.path.dirname(__file__)
CTRADER_BOT_DIR = os.path.join(BASE_DIR, "bot")
CTRADER_BOT_FILE = "lumir-ctrader.algo"
CTRADER_BOT_MOUNT_DIR = "/mnt/Robots"


def _get_ctrader_bot_host_path() -> str:
    bot_path = os.path.join(CTRADER_BOT_DIR, CTRADER_BOT_FILE)
    if not os.path.exists(bot_path):
        raise RuntimeError(f"cTrader bot file not found: {bot_path}")
    return bot_path


def _write_ctrader_password_file(account: str, password: str) -> str:
    os.makedirs(CTRADER_BOT_DIR, exist_ok=True)

    password_file_path = os.path.join(CTRADER_BOT_DIR, f"ctrader-{account}.pwd")
    with open(password_file_path, "w", encoding="utf-8", newline="") as password_file:
        password_file.write(password)

    return password_file_path


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


def remove_container(container_id: str) -> str:
    result = subprocess.run(
        ["docker", "rm", "-f", container_id],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        raise RuntimeError(f"docker rm failed: {result.stderr.strip()}")
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


def start_ctrader_docker(
    account: str,
    password: str,
    ctrader_id: str,
    symbol: str = "EURUSD",
    period: str = "H1",
):
    container_name = f"ctrader_bot_{account}"
    _get_ctrader_bot_host_path()
    password_file_path = _write_ctrader_password_file(account, password)
    robots_dir = os.path.abspath(CTRADER_BOT_DIR)
    algo_container_path = f"{CTRADER_BOT_MOUNT_DIR}/{CTRADER_BOT_FILE}"
    password_container_path = f"{CTRADER_BOT_MOUNT_DIR}/{os.path.basename(password_file_path)}"

    cmd = [
        "docker", "run", "-d", "-it",
        "--name", container_name,
        "--mount", f"type=bind,src={robots_dir},dst={CTRADER_BOT_MOUNT_DIR}",
        "-e", f"CTID={ctrader_id}",
        "-e", f"PWD-FILE={password_container_path}",
        "-e", f"ACCOUNT={account}",
        "-e", f"SYMBOL={symbol}",
        "-e", f"PERIOD={period}",
        "ghcr.io/spotware/ctrader-console:latest",
        "run",
        algo_container_path,
        "--environment-variables",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"cTrader docker failed: {result.stderr.strip()}")
    return result.stdout.strip()
