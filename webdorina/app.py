# !/usr/bin/env python3
# coding=utf-8
from __future__ import print_function
from __future__ import unicode_literals

import json
import logging
import os
import sys
import uuid
from io import BytesIO

import flask
from dorina.genome import Genome
from dorina.regulator import Regulator
from flask import flash, request, redirect, jsonify, render_template, send_file
from redis import Redis
from rq import Queue

from webdorina.workers import filter_genes, run_analyse

this_dir = os.path.dirname(os.path.abspath(__file__))
app = flask.Flask('webdorina',
                  template_folder=os.path.join(this_dir, 'templates'),
                  static_folder=os.path.join(this_dir, 'static'))
app.secret_key = os.urandom(24)
app.config.from_pyfile(os.path.join(this_dir, 'config.py'))
app.logger.addHandler(logging.getLogger('rq.worker'))

try:
    user_config = app.config.from_pyfile(sys.argv[1])
except FileNotFoundError:
    msg = 'Using app defaults, please provide a valid config file'
    app.logger.debug(msg)
except IndexError:
    pass

Genome.init(app.config['DATA_PATH'])
Regulator.init(app.config['DATA_PATH'])

conn = Redis(charset="utf-8", decode_responses=True)
# assert redis is running
conn.ping()


def _create_session(create_dir=False):
    unique_id = str(uuid.uuid4())
    session = "sessions:{0}".format(unique_id)
    session_dict = dict(uuid=unique_id, state='initialised')
    conn.setex(name=session,
               value=json.dumps(session_dict),
               time=app.config['SESSION_TTL'])
    if create_dir:
        os.mkdir(app.config['SESSION_STORE'].format(unique_id=unique_id))
    return unique_id


def _list_genomes():
    def without_assemblies(h):
        h1 = h.copy()
        del h1['assemblies']
        return h1

    genome_list = list(map(without_assemblies, Genome.all().values()))

    return genome_list


def _list_assemblies():
    assemblies = []
    for g in list(Genome.all().values()):
        for key, val in list(g['assemblies'].items()):
            val['id'] = key
            val['weight'] = int(key[2:])
            val['genome'] = g['id']
            assemblies.append(val)
    return assemblies


def _dict_to_bed(data):
    """Convert dorina dict to BED format"""
    chrom, coords = data['location'].split(':')
    start, end = coords.split('-')

    data['chrom'] = chrom
    data['start'] = start
    data['end'] = end

    return "{chrom}\t{start}\t{end}\t{data_source}" \
           "#{track}*{site}\t{score}\t{strand}".format(**data)


@app.context_processor
def inject_data():
    assemblies = [x['assemblies'] for x in Genome.all().values()]
    assemblies = (xx for x in assemblies for xx in x)
    return dict(_assemblies=assemblies)


@app.route('/')
def welcome():
    return render_template('welcome.html')


def count_columns(filename):
    with open(filename) as open_f:
        first_line = next(open_f).rstrip()
        data = first_line.split()
        return len(data)


@app.route('/search', methods=['GET', 'POST'])
def index():
    custom_regulator = 'false'
    if request.method == 'POST':
        uuid = _create_session(True)
        bedfile = request.files['bedfile']
        if bedfile and bedfile.filename.endswith('.bed'):
            filename = "{}.bed".format(uuid)
            dirname = app.config['SESSION_STORE'].format(unique_id=uuid)
            bedfile.save(os.path.join(dirname, filename))
            if count_columns(os.path.join(dirname, filename)) < 3:
                flash(u'Please upload a valid .bed '
                      u'file with at least three columns.', 'danger')
                return redirect(flask.url_for('index'))
            custom_regulator = 'true'
            flash(u'File {} loaded'.format(bedfile.filename), 'success')
        else:
            flash(u'Please upload a valid .bed '
                  u'file with at least six columns.', 'danger')
            return redirect(flask.url_for('index'))


    else:
        uuid = _create_session()

    genomes = json.dumps(_list_genomes())
    assemblies = json.dumps(_list_assemblies())
    return render_template('index.html', genomes=genomes,
                           assemblies=assemblies, uuid=uuid,
                           custom_regulator=custom_regulator)


@app.route('/api/v1.0/status/<uuid>')
def status(uuid):
    # uuid here shadows global uuid var,
    # but it seems a feature, not a bug
    key = "sessions:{0}".format(uuid)
    if conn.exists(key):
        _status = json.loads(conn.get(key))
        _status['ttl'] = conn.ttl(key)
    else:
        _status = dict(uuid=uuid, state='expired')

    return jsonify(_status)


@app.route('/api/v1.0/search', methods=['POST'])
def search():
    query = {'genes': request.form.getlist('genes[]')}

    if not query['genes']:
        query['genes'] = [u'all']

    query['match_a'] = request.form.get('match_a', u'any')
    query['region_a'] = request.form.get('region_a', u'any')
    query['genome'] = request.form.get('assembly', None)
    query['set_a'] = request.form.getlist('set_a[]')
    query['set_b'] = request.form.getlist('set_b[]')
    # werkzeug/Flask insists on returning an empty list, but dorina.analyse
    # expects 'None'
    if not query['set_b']:
        query['set_b'] = None
    query['match_b'] = request.form.get('match_b', u'any')
    query['region_b'] = request.form.get('region_b', u'any')
    query['combine'] = request.form.get('combinatorial_op', u'or')
    #query['tissue'] = request.form.getlist('tissue[]')
    #if not query['tissue']:
        #query['tissue'] = None

    window_a = request.form.get('window_a', -1, int)
    if window_a > -1:
        query['window_a'] = window_a
    window_b = request.form.get('window_b', -1, int)
    if window_b > -1:
        query['window_b'] = window_b

    query_key = "results:%s" % json.dumps(query, sort_keys=True)
    query_pending_key = "%s_pending" % query_key
    unique_id = request.form.get('uuid', u'invalid')
    session = "sessions:{}".format(unique_id)
    if unique_id == 'invalid' or not conn.exists(session):
        unique_id = _create_session()
        session = "sessions:{}".format(unique_id)

    if conn.exists(query_key):
        session_dict = dict(uuid=unique_id, state='done')
        conn.expire(query_key, app.config['RESULT_TTL'])
        conn.set(session, json.dumps(session_dict))
        conn.expire(session, app.config['SESSION_TTL'])
        conn.set("results:{0}".format(session),
                 json.dumps(dict(redirect=query_key)))
        conn.expire("results:{0}".format(session),
                    app.config['SESSION_TTL'])
        return jsonify(session_dict)

    elif query['genes'][0] != u'all':
        full_query = dict(query)
        full_query['genes'] = [u'all']
        full_query_key = "results:%s" % json.dumps(full_query, sort_keys=True)

        if conn.exists(full_query_key):
            conn.expire(full_query_key, app.config['RESULT_TTL'])
            conn.set(query_pending_key, True)
            conn.expire(query_pending_key, 30)
            session_dict = dict(state='pending', uuid=unique_id)
            conn.set('sessions:{0}'.format(unique_id),
                     json.dumps(session_dict))
            conn.expire(
                'sessions:{0}'.format(unique_id), app.config['SESSION_TTL'])
            q = Queue(connection=conn, default_timeout=600)

            q.enqueue(filter_genes, query['genes'], full_query_key, query_key,
                      query_pending_key, unique_id,
                      session_ttl=app.config['SESSION_TTL'],
                      result_ttl=app.config['RESULT_TTL'])
            return jsonify(session_dict)

    session_dict = dict(state='pending', uuid=unique_id)
    conn.set('sessions:{0}'.format(unique_id), json.dumps(session_dict))
    conn.expire('sessions:{0}'.format(unique_id),
                app.config['SESSION_TTL'])

    if conn.get(query_pending_key):
        return jsonify(session_dict)

    conn.set(query_pending_key, int(True))
    conn.expire(query_pending_key, 30)

    q = Queue(connection=conn, default_timeout=600)
    q.enqueue(run_analyse, app.config['DATA_PATH'], query_key,
              query_pending_key, query, unique_id,
              SESSION_STORE=app.config['SESSION_STORE'],
              RESULT_TTL=app.config['RESULT_TTL'],
              SESSION_TTL=app.config['SESSION_TTL'])

    return jsonify(session_dict)


@app.route('/api/v1.0/download/regulator/<assembly>/<name>')
def download_regulator(assembly, name):
    try:
        regulator = Regulator.from_name(name, assembly)
    except Exception as e:
        app.logger.error(e, assembly, name)
        return flask.abort(404)

    return send_file(regulator.path, as_attachment=True)


@app.route('/api/v1.0/download/results/<uuid>')
def download_results(uuid):
    key = "results:sessions:{0}".format(uuid)
    if not conn.exists(key):
        flask.abort(404)

    result_key = json.loads(conn.get(key))['redirect']
    result = '\n'.join(conn.lrange(result_key, 0, -1))
    return send_file(BytesIO(result.encode('utf-8')),
                     mimetype='text/tsv',
                     attachment_filename='carina_{}.txt'.format(uuid),
                     as_attachment=True)


@app.route('/modomics')
def modomics():
    return render_template('modomics.html')

@app.route('/news')
def news():
    return render_template('news.html')


@app.route('/tutorials')
def tutorials():
    return render_template('tutorials.html')


@app.route('/docs')
def docs():
    return render_template('api_docs.html')


@app.route('/acknowledgements')
def acknowledgements():
    return render_template('acknowledgements.html')


@app.route('/regulators/<assembly>')
def regulators(assembly=None):
    if assembly is None:
        return render_template('regulators.html')
    else:
        return render_template(
            'regulators_for_assembly.html', assembly=assembly)


@app.route('/docs/api/<page>')
def docs_api(page):
    return render_template('api_{}.html'.format(page))


@app.route('/api/v1.0/genomes')
def api_list_genomes():
    return jsonify(dict(genomes=_list_genomes()))


@app.route('/api/v1.0/assemblies/<genome>')
def api_list_assemblies(genome):
    assemblies = [x for x in _list_assemblies() if x['genome'] == genome]
    return jsonify(dict(assemblies=assemblies))


@app.route('/api/v1.0/regulators/<assembly>')
def list_regulators(assembly):
    cache_key = "regulators:{0}".format(assembly)
    if conn.exists(cache_key):
        regulators_ = json.loads(conn.get(cache_key))
    else:
        regulators_ = {}
        available_regulators = Regulator.all()
        for genome in available_regulators:
            if assembly in available_regulators[genome]:
                for key, val in list(
                        available_regulators[genome][assembly].items()):
                    regulators_[key] = val

                conn.set(cache_key, json.dumps(regulators_))
                conn.expire(cache_key, app.config['REGULATORS_TTL'])

    return jsonify(regulators_)


@app.route('/api/v1.0/genes/<assembly>', defaults={'query': ''})
@app.route('/api/v1.0/genes/<assembly>/<query>')
def list_genes(assembly, query):
    if query != '':
        start = "[{0}".format(query)
        end = "(" + start[1:-1] + chr(ord(start[-1]) + 1)
    else:
        start = "-"
        end = "+"

    cache_key = "genes:{0}".format(assembly)

    if not conn.exists(cache_key):
        new_genes = Genome.get_genes(assembly)
        for gene in new_genes:
            conn.zadd(cache_key, gene, 0)

    genes = conn.zrangebylex(cache_key, start, end)
    return jsonify(dict(genes=genes[:500]))


@app.route('/api/v1.0/result/<uuid>')
def get_result(uuid):
    key = "results:sessions:{0}".format(uuid)
    if not conn.exists(key):
        return jsonify(dict(uuid=uuid, state='expired'))

    rec = json.loads(conn.get(key))
    query_key = str(rec['redirect'])
    conn.expire(query_key, app.config['RESULT_TTL'])
    result = conn.lrange(query_key, 0, -1)
    if len(result) > 1000:
        return jsonify(
            dict(state='done', results=result[:999],
                 message='The result table was limited due to its size, '
                         'please limit your search query or use the download '
                         'button.',
                 total_results=len(result)))

    if 'Job failed' in result[0]:
        app.logger.error(result[0])
        return jsonify(
            dict(state='error', results=[], message=result[0], total_results=0))

    return jsonify(
        dict(state='done', results=result, total_results=len(result)))


#@app.route('/api/v1.0/tissues/<assembly>/')
#@app.route('/api/v1.0/tissues/<assembly>/<tissue>')
#def get_tissues(assembly, tissue=None):
    #path = app.config["DATA_PATH"] + '/{}_tissues.json'.format(assembly)
    #with open(path) as open_f:
        #genes_p_tissue = json.load(open_f)
    #if tissue is None:
        #return jsonify(dict(tissue=list(genes_p_tissue.keys())))
    #try:
        #return jsonify(dict(genes=genes_p_tissue[tissue]))
    #except KeyError:
        #return jsonify(dict(message='Tissue not found'))


if __name__ == "__main__":
    app.run(debug=app.config['DEBUG'], host=app.config['HOST'], port=app.config[
        'PORT'])
