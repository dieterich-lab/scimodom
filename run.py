import json
from redis import Redis
from dorina.run import analyse

def run_analyse(datadir, query_key, query_pending_key, query):
    redis_store = Redis()
    # get rid of the now-unused genes parameter
    query.pop('genes', None)
    result = analyse(datadir=datadir, **query)
    result.sort(key=lambda x: x['score'], reverse=True)

    print "returning %s rows" % len(result)

    if len(result) < 1:
        result.append({
            'data_source': 'no results found',
            'score': -1,
            'track': '',
            'gene': '',
            'site': '',
            'strand': '',
            'location': ''
        })

    for res in result:
        redis_store.rpush(query_key, json.dumps(res))


    redis_store.expire(query_key, 60)

    redis_store.delete(query_pending_key)


def filter(genes, full_query_key, query_key, query_pending_key):
    """Filter for a given set of gene names"""
    redis_store = Redis()

    full_results = redis_store.lrange(full_query_key, 0, -1)
    for res_string in full_results:
        res = json.loads(res_string)
        if res['gene'] in genes:
            redis_store.rpush(query_key, json.dumps(res))

    redis_store.expire(query_key, 60)
    redis_store.delete(query_pending_key)