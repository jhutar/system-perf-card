#!/bin/sh

set -xe

if ! [ -d venv ]; then
    python -m venv venv
    source venv/bin/activate
    python -m pip install -U pip
    python -m pip install -r requirements.txt
    deactivate
fi

source venv/bin/activate
export FLASK_APP=myapp.py
export SQLITE_FILE=/tmp/database.db
rm -rf $SQLITE_FILE
flask db upgrade
flask --debug run &>/tmp/myapp.log &
pid=$!
trap "kill $pid" EXIT
sleep 1

curl --silent -X GET http://127.0.0.1:5000/ | grep --quiet 'Hello world'
curl --silent -X GET http://127.0.0.1:5000/api/v1/result | grep '"total": 0'
curl --silent -X POST http://127.0.0.1:5000/api/v1/result -H "Content-Type: application/json" -d '{"machine_id": "abcdef0123456789", "hostname": "abc.example.com", "area": "disk", "command": "fio --directory=/fiotest --name fio_test_file --direct=1 --rw=randread --bs=16k --size=1G --numjobs=16 --time_based --runtime=60s --group_reporting --norandommap", "rc": 0, "result": 123456, "measurements_url": "http://pbench.example.com/results/xyz", "start": "2022-12-12 12:12:12.123456", "end": "2022-12-12 12:24:24.654321"}'
curl --silent -X GET http://127.0.0.1:5000/api/v1/result | grep '"total": 1'

echo "SUCCESS"
