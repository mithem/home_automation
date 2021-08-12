[![CI status](https://github.com/mithem/home_automation/actions/workflows/main.yml/badge.svg)](https://github.com/mithem/home_automation/actions/workflows/main.yml)

# home_automation

A project for home automation. That's organizing and compressing homework on miguelsnas and related scripts/programs or otherwise useful but maybe unrelated stuff.

## Run via docker-compose.yml:

```yml
version: "3"
services:
  home_automation:
    image: home_automation:1.0.0
    container_name: home_automation
    build: .
    volumes:
      - /mnt/MassStorage/Hausaufgaben/HAs:/homework/current
      - /mnt/MassStorage/Hausaufgaben/Archive:/homework/archive
    environment:
      EMAIL_ADDRESS: test@example.com
      EMAIL_PASSWD: passw0rd!
      HASS_BASE_URL: http://homeassistant.local:8123
      HASS_TOKEN: t0ken!
      THINGS_SERVER_URL: http://things.local:8001
```
