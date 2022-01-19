FROM python:3.9.10-slim
RUN mkdir linter
WORKDIR linter
COPY linter.py simple_java_linter.py simple_python_linter.py requirements.txt schema.py services_addresses.py ./
COPY configs/linters ./configs/linters

RUN pip install -r requirements.txt
RUN mkdir logs


ENV LINTER_TEST_LOGGING="false"
CMD ["uvicorn", "linter:linter_app", "--port=5000", "--host=0.0.0.0"]