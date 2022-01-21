FROM python:3.9.10-slim
RUN mkdir linter
WORKDIR linter
COPY linter.py simple_java_linter.py simple_python_linter.py requirements.txt schema.py services_addresses.py start_linter.sh simple_c_linter.py ./
COPY configs/linters ./configs/linters

RUN pip install -r requirements.txt
RUN mkdir logs


ENV LINTER_TEST_LOGGING="false"
ENTRYPOINT ["./start_linter.sh"]