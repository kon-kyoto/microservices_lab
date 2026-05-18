# microservices-lab

```bash
microservices-lab/
├── docker-compose.yml
├── .env
├── gateway/
│   ├── Dockerfile
│   └── nginx.conf
├── services/
│   ├── auth/
│   │   ├── Dockerfile
│   │   ├── app.py
│   │   └── requirements.txt
│   ├── users/
│   │   ├── Dockerfile
│   │   ├── app.py
│   │   └── requirements.txt
│   └── orders/
│       ├── Dockerfile
│       ├── app.py
│       └── requirements.txt
└── infrastructure/
    ├── postgres/
    │   └── init.sql
    └── redis/
        └── (пусто, используем стандартный образ)
```
