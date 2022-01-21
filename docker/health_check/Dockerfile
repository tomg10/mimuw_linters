FROM python:3.9.10-slim
RUN mkdir health_check
WORKDIR health_check
COPY requirements.txt ./
RUN pip install -r requirements.txt

COPY health_check.py machine_manager_api.py schema.py ./
COPY configs/health_check ./configs/health_check
RUN mkdir logs


COPY start_health_check.sh ./
ENTRYPOINT ["./start_health_check.sh"]