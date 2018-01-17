#!/usr/bin/env python3
# coding=utf-8
from __future__ import unicode_literals

import json
import logging

from dorina import run
from redis import Redis

log = logging.getLogger('webdorina')


def run_analyse(datadir, query_key, query_pending_key, query, uuid):
    log.info('Running analysis for {}'.format(query_key))
    dorina = run.Dorina(datadir)

    from webdorina import RESULT_TTL, SESSION_TTL, SESSION_STORE
    redis_store = Redis(charset="utf-8", decode_responses=True)

    session_store = SESSION_STORE.format(unique_id=uuid)
    custom_regulator_file = '{session_store}/{uuid}.bed'.format(
        session_store=session_store, uuid=uuid)
    set_a = []
    for regulator in query['set_a']:
        if regulator == uuid:
            set_a.append(custom_regulator_file)
        else:
            set_a.append(regulator)
        query['set_a'] = set_a

    if query['set_b'] is not None:
        set_b = []
        for regulator in query['set_b']:
            if regulator == uuid:
                set_b.append(custom_regulator_file)
            else:
                set_b.append(regulator)
        query['set_b'] = set_b
    try:
        log.debug('Storing analysis result for {}'.format(query_key))
        result = str(dorina.analyse(**query))
    except Exception as e:
        result = '\t\t\t\t\t\t\t\tJob failed: %s' % str(e).replace(
            '\n', ' ').replace('\t', ' ')

    lines = result.split('\n')
    if lines[-1] == '':
        lines = lines[:-1]

    def get_score(x):
        cols = x.split('\t')
        if len(cols) < 14:
            return -1
        try:
            return float(cols[13])
        except ValueError:
            return -1

    lines.sort(key=get_score, reverse=True)

    num_results = len(lines)
    log.debug("returning {} rows".format(num_results))

    if num_results == 0:
        lines = ['\t\t\t\t\t\t\t\tNo results found']
        num_results += 1

    for i in range(0, num_results, 1000):
        res = lines[i:i + 1000]
        redis_store.rpush(query_key, *res)

    redis_store.expire(query_key, RESULT_TTL)
    redis_store.setex('sessions:{0}'.format(uuid), json.dumps(dict(
        state='done', uuid=uuid)), SESSION_TTL)
    redis_store.setex('results:sessions:{0}'.format(uuid), json.dumps(dict(
        redirect=query_key)), SESSION_TTL)

    redis_store.delete(query_pending_key)


def filter(genes, full_query_key, query_key, query_pending_key, uuid):
    """Filter for a given set of gene names"""
    from webdorina import RESULT_TTL, SESSION_TTL
    redis_store = Redis(charset="utf-8", decode_responses=True)

    full_results = redis_store.lrange(full_query_key, 0, -1)
    results = []
    for res_string in full_results:
        if res_string == '':
            continue
        cols = res_string.split('\t')
        annotations = cols[8]
        for field in annotations.split(';'):
            key, val = field.split('=')
            if key == 'ID' and val in genes:
                results.append(res_string)

    num_results = len(results)
    if num_results == 0:
        results.append('\t\t\t\t\t\t\t\tNo results found')
        num_results += 1

    for i in range(0, num_results, 1000):
        res = results[i:i + 1000]
        redis_store.rpush(query_key, *res)

    redis_store.expire(query_key, RESULT_TTL)
    redis_store.delete(query_pending_key)

    redis_store.setex('sessions:{0}'.format(uuid), json.dumps(dict(
        state='done', uuid=uuid)), SESSION_TTL)
    redis_store.setex('results:sessions:{0}'.format(uuid), json.dumps(dict(
        redirect=query_key)), SESSION_TTL)
