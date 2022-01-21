FROM google/cloud-sdk:slim
RUN mkdir machine_manager
WORKDIR machine_manager
COPY requirements.txt ./
RUN pip3 install -r requirements.txt

COPY machine_manager_api.py linter_api.py machine_manager.py killable_proxy_deployer.py local_linter_deployer.py gcp_linter_deployer.py deploy_utils.py health_utils.py gcp_utils.py killable_linter_proxy_api.py schema.py services_addresses.py ./
COPY configs/machine_manager ./configs/machine_manager
COPY gcp/ ./gcp
COPY key/key.json ./key.json

RUN mkdir logs

ENV GOOGLE_APPLICATION_CREDENTIALS="key.json"

ENV MACHINE_MANAGER_DEPLOY_BACKEND="gcp"

COPY start_machine_manager.sh ./
ENTRYPOINT ["./start_machine_manager.sh"]