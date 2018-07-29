#!/usr/bin/env bash
docker volume create --driver local \
  --opt type=none \
  --opt device=/path/to/dir \
  --opt o=bind \
  postgres-data