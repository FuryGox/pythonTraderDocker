import json

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, model_validator
from enum import Enum
from docker_runner import start_mt4_docker, start_mt5_docker, start_ctrader_docker, get_containers_status, stop_container, restart_container, remove_container
from db import init_db, save_account_container, get_account_container, delete_account_container_by_name

app = FastAPI()

init_db()


class Platform(str, Enum):
    mt4 = "mt4"
    mt5 = "mt5"
    ctrader = "ctrader"


class JsonStringCompatibleModel(BaseModel):
    @model_validator(mode="before")
    @classmethod
    def parse_json_string_body(cls, value):
        if not isinstance(value, str):
            return value

        try:
            parsed = json.loads(value)
        except json.JSONDecodeError as exc:
            raise ValueError("Request body must be a valid JSON object") from exc

        if not isinstance(parsed, dict):
            raise ValueError("Request body must decode to a JSON object")

        return parsed


class RunRequest(JsonStringCompatibleModel):
    account: str
    password: str
    platform: Platform
    server: str | None = None
    ctrader_id: str | None = None
    symbol: str = "EURUSD"
    period: str = "H1"

    @model_validator(mode="after")
    def validate_platform_fields(self):
        if self.platform in {Platform.mt4, Platform.mt5} and not self.server:
            raise ValueError("server is required for mt4 and mt5")

        if self.platform == Platform.ctrader and not self.ctrader_id:
            raise ValueError("ctrader_id is required for ctrader")

        return self


def build_run_response(
    status: str,
    platform: Platform,
    account: str,
    container_name: str,
    server: str | None = None,
    ctrader_id: str | None = None,
    symbol: str | None = None,
    period: str | None = None,
):
    response = {
        "status": status,
        "platform": platform,
        "account": account,
        "container": container_name,
    }

    if platform == Platform.ctrader:
        response["ctrader_id"] = ctrader_id
        response["symbol"] = symbol
        response["period"] = period
    else:
        response["server"] = server

    return response


async def parse_request_model(request: Request, model_class: type[JsonStringCompatibleModel]):
    try:
        payload = await request.json()
    except json.JSONDecodeError:
        raw_body = (await request.body()).decode("utf-8").strip()
        if not raw_body:
            raise HTTPException(status_code=400, detail="Request body is required")
        payload = raw_body

    try:
        return model_class.model_validate(payload)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post("/api/run")
async def run_platform(request: Request):
    payload = await parse_request_model(request, RunRequest)
    account = payload.account
    password = payload.password
    platform = payload.platform

    try:
        existing = get_account_container(account, platform)
        if existing:
            restart_container(existing["container_name"])
            if platform == Platform.ctrader:
                return build_run_response(
                    status="restarted",
                    platform=platform,
                    account=account,
                    container_name=existing["container_name"],
                    ctrader_id=existing["server"],
                    symbol=payload.symbol,
                    period=payload.period,
                )

            return build_run_response(
                status="restarted",
                platform=platform,
                account=account,
                container_name=existing["container_name"],
                server=existing["server"],
            )

        if platform == Platform.mt4:
            container_name = f"mt4_bot_{account}"
            start_mt4_docker(account, password, payload.server)
            save_account_container(account, platform, payload.server, container_name)
        elif platform == Platform.mt5:
            container_name = f"mt5_bot_{account}"
            start_mt5_docker(account, password, payload.server)
            save_account_container(account, platform, payload.server, container_name)
        elif platform == Platform.ctrader:
            container_name = f"ctrader_bot_{account}"
            start_ctrader_docker(
                account=account,
                password=password,
                ctrader_id=payload.ctrader_id,
                symbol=payload.symbol,
                period=payload.period,
            )
            save_account_container(account, platform, payload.ctrader_id, container_name)

        return build_run_response(
            status="started",
            platform=platform,
            account=account,
            container_name=container_name,
            server=payload.server,
            ctrader_id=payload.ctrader_id,
            symbol=payload.symbol,
            period=payload.period,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/status")
def get_status():
    try:
        containers = get_containers_status()
        return {"containers": containers}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class StopRequest(JsonStringCompatibleModel):
    id: str


@app.post("/api/stop")
async def stop_container_route(request: Request):
    payload = await parse_request_model(request, StopRequest)
    try:
        stopped = stop_container(payload.id)
        return {"status": "stopped", "container": stopped}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class RemoveRequest(JsonStringCompatibleModel):
    container_id: str


@app.post("/api/remove")
async def remove_container_route(request: Request):
    payload = await parse_request_model(request, RemoveRequest)
    try:
        removed = remove_container(payload.container_id)
        delete_account_container_by_name(removed)
        return {"status": "removed", "container": removed}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
