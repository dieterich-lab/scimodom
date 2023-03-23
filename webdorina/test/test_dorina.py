#!/usr/bin/env python
# coding=utf-8

from __future__ import unicode_literals
import json
import os
import unittest
import doctest

import fakeredis
from flask_testing import TestCase
from minimock import Mock, mock, restore, TraceTracker

import webdorina.workers as run
import webdorina.app as webdorina
from dorina.regulator import Regulator

doctest.testmod(verbose=True, optionflags=doctest.ELLIPSIS)


class RedisStore(object):

    def __init__(self, name, tracker=None):
        self.name = name
        self.tt = tracker
        self.connection = fakeredis.FakeRedis(decode_responses=True)

    def __getattr__(self, attr):
        def wrapped_call(*args, **kwargs):
            if self.tt is not None:
                name = "{0}.{1}".format(self.name, attr)
                self.tt.call(name, *args, **kwargs)
                return getattr(self.connection, attr)(*args, **kwargs)

        return wrapped_call


class RunTestCase(unittest.TestCase):
    def setUp(self):
        self.maxDiff = None
        run.Redis = fakeredis.FakeRedis
        self.r = fakeredis.FakeStrictRedis(decode_responses=True)
        self.tt = TraceTracker()
        self.return_value = ''
        mock('run.run.Dorina.analyse', tracker=self.tt,
             returns_func=self.get_return_value)
        self.data_dir = os.path.join(os.path.dirname(__file__), 'data')

    def tearDown(self):
        self.r.flushdb()
        restore()

    def get_return_value(self, *args, **kwargs):
        return self.return_value

    def test_run_analyse(self):
        """Test run_analyze()"""
        expected_trace = '''Called run.run.Dorina.analyse(
    genome='hg19',
    match_a='any',
    region_a='any',
    set_a=['scifi'],
    set_b=None)'''

        query = dict(genome='hg19', set_a=['scifi'], match_a='any',
                     region_a='any', set_b=None)

        self.return_value = u"""chr1	doRiNA2	gene	1	1000	.	+	.	ID=gene01.01	chr1	250	260	PARCLIP#scifi*scifi_cds	5	+
chr1	doRiNA2	gene	2001	3000	.	+	.	ID=gene01.02	chr1	2350	2360	PARCLIP#scifi*scifi_intron	6	+"""

        run.run_analyse(self.data_dir, 'results:fake_key',
                        'results:fake_key_pending', query, 'fake-uuid')
        # TODO restest with mock
        # assert_same_trace(self.tt, expected_trace)
        self.assertTrue(self.r.exists('results:fake_key'))
        self.assertEqual(2, self.r.llen('results:fake_key'))
        expected = str(self.return_value).split('\n')
        expected.sort(key=lambda x: float(x.split('\t')[13]), reverse=True)
        self.assertEqual(expected, self.r.lrange('results:fake_key', 0, -1))
        self.assertTrue(self.r.exists('sessions:fake-uuid'))
        self.assertEqual(json.loads(self.r.get('sessions:fake-uuid')),
                         dict(uuid='fake-uuid', state='done'))
        self.assertTrue(self.r.exists('results:sessions:fake-uuid'))
        self.assertEqual(json.loads(self.r.get('results:sessions:fake-uuid')),
                         dict(redirect="results:fake_key"))

    def test_run_analyse_no_results(self):
        """Test run_analyze() when no results are returned"""
        query = dict(genome='hg19', set_a=['scifi'], match_a='any',
                     region_a='any', set_b=None)

        self.return_value = ''

        run.run_analyse(self.data_dir, 'results:fake_key',
                        'results:fake_key_pending', query, 'fake-uuid')
        expected = ['\t\t\t\t\t\t\t\tNo results found']

        self.assertTrue(self.r.exists('results:fake_key'))
        self.assertEqual(1, self.r.llen('results:fake_key'))
        self.assertEqual(expected, self.r.lrange('results:fake_key', 0, -1))

    def test_run_analyse_custom_regulator(self):
        """Test run_analyze() with a custom regulator"""
        session_store = webdorina.SESSION_STORE.format(unique_id='fake-uuid')
        expected_trace = '''Called run.run.Dorina.analyse(
    genome='hg19',
    match_a='any',
    region_a='any',
    set_a=['scifi', '{session_store}/fake-uuid.bed'],
    set_b=None)'''.format(session_store=session_store)

        query = dict(genome='hg19', set_a=['scifi', 'fake-uuid'], match_a='any',
                     region_a='any', set_b=None)

        self.intron_ = """chr1	doRiNA2	gene	1	1000	.	+	.	ID=gene01.01	chr1	250	260	PARCLIP#scifi*scifi_cds	5	+
chr1	doRiNA2	gene	2001	3000	.	+	.	ID=gene01.02	chr1	2350	2360	PARCLIP#scifi*scifi_intron	6	+"""
        self.self_intron_ = self.intron_
        self.return_value = self.self_intron_

        run.run_analyse(self.data_dir, 'results:fake_key',
                        'results:fake_key_pending', query, 'fake-uuid')
        expected = self.return_value.split('\n')
        expected.sort(key=lambda x: float(x.split('\t')[13]), reverse=True)

        #  TODO retest with mock
        # assert_same_trace(self.tt, expected_trace)

        self.assertTrue(self.r.exists('results:fake_key'))
        self.assertEqual(2, self.r.llen('results:fake_key'))
        self.assertEqual(expected, self.r.lrange('results:fake_key', 0, -1))

        self.assertTrue(self.r.exists('sessions:fake-uuid'))
        self.assertEqual(json.loads(self.r.get('sessions:fake-uuid')),
                         dict(uuid='fake-uuid', state='done'))

        self.assertTrue(self.r.exists('results:sessions:fake-uuid'))
        self.assertEqual(json.loads(self.r.get('results:sessions:fake-uuid')),
                         dict(redirect="results:fake_key"))

    def test_filter(self):
        """Test filter()"""

        data = [
            'chr1	doRiNA2	gene	1	1000	.	+	.	ID=gene01.01	chr1	250	260	PARCLIP#scifi*scifi_cds	6	+',
            'chr1	doRiNA2	gene	2001	3000	.	+	.	ID=gene01.02	chr1	2350	2360	PARCLIP#scifi*scifi_intron	5	+',
            'chr1	doRiNA2	gene	3001	4000	.	+	.	ID=gene01.03	chr1	3350	3360	PARCLIP#scifi*scifi_intron	7	+'
        ]

        for d in data:
            self.r.rpush('results:fake_full_key', d)

        run.filter(['gene01.01', 'gene01.02'], 'results:fake_full_key',
                   'results:fake_key', 'results:fake_key_pending', 'fake-uuid')

        data.pop()

        self.assertTrue(self.r.exists('results:fake_key'))
        self.assertEqual(2, self.r.llen('results:fake_key'))
        self.assertEqual(data, self.r.lrange('results:fake_key', 0, -1))

        self.assertTrue(self.r.exists('results:sessions:fake-uuid'))


class DorinaTestCase(TestCase):
    def create_app(self):
        self.app = webdorina.app
        return self.app

    def setUp(self):
        self.maxDiff = None
        self.tt = TraceTracker()
        webdorina.datadir = os.path.join(os.path.dirname(__file__), 'data')
        webdorina.conn = RedisStore('fake_store', self.tt)
        self.r = webdorina.conn.connection
        fake_queue = Mock('webdorina.Queue', tracker=self.tt)
        mock('webdorina.Queue', tracker=self.tt, returns=fake_queue)
        # use tracker=None to not track uuid4() calls
        mock('webdorina.uuid.uuid4', tracker=None, returns="fake-uuid")
        self.Regulator = Regulator.init(webdorina.datadir)

    def tearDown(self):
        self.r.flushdb()
        self.Regulator = None
        restore()

    def test_index(self):
        """Test if index page displays"""
        rv = self.client.get('/')
        assert b"doRiNA" in rv.data

    def test_list_regulators(self):
        """Test list_regulators()"""
        all_regulators = Regulator.all()
        expected = all_regulators['h_sapiens']['hg19']
        # file path isn't shown
        for val in list(expected.values()):
            del val['file']
        rv = self.client.get('/api/v1.0/regulators/hg19')
        self.assertDictEqual(rv.json, expected)
        rv = self.client.get('/api/v1.0/regulators/at3')
        self.assertEqual(rv.json, dict())

    def test_search_nothing_cached(self):
        """Test search() with nothing in cache"""
        self.r.set('sessions:fake-uuid',
                   json.dumps(dict(uuid='fake-uuid', state='done')))
        data = dict(match_a='any', assembly='hg19', uuid='fake-uuid')
        data['set_a[]'] = ['scifi']
        key = 'results:{"combine": "or", "genes": ["all"], "genome": "hg19", '
        key += '"match_a": "any", "match_b": "any", "region_a": "any", '
        key += '"region_b": "any", "set_a": ["scifi"], "set_b": null}'
        key_pending = '{0}_pending'.format(key)

        rv = self.client.post('/api/v1.0/search', data=data)

        # Now a query should be pending
        self.assertTrue(self.r.exists(key_pending))

        # A session should have been created as well
        self.assertTrue(self.r.exists('sessions:fake-uuid'))

        ttl = self.r.ttl(key_pending)
        self.assertGreater(ttl, 0)
        self.assertLessEqual(ttl, webdorina.RESULT_TTL)

        self.assertEqual(rv.json, dict(uuid='fake-uuid', state="pending"))

        # This query should trigger a defined set of calls
        expected_trace = '''Called fake_store.exists('sessions:fake-uuid')
Called fake_store.exists(
    '{0}')
Called fake_store.set(
    'sessions:fake-uuid',
    '{{"state": "pending", "uuid": "fake-uuid"}}')
Called fake_store.expire('sessions:fake-uuid', {4})
Called fake_store.get(
    '{1}')
Called fake_store.set(
    '{1}',
    True)
Called fake_store.expire(
    '{1}',
    30)
Called webdorina.Queue(
    connection=<fakeredis.FakeRedis object at ...>,
    default_timeout=600)
Called webdorina.Queue.enqueue(
    <function run_analyse at ...>,
    '{2}',
    '{0}',
    '{1}',
    {{{3}}},
    u'fake-uuid')'''.format(key, key_pending, webdorina.datadir,
                            "'genes': [u'all'], 'match_a': u'any', 'match_b': u'any', 'combine': u'or', 'genome': u'hg19', 'region_a': u'any', 'set_a': [u'scifi'], 'set_b': None, 'region_b': u'any'",
                            webdorina.SESSION_TTL)

        #  TODO restest with mock
        # assert_same_trace(self.tt, expected_trace)

    def test_search_query_pending(self):
        """Test search() with a query for this key pending"""
        self.r.set('sessions:fake-uuid',
                   json.dumps(dict(uuid='fake-uuid', state='done')))
        key = 'results:{"combine": "or", "genes": ["all"], "genome": "hg19", '
        key += '"match_a": "any", "match_b": "any", "region_a": "any", '
        key += '"region_b": "any", "set_a": ["scifi"], "set_b": null}'
        key_pending = '{0}_pending'.format(key)
        self.r.set(key_pending, True)

        data = dict(match_a='any', assembly='hg19', uuid='fake-uuid')
        data['set_a[]'] = ['scifi']
        rv = self.client.post('/api/v1.0/search', data=data)

        # Should return "pending"
        self.assertEqual(rv.json, dict(uuid='fake-uuid', state="pending"))

        # This query should trigger a defined set of calls
        expected_trace = '''Called fake_store.exists('sessions:fake-uuid')
Called fake_store.exists(
    '{0}')
Called fake_store.set(
    'sessions:fake-uuid',
    '{{"state": "pending", "uuid": "fake-uuid"}}')
Called fake_store.expire('sessions:fake-uuid', {2})
Called fake_store.get(
    '{1}')'''.format(key, key_pending, webdorina.SESSION_TTL)
        #  TODO MOCK
        # assert_same_trace(self.tt, expected_trace)

    def test_search_cached_results(self):
        """Test search() with cached_results"""
        key = 'results:{"combine": "or", "genes": ["all"], "genome": "hg19", '
        key += '"match_a": "any", "match_b": "any", "region_a": "any", '
        key += '"region_b": "any", "set_a": ["scifi"], "set_b": null}'
        results = [
            'chr1	doRiNA2	gene	1	1000	.	+	.	ID=gene01.01	chr1	250	260	PARCLIP#scifi*scifi_cds	6	+	250	260',
            'chr1	doRiNA2	gene	2001	3000	.	+	.	ID=gene01.02	chr1	2350	2360	PARCLIP#scifi*scifi_intron	5	+	2350	2360',
            'chr1	doRiNA2	gene	3001	4000	.	+	.	ID=gene01.03	chr1	3350	3360	PARCLIP#scifi*scifi_intron	7	+	3350	3360'
        ]
        for res in results:
            self.r.rpush(key, res)

        self.r.set('sessions:fake-uuid',
                   json.dumps(dict(state='done', uuid='fake-uuid')))

        data = dict(match_a='any', assembly='hg19', uuid='fake-uuid')
        data['set_a[]'] = ['scifi']
        rv = self.client.post('/api/v1.0/search', data=data)

        self.assertEqual(rv.json, dict(state='done', uuid="fake-uuid"))

        rv = self.client.get('/api/v1.0/result/fake-uuid')
        expected = dict(state='done', results=results, more_results=False,
                        next_offset=100, total_results=3)
        self.assertEqual(rv.json, expected)

        # This query should trigger a defined set of calls
        expected_trace = '''Called fake_store.exists('sessions:fake-uuid')
Called fake_store.exists(
    '{0}')
Called fake_store.expire(
    '{0}',
    {1})
Called fake_store.set(
    'sessions:{3}',
    '{{"uuid": "{3}", "state": "done"}}')
Called fake_store.expire('sessions:{3}', {4})
Called fake_store.set(
    'results:sessions:{3}',
    {5!r})
Called fake_store.expire('results:sessions:{3}', {4})
Called fake_store.exists('results:sessions:{3}')
Called fake_store.get('results:sessions:{3}')
Called fake_store.expire(
    '{0}',
    {1})
Called fake_store.lrange(
    '{0}',
    0,
    {2})
Called fake_store.llen(
    '{0}')
    '''.format(key, webdorina.RESULT_TTL, webdorina.MAX_RESULTS - 1,
               'fake-uuid', webdorina.SESSION_TTL,
               json.dumps(dict(redirect=key)))

        # TODO retest using MOCK
        # assert_same_trace(self.tt, expected_trace)

    def test_search_nothing_cached_all_regulators(self):
        """Test search() for all regulators with nothing in cache"""
        self.r.set('sessions:fake-uuid',
                   json.dumps(dict(uuid='fake-uuid', state='done')))
        data = dict(match_a='all', assembly='hg19', uuid='fake-uuid')
        data['set_a[]'] = ['scifi', 'fake01']
        rv = self.client.post('/api/v1.0/search', data=data)
        key = 'results:{"combine": "or", "genes": ["all"], "genome": "hg19", '
        key += '"match_a": "all", "match_b": "any", "region_a": "any", '
        key += '"region_b": "any", "set_a": ["scifi", "fake01"], "set_b": null}'
        key_pending = '{0}_pending'.format(key)

        # Now a query should be pending
        self.assertTrue(self.r.exists(key_pending))

        ttl = self.r.ttl(key_pending)
        self.assertGreater(ttl, 0)
        self.assertLessEqual(ttl, webdorina.RESULT_TTL)

        self.assertEqual(rv.json, dict(uuid='fake-uuid', state="pending"))

        # This query should trigger a defined set of calls
        expected_trace = '''Called fake_store.exists('sessions:fake-uuid')
Called fake_store.exists(
    '{0}')
Called fake_store.set(
    'sessions:fake-uuid',
    '{{"state": "pending", "uuid": "fake-uuid"}}')
Called fake_store.expire('sessions:fake-uuid', {4})
Called fake_store.get(
    '{1}')
Called fake_store.set(
    '{1}',
    True)
Called fake_store.expire(
    '{1}',
    30)
Called webdorina.Queue(
    connection=<fakeredis.FakeRedis object at ...>,
    default_timeout=600)
Called webdorina.Queue.enqueue(
    <function run_analyse at ...>,
    '{2}',
    '{0}',
    '{1}',
    {{{3}}},
    u'fake-uuid')'''.format(key, key_pending, webdorina.datadir,
                            "'genes': [u'all'], 'match_a': u'all', 'match_b': u'any', 'combine': u'or', 'genome': u'hg19', 'region_a': u'any', 'set_a': [u'scifi', u'fake01'], 'set_b': None, 'region_b': u'any'",
                            webdorina.SESSION_TTL)

        #  MOCK
        # assert_same_trace(self.tt, expected_trace)

    def test_search_nothing_cached_CDS_region(self):
        """Test search() in CDS regions with nothing in cache"""
        self.r.set('sessions:fake-uuid',
                   json.dumps(dict(uuid='fake-uuid', state='done')))
        data = dict(match_a='any', region_a='CDS', assembly='hg19',
                    uuid='fake-uuid')
        data['set_a[]'] = ['scifi', 'fake01']
        key = 'results:{"combine": "or", "genes": ["all"], "genome": "hg19", '
        key += '"match_a": "any", "match_b": "any", "region_a": "CDS", '
        key += '"region_b": "any", "set_a": ["scifi", "fake01"], "set_b": null}'
        key_pending = '{0}_pending'.format(key)

        rv = self.client.post('/api/v1.0/search', data=data)

        # Now a query should be pending
        self.assertTrue(self.r.exists(key_pending))

        ttl = self.r.ttl(key_pending)
        self.assertGreater(ttl, 0)
        self.assertLessEqual(ttl, webdorina.RESULT_TTL)

        self.assertEqual(rv.json, dict(uuid='fake-uuid', state="pending"))

        # This query should trigger a defined set of calls
        expected_trace = '''Called fake_store.exists('sessions:fake-uuid')
Called fake_store.exists(
    '{0}')
Called fake_store.set(
    'sessions:fake-uuid',
    '{{"state": "pending", "uuid": "fake-uuid"}}')
Called fake_store.expire('sessions:fake-uuid', {4})
Called fake_store.get(
    '{1}')
Called fake_store.set(
    '{1}',
    True)
Called fake_store.expire(
    '{1}',
    30)
Called webdorina.Queue( # doctest: +ELLIPSIS
    connection=<fakeredis.FakeRedis object at ...>,
    default_timeout=600) 
Called webdorina.Queue.enqueue( # doctest:+ELLIPSIS  
    <function run_analyse at ...>,
    '{2}',
    '{0}',
    '{1}',
     {3},
    'fake-uuid')'''
        query = {'genes': ['all'], 'match_a': 'any', 'match_b': 'any',
                 'combine': 'or', 'genome': 'hg19', 'set_a': ['scifi', 'fake01']
                 , 'set_b': None, 'region_b': 'any'}
        # TODO MOCK
        # assert_same_trace(self.tt, expected_trace.format(
        #     key, key_pending, webdorina.datadir, repr(query),
        #     webdorina.SESSION_TTL))

    def test_search_filtered_results_cached(self):
        """Test search() with filtered results in cache"""
        key = 'results:{"combine": "or", "genes": ["fake01"], "genome": "hg19", '
        key += '"match_a": "any", "match_b": "any", "region_a": "any", '
        key += '"region_b": "any", "set_a": ["scifi"], "set_b": null}'
        results = [
            'chr1	doRiNA2	gene	1	1000	.	+	.	ID=gene01.01	chr1	250	260	PARCLIP#scifi*scifi_cds	6	+'
        ]
        for res in results:
            self.r.rpush(key, res)

        self.r.set('sessions:fake-uuid',
                   json.dumps(dict(uuid='fake-uuid', state='done')))

        data = dict(match_a='any', assembly='hg19', uuid='fake-uuid')
        data['genes[]'] = ['fake01']
        data['set_a[]'] = ['scifi']
        rv = self.client.post('/api/v1.0/search', data=data)

        self.assertEqual(rv.json, dict(state='done', uuid="fake-uuid"))

        rv = self.client.get('/api/v1.0/result/fake-uuid')
        expected = dict(state='done', results=results, more_results=False,
                        next_offset=100, total_results=1)
        self.assertEqual(rv.json, expected)

        # This query should trigger a defined set of calls
        expected_trace = '''Called fake_store.exists('sessions:fake-uuid')
Called fake_store.exists(
    '{0}')
Called fake_store.expire(
    '{0}',
    {1})
Called fake_store.set(
    'sessions:fake-uuid',
    '{{"uuid": "fake-uuid", "state": "done"}}')
Called fake_store.expire('sessions:fake-uuid', {3})
Called fake_store.set(
    'results:sessions:fake-uuid',
    {4!r})
Called fake_store.expire('results:sessions:fake-uuid', {3})
Called fake_store.exists('results:sessions:fake-uuid')
Called fake_store.get('results:sessions:fake-uuid')
Called fake_store.expire(
    '{0}',
    {1})
Called fake_store.lrange(
    '{0}',
    0,
    {2})
Called fake_store.llen(
    '{0}')
    '''.format(key, webdorina.RESULT_TTL, webdorina.MAX_RESULTS - 1,
               webdorina.SESSION_TTL, json.dumps(dict(redirect=key)))
        # assert_same_trace(self.tt, expected_trace) TODO MOCK


    def test_search_filtered_full_results_cached(self):
        """Test search() with filter and full results in cache"""
        templ = 'results:{{"combine": "or", "genes": ["{0}"], "genome": "hg19", '
        templ += '"match_a": "any", "match_b": "any", "region_a": "any", '
        templ += '"region_b": "any", "set_a": ["scifi"], "set_b": null}}'
        full_key = templ.format('all')
        key = templ.format('fake01')
        key_pending = '{0}_pending'.format(key)
        results = [
            'chr1	doRiNA2	gene	1	1000	.	+	.	ID=gene01.01	chr1	250	260	PARCLIP#scifi*scifi_cds	6	+',
            'chr1	doRiNA2	gene	2001	3000	.	+	.	ID=gene01.02	chr1	2350	2360	PARCLIP#scifi*scifi_intron	5	+'
        ]
        for res in results:
            self.r.rpush(full_key, res)

        self.r.set('sessions:fake-uuid',
                   json.dumps(dict(uuid='fake-uuid', state='done')))

        data = dict(match_a='any', assembly='hg19', uuid='fake-uuid')
        data['genes[]'] = ['fake01']
        data['set_a[]'] = ['scifi']
        rv = self.client.post('/api/v1.0/search', data=data)

        # Now a query should be pending
        self.assertTrue(self.r.exists(key_pending))

        self.assertEqual(rv.json, dict(uuid='fake-uuid', state="pending"))

        # now pretend the filtering finished
        results.pop()
        self.r.set('results:sessions:fake-uuid', json.dumps(dict(redirect=key)))
        for res in results:
            self.r.rpush(key, res)

        rv = self.client.get('/api/v1.0/result/fake-uuid')
        expected = dict(state='done', results=results, more_results=False,
                        next_offset=100, total_results=1)
        self.assertEqual(rv.json, expected)

        # This query should trigger a defined set of calls
        expected_trace = '''Called fake_store.exists('sessions:fake-uuid')
Called fake_store.exists(
    '{0}')
Called fake_store.exists(
    '{2}')
Called fake_store.expire(
    '{2}',
    {3})
Called fake_store.set(
    '{1}',
    True)
Called fake_store.expire(
    '{1}',
    30)
Called fake_store.set(
    'sessions:fake-uuid',
    '{{"state": "pending", "uuid": "fake-uuid"}}')
Called fake_store.expire('sessions:fake-uuid', {5})
Called webdorina.Queue(
    connection=<fakeredis.FakeRedis object at ...>,
    default_timeout=600)
Called webdorina.Queue.enqueue(
    <function filter at ...>,
    [u'fake01'],
    '{2}',
    '{0}',
    '{1}',
    'fake-uuid')
Called fake_store.exists('results:sessions:fake-uuid')
Called fake_store.get('results:sessions:fake-uuid')
Called fake_store.expire(
    '{0}',
    {3})
Called fake_store.lrange(
    '{0}',
    0,
    {4})
Called fake_store.llen(
    '{0}')'''.format(key, key_pending, full_key, webdorina.RESULT_TTL,
                     webdorina.MAX_RESULTS - 1, webdorina.SESSION_TTL)
        # TODO retest with MOCK
        # assert_same_trace(self.tt, expected_trace)

    def test_search_filtered_results_nothing_cached(self):
        '''Test search() with filtered results without anything in cache'''
        full_key = 'results:{"combine": "or", "genes": ["all"], "genome": "hg19", '
        full_key += '"match_a": "any", "match_b": "any", "region_a": "any", '
        full_key += '"region_b": "any", "set_a": ["scifi"], "set_b": null}'

        self.r.set('sessions:fake-uuid',
                   json.dumps(dict(uuid='fake-uuid', state='pending')))

        data = dict(match_a='any', assembly='hg19', uuid='fake-uuid')
        data['genes[]'] = ['fake01']
        data['set_a[]'] = ['scifi']
        rv = self.client.post('/api/v1.0/search', data=data)

        self.assertEqual(rv.json, dict(state='pending', uuid="fake-uuid"))

        # now pretend the search finished
        key = 'results:{"combine": "or", "genes": ["fake01"], "genome": "hg19", '
        key += '"match_a": "any", "match_b": "any", "region_a": "any", '
        key += '"region_b": "any", "set_a": ["scifi"], "set_b": null}'
        results = [
            'chr1	doRiNA2	gene	1	1000	.	+	.	ID=gene01.01	chr1	250	260	PARCLIP#scifi*scifi_cds	6	+'
        ]
        for res in results:
            self.r.rpush(key, res)

        self.r.set('results:sessions:fake-uuid', json.dumps(dict(redirect=key)))
        self.r.set('sessions:fake-uuid',
                   json.dumps(dict(uuid='fake-uuid', state='done')))

        rv = self.client.get('/api/v1.0/result/fake-uuid')
        expected = dict(state='done', results=results, more_results=False,
                        next_offset=100, total_results=1)
        self.assertEqual(rv.json, expected)

        query = "{'genes': [u'fake01'], 'match_a': u'any', 'match_b': u'any', 'combine': u'or', 'genome': u'hg19', 'region_a': u'any', 'set_a': [u'scifi'], 'set_b': None, 'region_b': u'any'}"

        # This query should trigger a defined set of calls
        expected_trace = '''Called fake_store.exists('sessions:fake-uuid')
Called fake_store.exists(
    '{query_key}')
Called fake_store.exists(
    '{full_query_key}')
Called fake_store.set(
    'sessions:fake-uuid',
    '{{"state": "pending", "uuid": "fake-uuid"}}')
Called fake_store.expire('sessions:fake-uuid', {session_ttl})
Called fake_store.get(
    '{key_pending}')
Called fake_store.set(
    '{key_pending}',
    True)
Called fake_store.expire(
    '{key_pending}',
    30)
Called webdorina.Queue(
    connection=<fakeredis.FakeRedis object at ...>,
    default_timeout=600)
Called webdorina.Queue.enqueue(  
    <function run_analyse at ...>,
    '{datadir}',
    '{query_key}',
    '{key_pending}',
    {query},
    u'fake-uuid')
Called fake_store.exists('results:sessions:fake-uuid')
Called fake_store.get('results:sessions:fake-uuid')
Called fake_store.expire(
    '{query_key}',
    {result_ttl})
Called fake_store.lrange(
    '{query_key}',
    0,
    {max_results})
Called fake_store.llen(
    '{query_key}')'''.format(query_key=key, result_ttl=webdorina.RESULT_TTL,
                             max_results=(webdorina.MAX_RESULTS - 1),
                             session_ttl=webdorina.SESSION_TTL,
                             redirect_key=json.dumps(dict(redirect=key)),
                             full_query_key=full_key,
                             key_pending=(key + "_pending"),
                             datadir=webdorina.datadir, query=query)
        # TODO retest with mock
        # assert_same_trace(self.tt, expected_trace)

    def test_status(self):
        '''Test status()'''
        got = self.client.get('/api/v1.0/status/invalid')
        self.assertEqual(got.json, dict(uuid='invalid', state='expired'))

        valid = dict(uuid='valid', state='done')
        self.r.set('sessions:valid', json.dumps(valid))
        got = self.client.get('/api/v1.0/status/valid')
        valid['ttl'] = self.r.ttl('sessions:valid')
        self.assertEqual(got.json, valid)

    def test_genes(self):
        """Test list_genes()"""
        expected = dict(genes=['gene01.01', 'gene01.02'])
        fakeredis.FakeRedis.zrangebylex = Mock(
            'zrangebylex', returns=['gene01.01', 'gene01.02'], tracker=self.tt)
        got = self.client.get('/api/v1.0/genes/hg19')
        
        self.assertEqual(got.json, expected)

    def test_download_regulator(self):
        """Test download_regulator()"""

        got = self.client.get('/api/v1.0/download/regulator/hg19/PARCLIP_scifi')

        expected_file = Regulator.from_name("PARCLIP_scifi", "hg19").basename
        with open(expected_file + '.bed', encoding="utf-8") as fh:
            expected = fh.read()

        self.assertEqual(got.status_code, 200)
        self.assertSequenceEqual(got.data.decode('utf8'), expected)

    def test_invalid_regulator(self):
        got = self.client.get('/api/v1.0/download/regulator/hg19/invalid')
        self.assertEqual(got.status_code, 404)

    def test_download_results(self):
        """Test download_results()"""
        got = self.client.get('/api/v1.0/download/results/invalid')
        self.assertEqual(got.status_code, 404)

        key = 'results:{"combine": "or", "genes": ["all"], "genome": "hg19", '
        key += '"match_a": "any", "match_b": "any", "region_a": "any", '
        key += '"region_b": "any", "set_a": ["scifi"], "set_b": null}'
        res = ['chr1	doRiNA2	gene	1	1000	.	+	.	ID=gene01.01	chr1	250	260	PARCLIP#scifi*scifi_cds	6	+	250	260']

        self.r.rpush(key, res)
        self.r.set('results:sessions:fake-uuid', json.dumps(dict(redirect=key)))

        got = self.client.get('/api/v1.0/download/results/fake-uuid')

        expected = "{}\n".format(res)
        self.assertEqual(got.data.decode('utf8'), expected)

    def test_dict_to_bed(self):
        """Test _dict_to_bed()"""
        data = {'data_source': 'PARCLIP', 'score': 1000, 'track': 'scifi_hg19',
                'gene': 'gene01.02', 'site': 'fake', 'strand': '-',
                'location': 'chr1:23-42'}
        expected = "chr1	23	42	PARCLIP#scifi_hg19*fake	1000	-"

        got = webdorina._dict_to_bed(data)
        self.assertEqual(got, expected)


