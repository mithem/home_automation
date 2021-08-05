FROM python:3.9-slim


COPY rootfs /

WORKDIR /home_automation

COPY . .
RUN mv docker.env .env

RUN --mount=type=cache,target=/var/root/.cache/pip pip3 install -r requirements_dev.txt

RUN python3 setup.py install

VOLUME ["/home_automation", "/homework/current", "/homework/archive"]

ENTRYPOINT ["python3", "-m", "home_automation.run_cron_jobs"]
