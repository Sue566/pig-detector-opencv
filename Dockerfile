FROM python:3.11-slim
WORKDIR /app

# Allow using a mirror for Python packages inside China
ARG PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple
ENV PIP_INDEX_URL=${PIP_INDEX_URL}

COPY requirements.txt .
RUN pip install --no-cache-dir -i $PIP_INDEX_URL -r requirements.txt

COPY . .

# Expose port 8092 for the FastAPI service
EXPOSE 8092

CMD ["bash", "start_api.sh"]
