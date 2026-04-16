# pythonDocker — Trading Platform Docker Runner

A FastAPI service that launches and manages Docker containers for MT4, MT5, and cTrader trading bots.

## Prerequisites

- Python 3.10+
- Docker (running and accessible from the command line)
- Docker images built and tagged:
  - `mt4-beq-auto`
  - `mt5-wine-auto`
  - `ctrader-auto`

## Setup

```bash
pip install -r requirements.txt
```

## Run the API server

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```
Or

```bash
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`.  
Interactive docs: `http://localhost:8000/docs`

---

## API Endpoints

### `POST /api/run`

Start a trading platform container.

**Request body:**
```json
{
  "account": "12345678",
  "password": "yourpassword",
  "server": "Broker-Live",
  "platform": "mt4"
}
```

`platform` must be one of: `mt4`, `mt5`, `ctrader`

**Response:**
```json
{
  "status": "started",
  "platform": "mt4",
  "account": "12345678",
  "server": "Broker-Live"
}
```

---

### `GET /api/status`

List all running/stopped bot containers (`mt4_bot_*`, `mt5_bot_*`, `ctrader_bot_*`).

**Response:**
```json
{
  "containers": [
    { "ID": "abc123", "Names": "mt4_bot_12345678", "Status": "Up 2 minutes", ... }
  ]
}
```

---

### `POST /api/stop`

Stop a container by its Docker container ID.

**Request body:**
```json
{
  "id": "abc123def456"
}
```

**Response:**
```json
{
  "status": "stopped",
  "container": "abc123def456"
}
```

---

## Project Structure

| File | Description |
|------|-------------|
| `main.py` | FastAPI app with `/api/run`, `/api/status`, `/api/stop` routes |
| `docker_runner.py` | Subprocess wrappers that call `docker run`/`docker stop`/`docker ps` |
| `requirements.txt` | Python dependencies |
