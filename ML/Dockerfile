FROM python:3.11-slim

WORKDIR /app

# Install python dependencies using PyPI mirror
RUN pip install --no-cache-dir --default-timeout=1000 --index-url https://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com \
    fastapi \
    uvicorn \
    pydantic \
    numpy \
    pandas \
    scikit-learn \
    requests

COPY . /app

EXPOSE 8000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
