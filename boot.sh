#!/usr/bin/env bash
# this script is used to boot a Docker container

GUNICORN_LOGS_DIR="logs"
ERROR_LOGFILE="$GUNICORN_LOGS_DIR/error.log"
ACCESS_LOGFILE="$GUNICORN_LOGS_DIR/access.log"

HOST="0.0.0.0"

GUNICORN_PORT=$1

cd /brain_morph

mkdir -p "$GUNICORN_LOGS_DIR"
touch "$ERROR_LOGFILE" "$ACCESS_LOGFILE"

while true; do
    mongod --bind_ip $HOST --port 27017 > mongod.log 2>&1 &
    if [[ "$?" == "0" ]]; then
        break
    fi
    echo "Deploy command failed, retrying in 5 secs..."
    sleep 5
done

source venv/bin/activate
exec gunicorn -b $HOST:$GUNICORN_PORT --timeout=120 --access-logfile "$ACCESS_LOGFILE" --error-logfile "$ERROR_LOGFILE" brain_morph:flask_app
