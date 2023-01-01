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

curl --silent -X GET http://127.0.0.1:5000/api/v1/host | grep '"total": 0'
curl --silent -X GET http://127.0.0.1:5000/api/v1/run | grep '"total": 0'
curl --silent -X GET http://127.0.0.1:5000/api/v1/result | grep '"total": 0'
curl --silent -X POST http://127.0.0.1:5000/api/v1/result -H "Content-Type: application/json" -d '{"machine_id": "abcdef0123456789", "hostname": "abc.example.com", "area": "disk", "command": "fio --directory=/fiotest --name fio_test_file --direct=1 --rw=randread --bs=16k --size=1G --numjobs=16 --time_based --runtime=60s --group_reporting --norandommap", "rc": 0, "result": "123.450k", "measurements_url": "http://pbench.example.com/results/xyz", "start": "2022-12-12 12:12:12.123456", "end": "2022-12-12 12:24:24.654321", "run_name": "2022-12-12T12:00:00,000000000+00:00"}'   # upload first result
curl --silent -X GET http://127.0.0.1:5000/api/v1/host | grep '"total": 1'
curl --silent -X GET http://127.0.0.1:5000/api/v1/run | grep '"total": 1'
curl --silent -X GET http://127.0.0.1:5000/api/v1/result | grep '"total": 1'
curl --silent -X POST http://127.0.0.1:5000/api/v1/result -H "Content-Type: application/json" -d '{"machine_id": "abcdef0123456789", "hostname": "abc.example.com", "area": "disk", "command": "fio --directory=/fiotest --ioengine=psync --name fio_test_file --direct=1 --rw=randwrite --bs=16k --size=1G --numjobs=16 --time_based --runtime=60s --group_reporting --norandommap", "rc": 0, "result": 123456, "measurements_url": "http://pbench.example.com/results/xyz", "start": "2022-12-12 12:24:25.000000", "end": "2022-12-12 12:26:26.000000", "run_name": "2022-12-12T12:00:00,000000000+00:00"}'   # upload second result to same run
curl --silent -X GET http://127.0.0.1:5000/api/v1/host | grep '"total": 1'
curl --silent -X GET http://127.0.0.1:5000/api/v1/run | grep '"total": 1'
curl --silent -X GET http://127.0.0.1:5000/api/v1/result | grep '"total": 2'
curl --silent -X POST http://127.0.0.1:5000/api/v1/result -H "Content-Type: application/json" -d '{"machine_id": "abcdef0123456789", "hostname": "abc.example.com", "area": "disk", "command": "fio --directory=/fiotest --name fio_test_file --direct=1 --rw=randread --bs=16k --size=1G --numjobs=16 --time_based --runtime=60s --group_reporting --norandommap", "rc": 0, "result": 123456, "measurements_url": "http://pbench.example.com/results/xyz", "start": "2022-12-15 12:12:12.123456", "end": "2022-12-15 12:24:24.654321", "run_name": "2022-12-15T12:00:00,000000000+00:00"}'   # upload first result to different run
curl --silent -X GET http://127.0.0.1:5000/api/v1/host | grep '"total": 1'
curl --silent -X GET http://127.0.0.1:5000/api/v1/run | grep '"total": 2'
curl --silent -X GET http://127.0.0.1:5000/api/v1/result | grep '"total": 3'
curl --silent -X POST http://127.0.0.1:5000/api/v1/result -H "Content-Type: application/json" -d '{"machine_id": "abcdef0123456789", "hostname": "abc.example.com", "area": "disk", "command": "fio --directory=/fiotest --name fio_test_file --direct=1 --rw=randread --bs=16k --size=1G --numjobs=16 --time_based --runtime=60s --group_reporting --norandommap", "rc": 0, "result": 123456, "measurements_url": "http://pbench.example.com/results/xyz", "start": "2022-12-15 12:12:12.123456", "end": "2022-12-15 12:24:24.654321", "run_name": "2022-12-15T12:00:00,000000000+00:00"}'   # upload second result to that second run
curl --silent -X GET http://127.0.0.1:5000/api/v1/host | grep '"total": 1'
curl --silent -X GET http://127.0.0.1:5000/api/v1/run | grep '"total": 2'
curl --silent -X GET http://127.0.0.1:5000/api/v1/result | grep '"total": 4'
curl --silent -X POST http://127.0.0.1:5000/api/v1/result -H "Content-Type: application/json" -d '{"machine_id": "abcdef0000000000", "hostname": "xyz.example.com", "area": "disk", "command": "fio --directory=/fiotest --name fio_test_file --direct=1 --rw=randread --bs=16k --size=1G --numjobs=16 --time_based --runtime=60s --group_reporting --norandommap", "rc": 0, "result": 123456, "measurements_url": "http://pbench.example.com/results/xyz", "start": "2022-12-15 12:12:12.000000", "end": "2022-12-15 12:24:24.000000", "run_name": "2022-12-15T12:00:00,000000000+00:00"}'   # upload first result for new host
curl --silent -X GET http://127.0.0.1:5000/api/v1/host | grep '"total": 2'
curl --silent -X GET http://127.0.0.1:5000/api/v1/run | grep '"total": 3'
curl --silent -X GET http://127.0.0.1:5000/api/v1/result | grep '"total": 5'

curl --silent -X GET http://127.0.0.1:5000/ | grep --quiet 'This application tries to address these use-cases'
curl --silent -X GET http://127.0.0.1:5000/host | grep --quiet 'Hosts'
curl --silent -X GET http://127.0.0.1:5000/host/abcdef0123456789 | grep --quiet 'Details on abc.example.com'
curl --silent -X GET http://127.0.0.1:5000/run/2 | grep --quiet 'Run 2022-12-15T12:00:00,000000000+00:00'
curl --silent -X GET http://127.0.0.1:5000/result/3 | grep --quiet 'Result 3'
curl --silent -X GET http://127.0.0.1:5000/compare | grep --quiet 'Compare'
curl --silent -X GET "http://127.0.0.1:5000/compare?host1=abcdef0123456789&host2=abcdef0000000000" | grep --quiet 'Comparing'

echo "SUCCESS"
