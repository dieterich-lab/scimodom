#!/usr/bin/env python
# -*- coding: utf-8
"""
Created on 15:57 18/01/2018 2018 

"""
import json
import logging

from dorina import run
from redis import Redis

logger = logging.getLogger('app')


def run_analyse(datadir, query_key, query_pending_key, query, uuid,
                SESSION_STORE=None, RESULT_TTL=None, SESSION_TTL=None,
                tissue=None):
    logger.info('Running analysis for {}'.format(query_key))
    if tissue:
        dorina = run.Dorina(datadir, ext=tissue)
    else:
        dorina = run.Dorina(datadir)

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
        logger.debug('Storing analysis result for {}'.format(query_key))
        result = str(dorina.analyse(**query))
        lines = result.splitlines()
        logger.debug("returning {} rows".format(len(lines)))
        redis_store.rpush(query_key, *lines)

        #ilogger.info(f"uuid={uuid}, dict={json.dumps(dict(redirect=query_key))}, SESSION_TTL={SESSION_TTL}")
        #print(f"++++++++++++++++uuid={uuid}, dict={json.dumps(dict(redirect=query_key))}, SESSION_TTL={SESSION_TTL}")

        #redis_store.setex('results:sessions:{0}'.format(uuid), json.dumps(dict(
        #    redirect=query_key)), SESSION_TTL)
        redis_store.setex('results:sessions:{0}'.format(uuid), SESSION_TTL, json.dumps(dict(
            redirect=query_key)))
    except Exception as e:
        result = 'Job failed: %s' % str(e)
        

        logger.info(f">>>>>>>>>>>>>>>>>>> uuid={uuid}, dict={json.dumps(dict(state='error', uuid=uuid))}, SESSION_TTL={SESSION_TTL}")
        print(f">>>>>>>>>>>>>>>>>>> uuid={uuid}, dict={json.dumps(dict(state='error', uuid=uuid))}, SESSION_TTL={SESSION_TTL}")

        #redis_store.setex('sessions:{0}'.format(uuid), json.dumps(dict(
        #    state='error', uuid=uuid)), SESSION_TTL)
        redis_store.setex('sessions:{0}'.format(uuid), SESSION_TTL, json.dumps(dict(
            state='error', uuid=uuid)))
        redis_store.rpush(query_key, result)

    redis_store.expire(query_key, RESULT_TTL)
    #redis_store.setex('sessions:{0}'.format(uuid), json.dumps(dict(
    #    state='done', uuid=uuid)), SESSION_TTL)
    redis_store.setex('sessions:{0}'.format(uuid), SESSION_TTL, json.dumps(dict(
        state='done', uuid=uuid)))
    redis_store.delete(query_pending_key)


def filter_genes(genes, full_query_key, query_key, query_pending_key, uuid,
                 session_ttl=None, result_ttl=None):
    """Filter for a given set of gene names"""
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
    if num_results:
        for i in range(0, num_results, 1000):
            res = results[i:i + 1000]
            redis_store.rpush(query_key, *res)
    else:
        redis_store.rpush(query_key, [])

    redis_store.expire(query_key, result_ttl)
    redis_store.delete(query_pending_key)

    #redis_store.setex('sessions:{0}'.format(uuid), json.dumps(dict(
    #    state='done', uuid=uuid)), session_ttl)
    redis_store.setex('sessions:{0}'.format(uuid), session_ttl, json.dumps(dict(
        state='done', uuid=uuid)))
    #redis_store.setex('results:sessions:{0}'.format(uuid), json.dumps(dict(
    #    redirect=query_key)), session_ttl)
    redis_store.setex('results:sessions:{0}'.format(uuid), session_ttl, json.dumps(dict(
        redirect=query_key)))
