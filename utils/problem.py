#!/usr/bin/env python

from mxklabs import dimacs
import re
from subprocess import call
import os.path

UTILS_FOLDER = os.path.dirname(__file__)
APP_ROOT_FOLDER = os.path.abspath(__file__ + "/../../")
STATIC_FOLDER = os.path.join(APP_ROOT_FOLDER, 'static')
DATA_FOLDER = os.path.join(STATIC_FOLDER, 'data')
RAW_FOLDER = os.path.join(DATA_FOLDER, 'raw')
SATELITED_FOLDER = os.path.join(DATA_FOLDER, 'satelited')
BIN_FOLDER = os.path.join(APP_ROOT_FOLDER, 'bin')


def read(filename):
    cnf_problem = dimacs.read(filename)
    return cnf_problem.__dict__


def generate_interaction_graph(data):
    clauses_only_positive_literals = []
    for clause in data["clauses"]:
        c = [abs(v) for v in clause]
        clauses_only_positive_literals.append(c)

    relations = {}
    for variable in range(1, data["num_vars"]):
        vars_associated_dirty = [v for c in clauses_only_positive_literals if variable in c for v in c]
        vars_associated_flat = list(set(vars_associated_dirty))
        vars_associated = [v for v in vars_associated_flat if v not in range(variable + 1)]
        relations[variable] = vars_associated
    if relations:
        relations[data["num_vars"]] = []

    interaction_graph = dict(nodes=[], links=[])
    for v, i in relations.iteritems():
        node = {"id": "L" + str(v) + "", "group": 1}
        interaction_graph["nodes"].append(node)
        links = [dict(source=("L" + str(v) + ""), target=("L" + str(item) + ""), weight=1) for item in i]
        interaction_graph["links"].extend(links)

    interaction_graph["num_vars"] = data["num_vars"]
    interaction_graph["num_clauses"] = data["num_clauses"]
    return interaction_graph


def satelite_it(dimacs_file_path):
    satelite_path = os.path.join(BIN_FOLDER, 'SatELite_v1.0_linux')
    file_name = re.sub(r'.cnf', '_satelited.cnf', os.path.basename(dimacs_file_path))
    satelited_file_path = os.path.join(SATELITED_FOLDER, file_name)
    call([satelite_path, dimacs_file_path, satelited_file_path], stdout=open(os.devnull, 'wb'))

    return satelited_file_path


# author: knerushkin@gmail.com
def transform(data):
    result = {}
    result.update({"nodes": nodes(data["clauses"], data["num_clauses"], data["num_vars"])})
    result.update({"links": links(data["clauses"])})
    result.update({"num_vars": data["num_vars"]})
    result.update({"num_clauses": data["num_clauses"]})
    return result


def sign(x):
    return 'positive' if x > 0 else 'negative'


def link(clause, count):
    result = []
    for literal in clause:
        result.append({"source": "L{l}".format(l=abs(literal)), "target": "C{c}".format(c=count), "value": 1,
                       "direction": sign(literal)})

    return result


def links(clauses):
    links = []
    for count, clause in enumerate(clauses):
        links.append(link(clause,count))

    return [item for sublist in links for item in sublist]


def nodes(clauses, num_clauses, num_literals):
    result = []
    for clause in range(0, num_clauses):
        result.append({"id": "C" + str(clause), "group": "clause"})

    for literal in range(1, num_literals + 1):
        result.append({"id": "L" + str(abs(literal)) + "",
                       "group":  "literal"})
    return result


def prepare_graph_data(file, graph_type, satelite):
    cnf_file_path = os.path.join(RAW_FOLDER, file)

    if satelite:
        cnf_file_path = os.path.join(SATELITED_FOLDER, file)
        cnf_file_path = re.sub(r'.cnf', '_satelited.cnf', cnf_file_path.rstrip())

    cnf = read(cnf_file_path)
    if graph_type == "factor":
        graph_data = transform(cnf)
    elif graph_type == "interaction":
        graph_data = generate_interaction_graph(cnf)

    return graph_data


def get_metadata(file, satelite):
    if not file:
        return None

    if satelite:
        file = satelite_it(os.path.join(RAW_FOLDER, file))
    cnf = read(os.path.join(RAW_FOLDER, file))
    meta = {}
    meta.update({"num_vars": cnf["num_vars"]})
    meta.update({"num_clauses": cnf["num_clauses"]})

    return meta