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
    "sysbench memory run --memory-access-mode=seq --time=60 --threads=1": 6846183.03,
    "sysbench memory run --memory-access-mode=seq --time=60 --threads=16": 1800543.07,
    "sysbench memory run --memory-access-mode=rnd --time=60 --threads=1": 820909.95,
    "sysbench memory run --memory-access-mode=rnd --time=60 --threads=16": 4570970,
    "stress-ng --cpu 1 --cpu-method int32 --timeout 1m --oomable --metrics": 35992331,
    "stress-ng --cpu 0 --cpu-method int32 --timeout 1m --oomable --metrics": 177700,
    "stress-ng --matrix 1 --timeout 1m --oomable --metrics": 1389032,
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


##########
# Routes
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

@app.route('/', methods=['GET'])
def get_index():
    """Main page."""
    return flask.render_template('items/get_index.html')

@app.route('/host', methods=['GET'])
def get_host():
    """List hosts."""
    pager = _paginate(Result.query.with_entities(Result.machine_id).distinct())
    return flask.render_template('items/get_host.html', pager=pager)

@app.route('/host/<string:machine_id>', methods=['GET'])
def get_host_machine_id(machine_id):
    ###paget = _paginate(Result.query.filter_by(machine_id=machine_id))
    from sqlalchemy import func

    subquery = (
        Result
        .query
        .filter_by(machine_id=machine_id)
        .with_entities(
            Result.command,
            Result.created_at,
            Result.id,
            Result.result,
            func.row_number().over(
                partition_by=Result.command,
                order_by=Result.created_at.desc()
            ).label("rn")
        ).subquery()
    )
    full_query = (
        Result.query.with_entities(
            subquery.c.command,
            subquery.c.created_at,
            subquery.c.id,
            subquery.c.result
        )
        .select_from(subquery)
        .filter(subquery.c.rn == 1)
        .all()
    )

    return "TODO"


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

    db_result = Result(
        start=datetime.datetime.strptime(flask.request.json['start'], '%Y-%m-%d %H:%M:%S.%f'),
        end=datetime.datetime.strptime(flask.request.json['end'], '%Y-%m-%d %H:%M:%S.%f'),
        area=flask.request.json['area'],
        command=flask.request.json['command'],
        rc=flask.request.json['rc'],
        measurements_url=flask.request.json['measurements_url'],
        result=flask.request.json['result'],
        run=db_run,
    )

    app_db.session.add(db_host)
    app_db.session.add(db_run)
    app_db.session.add(db_result)
    app_db.session.commit()

    return {"result": "created", "data": db_result.serialize()}, 201

@app.route('/api/v1/result/<string:machine_id>', methods=['GET'])
def api_v1_get_result_machine_id(machine_id):
    """Get info about result by it's machine_id."""
    return Result.query.filter_by(machine_id=machine_id).serialize()

@app.route('/api/v1/result/<int:rid>', methods=['GET'])
def api_v1_get_result_rid(rid):
    """Get info about result by it's id."""
    return Result.query.filter_by(id=rid).first_or_404().serialize()
