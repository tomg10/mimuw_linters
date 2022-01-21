#!/bin/bash

uvicorn linter:linter_app --host=0.0.0.0 --port="$1"