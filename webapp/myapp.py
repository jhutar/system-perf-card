#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import datetime
import os

import random

import click

import flask

import flask_sqlalchemy
import flask_migrate

from sqlalchemy.sql import func


TREASHOLDS = {
    "sysbench memory run --memory-access-mode=seq --time=60 --threads=1": 4707590.65,
    "sysbench memory run --memory-access-mode=seq --time=60 --threads=16":6995066.88,
    "sysbench memory run --memory-access-mode=rnd --time=60 --threads=1":1797867.98,
    "sysbench memory run --memory-access-mode=rnd --time=60 --threads=16":822498.42,
    "stress-ng --cpu 1 --cpu-method int32 --timeout 1m --oomable --metrics":4613675,
    "stress-ng --cpu 0 --cpu-method int32 --timeout 1m --oomable --metrics":35968160,
    "stress-ng --matrix 1 --timeout 1m --oomable --metrics":176314,
    "stress-ng --matrix 0 --timeout 1m --oomable --metrics":1389884,
    "stress-ng --mq 0 -t 30s --oomable --metrics":34197581,
    "stress-ng --vm 2 --vm-bytes 1G --page-in --timeout 1m --oomable --metrics":5011932,
    "stress-ng --timer 32 --timer-freq 1000000 --timeout 1m --oomable --metrics":42746792,
    "stress-ng --userfaultfd 0 --timeout 1m --oomable --metrics":24294961,
    "fio --directory=/fiotest --name fio_test_file --direct=1 --rw=randread --bs=16k --size=1G --numjobs=16 --time_based --runtime=60s --group_reporting --norandommap":20300,
    "fio --directory=/fiotest --ioengine=psync --name fio_test_file --direct=1 --rw=randwrite --bs=16k --size=1G --numjobs=16 --time_based --runtime=60s --group_reporting --norandommap":6196,
    "fio --directory=/fiotest --direct=1 --rw=read --randrepeat=0 --ioengine=libaio --bs=1024k --size=1G --iodepth=8 --time_based=1 --runtime=60s --name=fio_direct_read_test":316,
    "fio --directory=/fiotest --direct=1 --rw=write --randrepeat=0 --ioengine=libaio --bs=1024k --size=1G --iodepth=8 --time_based=1 --runtime=60s --name=fio_direct_write_test":606,
    "sysbench memory run --memory-access-mode=seq --time=60 --threads=1":4687364.83,
    "sysbench memory run --memory-access-mode=seq --time=60 --threads=16":6944556.98,
    "sysbench memory run --memory-access-mode=rnd --time=60 --threads=1":1790700.35,
    "sysbench memory run --memory-access-mode=rnd --time=60 --threads=16":817756.61,
}


app = flask.Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{ os.environ['SQLITE_FILE'] }"
###app.config['SQLALCHEMY_DATABASE_URI'] = f"postgresql://{ os.environ['POSTGRESQL_USER'] }:{ os.environ['POSTGRESQL_PASSWORD'] }@{ os.environ['POSTGRESQL_HOST'] }:{ os.environ['POSTGRESQL_PORT'] }/{ os.environ['POSTGRESQL_DATABASE'] }"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app_db = flask_sqlalchemy.SQLAlchemy(app)

app_migrate = flask_migrate.Migrate(app, app_db)


##########
# Models
##########

class Host(app_db.Model):
    id = app_db.Column(app_db.Integer, primary_key=True)
    created_at = app_db.Column(app_db.DateTime(timezone=True), server_default=func.now())
    machine_id = app_db.Column(app_db.String(80), unique=False, nullable=False)
    hostname = app_db.Column(app_db.String(200), unique=False, nullable=False)
    runs = app_db.relationship('Run', backref='host')

    def __repr__(self):
        return f'<Host {self.id}>'

    def serialize(self):
        return {
            "id": self.id,
            "created_at": self.created_at,
            "machine_id": self.machine_id,
            "hostname": self.hostname,
        }

class Run(app_db.Model):
    id = app_db.Column(app_db.Integer, primary_key=True)
    created_at = app_db.Column(app_db.DateTime(timezone=True), server_default=func.now())
    name = app_db.Column(app_db.String(80), unique=False, nullable=False)
    host_id = app_db.Column(app_db.Integer, app_db.ForeignKey('host.id'))
    results = app_db.relationship("Result", backref="run")

    def __repr__(self):
        return f'<Run {self.id}>'

    def serialize(self):
        return {
            "id": self.id,
            "created_at": self.created_at,
            "name": self.name,
            "host_id": self.host_id,
        }

class Result(app_db.Model):
    id = app_db.Column(app_db.Integer, primary_key=True)
    created_at = app_db.Column(app_db.DateTime(timezone=True), server_default=func.now())
    start = app_db.Column(app_db.DateTime(timezone=True), unique=False, nullable=False)
    end = app_db.Column(app_db.DateTime(timezone=True), unique=False, nullable=False)
    area = app_db.Column(app_db.String(80), unique=False, nullable=False)
    command = app_db.Column(app_db.Text, unique=False, nullable=False)
    rc = app_db.Column(app_db.Integer, unique=False, nullable=False)
    measurements_url = app_db.Column(app_db.Text, unique=False, nullable=False)
    result = app_db.Column(app_db.Integer, unique=False, nullable=False)
    run_id = app_db.Column(app_db.Integer, app_db.ForeignKey('run.id'))

    def __repr__(self):
        return f'<Result {self.id}>'

    def serialize(self):
        return {
            "id": self.id,
            "created_at": self.created_at,
            "start": self.start,
            "end": self.end,
            "area": self.area,
            "command": self.command,
            "rc": self.rc,
            "measurements_url": self.measurements_url,
            "result": self.result,
            "run_id": self.run_id,
        }

    def perf_index(self):
        if self.command not in TREASHOLDS:
            app.logger.error(f"Result {self.id} did not found treshold for {self.command}")
            return None
        else:
            return self.result / TREASHOLDS[self.command]


##########
# Utils
##########

def _paginate(query):
    if 'page' in flask.request.args:
        page = int(flask.request.args['page'])
    else:
        page = 1

    return query.paginate(page=page)


def _serialize(query):
    data = _paginate(query)

    return {
        "total": data.total,
        "page": data.page,
        "pages": data.pages,
        "per_page": data.per_page,
        "items": [d.serialize() for d in data.items],
    }


##########
# Routes
##########

@app.route('/', methods=['GET'])
def get_index():
    """Main page."""
    return flask.render_template('items/get_index.html')

@app.route('/host', methods=['GET'])
def get_host():
    """List hosts."""
    pager = _paginate(Host.query)
    return flask.render_template('items/get_host.html', pager=pager)

@app.route('/host/<string:machine_id>', methods=['GET'])
def get_host_machine_id(machine_id):
    db_host = Host.query.filter_by(machine_id=machine_id).first_or_404()
    pager = _paginate(Run.query.filter_by(host=db_host))
    return flask.render_template('items/get_host_machine_id.html', host=db_host, pager=pager)

@app.route('/run/<int:rid>', methods=['GET'])
def get_run_rid(rid):
    db_run = Run.query.filter_by(id=rid).first_or_404()
    pager = _paginate(Result.query.filter_by(run=db_run))
    return flask.render_template('items/get_run_rid.html', run=db_run, pager=pager)

@app.route('/result/<int:rid>', methods=['GET'])
def get_result_rid(rid):
    db_result = Result.query.filter_by(id=rid).first_or_404()
    return flask.render_template('items/get_result_rid.html', result=db_result)


##########
# API
##########

@app.route('/api/v1/host', methods=['GET'])
def api_v1_get_host():
    """List hosts."""
    return _serialize(Host.query)

@app.route('/api/v1/run', methods=['GET'])
def api_v1_get_run():
    """List runs."""
    return _serialize(Run.query)

@app.route('/api/v1/result', methods=['GET'])
def api_v1_get_result():
    """List results."""
    return _serialize(Result.query)

@app.route('/api/v1/result', methods=['POST'])
def api_v1_post_result():
    """Upload new result."""
    db_host = Host.query.filter_by(machine_id=flask.request.json['machine_id']).first()
    if db_host is None:
        db_host = Host(
            machine_id=flask.request.json['machine_id'],
            hostname=flask.request.json['hostname'],
        )
    else:
        db_host.hostname = flask.request.json['hostname']

    db_run = Run.query.filter_by(name=flask.request.json['run_name']).first()
    if db_run is None:
        db_run = Run(
            name=flask.request.json['run_name'],
            host=db_host,
        )

    result = flask.request.json['result']
    if isinstance(result, str):
        fixes = {
            "k": 1000,
            "M": 1000000,
            "G": 1000000000,
        }
        for unit, multiplier in fixes.items():
            if result.endswith(unit):
                result = float(result[:-1]) * multiplier
                break
    result = float(result)

    db_result = Result(
        start=datetime.datetime.strptime(flask.request.json['start'], '%Y-%m-%d %H:%M:%S.%f'),
        end=datetime.datetime.strptime(flask.request.json['end'], '%Y-%m-%d %H:%M:%S.%f'),
        area=flask.request.json['area'],
        command=flask.request.json['command'],
        rc=flask.request.json['rc'],
        measurements_url=flask.request.json['measurements_url'],
        result=result,
        run=db_run,
    )

    app_db.session.add(db_host)
    app_db.session.add(db_run)
    app_db.session.add(db_result)
    app_db.session.commit()

    return {"result": "created", "data": db_result.serialize()}, 201

@app.route('/api/v1/result/<int:rid>', methods=['GET'])
def api_v1_get_result_rid(rid):
    """Get info about result by it's id."""
    return Result.query.filter_by(id=rid).first_or_404().serialize()
