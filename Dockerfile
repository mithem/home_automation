FROM python:3.9
FROM node:17

WORKDIR /home_automation

COPY . .
RUN mv docker.env .env

RUN mkdir /var/run/home_automation

RUN script/install-system-dependencies

RUN --mount=type=cache,target=/var/root/.cache/pip python3 -m pip install -r requirements_dev.txt

RUN python3 setup.py install

VOLUME ["/home_automation", "/homework/current", "/homework/archive", "/moodle"]

HEALTHCHECK --interval=10s --timeout=3s CMD curl -f http://localhost:10000/api/healthcheck || exit 1

ENTRYPOINT ["python3", "-m", "home_automation.runner"]
