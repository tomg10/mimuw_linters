FROM python:3.9.10-slim
RUN mkdir update_manager
WORKDIR update_manager
COPY requirements.txt ./
RUN pip install -r requirements.txt

COPY machine_manager_api.py update_manager.py schema.py ./
COPY configs/update_manager ./configs/update_manager
RUN mkdir logs


COPY start_update_manager.sh ./
ENTRYPOINT ["./start_update_manager.sh"]