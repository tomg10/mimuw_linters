FROM python:3.9.10-slim
RUN mkdir load_balancer
WORKDIR load_balancer
COPY requirements.txt ./
RUN pip install -r requirements.txt

COPY linter_api.py load_balancer.py machine_manager_api.py schema.py ./
COPY configs/load_balancer ./configs/load_balancer
RUN mkdir logs


COPY start_load_balancer.sh ./
ENTRYPOINT ["./start_load_balancer.sh"]