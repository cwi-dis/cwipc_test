# Point cloud streaming server

This is a server that will serve compressed point cloud streams, running in a docker container.

## Usage

```
docker compose stop
docker compose build
docker compose up -d
```

The container will restart unless stopped.

The point cloud server is exposed at host port `8089`.
