FROM python:3.9-slim

WORKDIR /home_automation

COPY . .
RUN mv docker.env .env

RUN pip3 install -U -r requirements_dev.txt

RUN python3 setup.py install

VOLUME ["/home_automation", "/homework/current", "/homework/archive"]

ENTRYPOINT ["python3", "-m", "home_automation.run_cron_jobs"]
