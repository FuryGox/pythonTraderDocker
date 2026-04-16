from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from enum import Enum
from docker_runner import start_mt4_docker, start_mt5_docker, start_ctrader_docker, get_containers_status, stop_container, restart_container
from db import init_db, save_account_container, get_account_container

app = FastAPI()

init_db()


class Platform(str, Enum):
    mt4 = "mt4"
    mt5 = "mt5"
    ctrader = "ctrader"


class RunRequest(BaseModel):
    account: str
    password: str
    server: str
    platform: Platform


@app.post("/api/run")
def run_platform(payload: RunRequest):
    account = payload.account
    password = payload.password
    server = payload.server
    platform = payload.platform

    try:
        existing = get_account_container(account, platform)
        if existing:
            restart_container(existing["container_name"])
            return {
                "status": "restarted",
                "platform": platform,
                "account": account,
                "server": existing["server"],
                "container": existing["container_name"],
            }

        if platform == Platform.mt4:
            container_name = f"mt4_bot_{account}"
            start_mt4_docker(account, password, server)
        elif platform == Platform.mt5:
            container_name = f"mt5_bot_{account}"
            start_mt5_docker(account, password, server)
        elif platform == Platform.ctrader:
            container_name = f"ctrader_bot_{account}"
            start_ctrader_docker(account, password, server)

        save_account_container(account, platform, server, container_name)

        return {
            "status": "started",
            "platform": platform,
            "account": account,
            "server": server,
            "container": container_name,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/status")
def get_status():
    try:
        containers = get_containers_status()
        return {"containers": containers}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class StopRequest(BaseModel):
    id: str


@app.post("/api/stop")
def stop_container_route(payload: StopRequest):
    try:
        stopped = stop_container(payload.id)
        return {"status": "stopped", "container": stopped}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
