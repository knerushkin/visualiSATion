#!/usr/bin/env python

from __future__ import print_function

import urllib2

from flask import Flask, render_template, request, redirect, url_for
import os
import socket
import json
from utils import problem
from subprocess import call
import pycosat
from utils.problem import sign

app = Flask(__name__)

APP_ROOT_FOLDER = os.path.dirname(__file__)
TEMPLATE_FOLDER = os.path.join(APP_ROOT_FOLDER, 'templates')
STATIC_FOLDER = os.path.join(APP_ROOT_FOLDER, 'static')
UPLOAD_FOLDER = os.path.join(STATIC_FOLDER, 'data')
ALLOWED_EXTENSIONS = set(['cnf'])

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


@app.route("/")
def hello():
    return "Hello, I love Digital Ocean!"


@app.route("/load", methods=['GET', 'POST'])
def load():
    return '''
    <!doctype html>
    <title>Upload new File</title>
    <h1>Upload new File</h1>
    <form method=post enctype=multipart/form-data>
      <p><input type=file name=file>
         <input type=submit value=Upload>
    </form>
    '''


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


def list_data(path):
    l = []
    for folder, subfolder, file in os.walk(path):
        l.extend(file)

    return l


@app.route("/visualisation", methods=['GET', 'POST'])
def show():
    call(['rm', '-f', 'bin/pre-satelited.cnf'])
    selected = request.args.get('file')
    file_list = list_data(UPLOAD_FOLDER)
    print('--------------')
    print(UPLOAD_FOLDER)
    print('--------------')
    print(file_list)
    print('--------------')
    if request.method == 'POST':
        file = request.files['file']
        if file and allowed_file(file.filename):
            filename = file.filename
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            return redirect(url_for('show'))

    return render_template("visualisation.html", file_list=file_list, selected=selected)


@app.route("/sat/solve/<file>")
def solve(file):
    solution = pycosat.solve(problem.read('static/data/' + file)["clauses"])
    result = []
    if solution != "UNSAT":
        for value in solution:
            result.append({"id": "L" + str(abs(value)) + "",
                           "value":  sign(value)})
    else:
        result = solution
    return json.dumps(result)


@app.route("/visual/repr/factor/<file>")
def graph(file):
    graph_data = problem.prepare_graph_data(file, graph_type="factor", satelite=False)
    return json.dumps(graph_data)


@app.route("/visual/repr/factor/satelited/<file>")
def graph_satelited(file):
    graph_data = problem.prepare_graph_data(file, graph_type="factor", satelite=True)
    return json.dumps(graph_data)


@app.route("/visual/repr/interaction/<file>")
def graph_interaction(file):
    graph_data = problem.prepare_graph_data(file, graph_type="interaction", satelite=False)
    return json.dumps(graph_data)


@app.route("/visual/repr/interaction/satelited/<file>")
def graph_interaction_satelited(file):
    graph_data = problem.prepare_graph_data(file, graph_type="interaction", satelite=True)
    return json.dumps(graph_data)


if __name__ == "__main__":
    app.run()