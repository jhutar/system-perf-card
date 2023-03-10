Webapp to store and present system performance card results
===========================================================

Webapp to store and present system performance card results

Usage
-----

This is a simple Flask application that allows to upload JSONs with benchmark run details and visualize them.
Every upload contains:

* Identification of a host where it was running (hostname and machine ID).
* Command with a benchmark that was running. Also it's return code.
* Parsed numerical result of a benchmark.
* Test run ID (one ID common to all benchmarks ran in given iteration), data and some more metadata.

App then allows to see:

* History of runs per host, how final single performance index number changed over time for a host.
* Compare results from two systems to assess how different they are regarding performance.

Developing
----------

Setup terminal environment with what you need to run the app:

    python -m venv venv
    source venv/bin/activate
    python -m pip install -U pip
    python -m pip install -r requirements.txt
    export FLASK_APP=myapp.py
    export SQLITE_FILE=/tmp/database.db

Initialize DB:

    flask db upgrade

And finally this will get you the server running on `http://127.0.0.1:5000/`:

    flask run

Handy command to look into the DB:

    sqlite3 $SQLITE_FILE
    > .tables

Changing schema
---------------

Initial steps:

    rm -rf /tmp/database.db
    rm -rf migrations/
    flask db init
    flask db migrate -m "Initial migration."
    flask db upgrade


Build image
-----------

Image should be available form quay.io repo:

    podman pull quay.io/rhcloudperfscale/system-perf-card-webapp

But if you want to build the image locally from git repo:

    sudo podman build -t system-perf-card-webapp .

And to run it:

    mkdir /tmp/system-perf-card-webapp
    podman run --rm -ti -p 5000:5000 -v /tmp/system-perf-card-webapp:/usr/src/app/data:z -e SQLITE_FILE=/usr/src/app/data/database.db system-perf-card-webapp


Testing
-------

To test basic functionality, ensure you do not have some server listening on port 5000 and run below command.
Note it will remove /tmp/database.db file.

    ./tests.sh
