#!/usr/bin/env bash

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
cd "$SCRIPT_DIR" || exit

# Add conditional Playwright browser installation
if [[ "${WEB_LOADER_ENGINE,,}" == "playwright" ]]; then
    if [[ -z "${PLAYWRIGHT_WS_URL}" ]]; then
        echo "Installing Playwright browsers..."
        playwright install chromium
        playwright install-deps chromium
    fi

    python -c "import nltk; nltk.download('punkt_tab')"
fi

if [ -n "${WEBUI_SECRET_KEY_FILE}" ]; then
    KEY_FILE="${WEBUI_SECRET_KEY_FILE}"
else
    KEY_FILE=".webui_secret_key"
fi

PORT="${PORT:-8080}"
HOST="${HOST:-0.0.0.0}"
if test "$WEBUI_SECRET_KEY $WEBUI_JWT_SECRET_KEY" = " "; then
  echo "Loading WEBUI_SECRET_KEY from file, not provided as an environment variable."

  if ! [ -e "$KEY_FILE" ]; then
    echo "Generating WEBUI_SECRET_KEY"
    # Generate a random value to use as a WEBUI_SECRET_KEY in case the user didn't provide one.
    echo $(head -c 12 /dev/random | base64) > "$KEY_FILE"
  fi

  echo "Loading WEBUI_SECRET_KEY from $KEY_FILE"
  WEBUI_SECRET_KEY=$(cat "$KEY_FILE")
fi

if [[ "${USE_OLLAMA_DOCKER,,}" == "true" ]]; then
    echo "USE_OLLAMA is set to true, starting ollama serve."
    ollama serve &
fi

if [[ "${USE_CUDA_DOCKER,,}" == "true" ]]; then
  echo "CUDA is enabled, appending LD_LIBRARY_PATH to include torch/cudnn & cublas libraries."
  export LD_LIBRARY_PATH="$LD_LIBRARY_PATH:/usr/local/lib/python3.11/site-packages/torch/lib:/usr/local/lib/python3.11/site-packages/nvidia/cudnn/lib"
fi

# Check if SPACE_ID is set, if so, configure for space
if [ -n "$SPACE_ID" ]; then
  echo "Configuring for HuggingFace Space deployment"
  if [ -n "$ADMIN_USER_EMAIL" ] && [ -n "$ADMIN_USER_PASSWORD" ]; then
    echo "Admin user configured, creating"
    WEBUI_SECRET_KEY="$WEBUI_SECRET_KEY" uvicorn open_webui.main:app --host "$HOST" --port "$PORT" --forwarded-allow-ips '*' &
    webui_pid=$!
    echo "Waiting for webui to start..."
    while ! curl -s http://localhost:8080/health > /dev/null; do
      sleep 1
    done
    echo "Creating admin user..."
    curl \
      -X POST "http://localhost:8080/api/v1/auths/signup" \
      -H "accept: application/json" \
      -H "Content-Type: application/json" \
      -d "{ \"email\": \"${ADMIN_USER_EMAIL}\", \"password\": \"${ADMIN_USER_PASSWORD}\", \"name\": \"Admin\" }"
    echo "Shutting down webui..."
    kill $webui_pid
  fi

  export WEBUI_URL=${SPACE_HOST}
fi

# 数据库初始化检查
echo "检查数据库连接..."
if [[ -n "${DATABASE_TYPE}" ]]; then
    echo "使用 ${DATABASE_TYPE} 数据库"
    
    # 如果是MySQL，确保PyMySQL已安装
    if [[ "${DATABASE_TYPE,,}" == "mysql" ]]; then
        echo "检查PyMySQL依赖..."
        python -c "import pymysql" 2>/dev/null || {
            echo "安装PyMySQL..."
            pip install PyMySQL
        }
    fi
    
    # 如果是PostgreSQL，确保psycopg2已安装
    if [[ "${DATABASE_TYPE,,}" == "postgresql" ]]; then
        echo "检查psycopg2依赖..."
        python -c "import psycopg2" 2>/dev/null || {
            echo "安装psycopg2..."
            pip install psycopg2-binary
        }
    fi
else
    echo "使用默认SQLite数据库"
fi

PYTHON_CMD=$(command -v python3 || command -v python)

WEBUI_SECRET_KEY="$WEBUI_SECRET_KEY" exec "$PYTHON_CMD" -m uvicorn open_webui.main:app --host "$HOST" --port "$PORT" --forwarded-allow-ips '*' --workers "${UVICORN_WORKERS:-1}"