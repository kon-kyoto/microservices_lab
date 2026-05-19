# Microservices Lab

A learning project with two microservices and an API gateway using Docker Compose.

## Architecture

- **Gateway** (Nginx) — routes requests to services:
  - `/api/service1/` → `service1:5001`
  - `/api/service2/` → `service2:5002`

- **Service1** (Flask) — returns a JSON message about itself.

- **Service2** (Flask) — requests `/info` from Service1 and returns a combined response.

## Run

```bash
docker-compose up --build
```

## Endpoints

| URL | Description |
|-----|-------------|
| `http://localhost:5000/api/service1/info` | Response from the first service |
| `http://localhost:5000/api/service2/` | Response from the second service (includes data from Service1) |

## Structure

```
.
├── docker-compose.yml
├── gateway/
│   └── nginx.conf
└── services/
    ├── service1/
    │   └── app.py
    └── service2/
        └── app.py
```

## Ports

- `5000` — API Gateway (external)
- `5001` — Service1 (internal)
- `5002` — Service2 (internal)
