#!/usr/bin/env python3
# coding: utf-8
"""
partitioning_test.py
        Various stuff that looks out of place in regression tests

        Copyright (c) 2015-2017, Postgres Professional
"""

import json
import math
import os
import re
import subprocess
import threading
import time
import unittest
<<<<<<< HEAD

from distutils.version import LooseVersion
from testgres import get_new_node, get_bin_path, get_pg_version

# set setup base logging config, it can be turned on by `use_logging`
# parameter on node setup

import logging
import logging.config

logfile = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'tests.log')
LOG_CONFIG = {
    'version': 1,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'base_format',
            'level': logging.DEBUG,
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': logfile,
            'formatter': 'base_format',
            'level': logging.DEBUG,
        },
    },
    'formatters': {
        'base_format': {
            'format': '%(node)-5s: %(message)s',
        },
    },
    'root': {
        'handlers': ('file', ),
        'level': 'DEBUG',
    },
}

logging.config.dictConfig(LOG_CONFIG)
version = LooseVersion(get_pg_version())

=======
import functools

from distutils.version import LooseVersion
from testgres import get_new_node, get_pg_version
from testgres.utils import pg_version_ge

# set setup base logging config, it can be turned on by `use_logging`
# parameter on node setup

import logging
import logging.config

logfile = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'tests.log')
LOG_CONFIG = {
    'version': 1,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'base_format',
            'level': logging.DEBUG,
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': logfile,
            'formatter': 'base_format',
            'level': logging.DEBUG,
        },
    },
    'formatters': {
        'base_format': {
            'format': '%(node)-5s: %(message)s',
        },
    },
    'root': {
        'handlers': ('file', ),
        'level': 'DEBUG',
    },
}

logging.config.dictConfig(LOG_CONFIG)
version = LooseVersion(get_pg_version())

>>>>>>> master

# Helper function for json equality
def ordered(obj, skip_keys=None):
    if isinstance(obj, dict):
        return sorted((k, ordered(v, skip_keys=skip_keys)) for k, v in obj.items()
                      if skip_keys is None or (skip_keys and k not in skip_keys))
    if isinstance(obj, list):
        return sorted(ordered(x, skip_keys=skip_keys) for x in obj)
    else:
        return obj


<<<<<<< HEAD
def if_fdw_enabled(func):
    """ To run tests with FDW support, set environment variable TEST_FDW=1 """

    def wrapper(*args, **kwargs):
        if os.environ.get('FDW_DISABLED') != '1':
            func(*args, **kwargs)
        else:
            print('Warning: FDW features tests are disabled, skipping...')

    return wrapper
=======
# Check if postgres_fdw is available
@functools.lru_cache(maxsize=1)
def is_postgres_fdw_ready():
    with get_new_node().init().start() as node:
        result = node.execute("""
            select count(*) from pg_available_extensions where name = 'postgres_fdw'
        """)

        if result[0][0] > 0:
            return True

        return False
>>>>>>> master


class Tests(unittest.TestCase):
    def set_trace(self, con, command="pg_debug"):
        pid = con.execute("select pg_backend_pid()")[0][0]
        p = subprocess.Popen([command], stdin=subprocess.PIPE)
        p.communicate(str(pid).encode())

<<<<<<< HEAD
    def start_new_pathman_cluster(self,
                                  name='test',
                                  allow_streaming=False,
                                  test_data=False):
        node = get_new_node(name)
        node.init(allow_streaming=allow_streaming)
        node.append_conf("postgresql.conf", "shared_preload_libraries='pg_pathman'\n")
        node.start()
        node.psql('postgres', 'create extension pg_pathman')
        if test_data:
            cmds = (
                "create table abc(id serial, t text)",
                "insert into abc select generate_series(1, 300000)",
                "select create_hash_partitions('abc', 'id', 3, partition_data := false)",
            )
            for cmd in cmds:
                node.safe_psql('postgres', cmd)
=======
    def start_new_pathman_cluster(self, allow_streaming=False, test_data=False):
        node = get_new_node()
        node.init(allow_streaming=allow_streaming)
        node.append_conf("shared_preload_libraries='pg_pathman'\n")
        node.start()
        node.psql('create extension pg_pathman')

        if test_data:
            node.safe_psql("""
                create table abc(id serial, t text);
                insert into abc select generate_series(1, 300000);
                select create_hash_partitions('abc', 'id', 3, partition_data := false);
            """)

            node.safe_psql('vacuum analyze')
>>>>>>> master

        return node

    def test_concurrent(self):
        """ Test concurrent partitioning """

        with self.start_new_pathman_cluster(test_data=True) as node:
<<<<<<< HEAD
            node.psql('postgres', "select partition_table_concurrently('abc')")

            while True:
                # update some rows to check for deadlocks
                node.safe_psql('postgres', """
=======
            node.psql("select partition_table_concurrently('abc')")

            while True:
                # update some rows to check for deadlocks
                node.safe_psql("""
>>>>>>> master
                    update abc set t = 'test'
                    where id in (select (random() * 300000)::int
                    from generate_series(1, 3000))
                """)

<<<<<<< HEAD
                count = node.execute('postgres', """
=======
                count = node.execute("""
>>>>>>> master
                    select count(*) from pathman_concurrent_part_tasks
                """)

                # if there is no active workers then it means work is done
                if count[0][0] == 0:
                    break
                time.sleep(1)

<<<<<<< HEAD
            data = node.execute('postgres', 'select count(*) from only abc')
            self.assertEqual(data[0][0], 0)
            data = node.execute('postgres', 'select count(*) from abc')
=======
            data = node.execute('select count(*) from only abc')
            self.assertEqual(data[0][0], 0)
            data = node.execute('select count(*) from abc')
>>>>>>> master
            self.assertEqual(data[0][0], 300000)
            node.stop()

    def test_replication(self):
        """ Test how pg_pathman works with replication """

        with self.start_new_pathman_cluster(allow_streaming=True, test_data=True) as node:
<<<<<<< HEAD
            with node.replicate('node2') as replica:
=======
            with node.replicate() as replica:
>>>>>>> master
                replica.start()
                replica.catchup()

                # check that results are equal
                self.assertEqual(
<<<<<<< HEAD
                    node.psql('postgres', 'explain (costs off) select * from abc'),
                    replica.psql('postgres', 'explain (costs off) select * from abc'))

                # enable parent and see if it is enabled in replica
                node.psql('postgres', "select enable_parent('abc')")
=======
                    node.psql('explain (costs off) select * from abc'),
                    replica.psql('explain (costs off) select * from abc'))

                # enable parent and see if it is enabled in replica
                node.psql("select enable_parent('abc')")
>>>>>>> master

                # wait until replica catches up
                replica.catchup()

                self.assertEqual(
<<<<<<< HEAD
                    node.psql('postgres', 'explain (costs off) select * from abc'),
                    replica.psql('postgres', 'explain (costs off) select * from abc'))
                self.assertEqual(
                    node.psql('postgres', 'select * from abc'),
                    replica.psql('postgres', 'select * from abc'))
                self.assertEqual(
                    node.execute('postgres', 'select count(*) from abc')[0][0], 300000)

                # check that UPDATE in pathman_config_params invalidates cache
                node.psql('postgres',
                          'update pathman_config_params set enable_parent = false')
=======
                    node.psql('explain (costs off) select * from abc'),
                    replica.psql('explain (costs off) select * from abc'))
                self.assertEqual(
                    node.psql('select * from abc'),
                    replica.psql('select * from abc'))
                self.assertEqual(
                    node.execute('select count(*) from abc')[0][0], 300000)

                # check that UPDATE in pathman_config_params invalidates cache
                node.psql('update pathman_config_params set enable_parent = false')
>>>>>>> master

                # wait until replica catches up
                replica.catchup()

                self.assertEqual(
<<<<<<< HEAD
                    node.psql('postgres', 'explain (costs off) select * from abc'),
                    replica.psql('postgres', 'explain (costs off) select * from abc'))
                self.assertEqual(
                    node.psql('postgres', 'select * from abc'),
                    replica.psql('postgres', 'select * from abc'))
                self.assertEqual(
                    node.execute('postgres', 'select count(*) from abc')[0][0], 0)
=======
                    node.psql('explain (costs off) select * from abc'),
                    replica.psql('explain (costs off) select * from abc'))
                self.assertEqual(
                    node.psql('select * from abc'),
                    replica.psql('select * from abc'))
                self.assertEqual(
                    node.execute('select count(*) from abc')[0][0], 0)
>>>>>>> master

    def test_locks(self):
        """
        Test that a session trying to create new partitions
        waits for other sessions if they are doing the same
        """

        class Flag:
            def __init__(self, value):
                self.flag = value

            def set(self, value):
                self.flag = value

            def get(self):
                return self.flag

        # There is one flag for each thread which shows if thread have done its work
        flags = [Flag(False) for i in range(3)]

        # All threads synchronize though this lock
        lock = threading.Lock()

        # Define thread function
        def add_partition(node, flag, query):
            """
            We expect that this query will wait until
            another session commits or rolls back
            """
<<<<<<< HEAD
            node.safe_psql('postgres', query)
=======
            node.safe_psql(query)
>>>>>>> master
            with lock:
                flag.set(True)

        # Initialize master server
<<<<<<< HEAD
        with get_new_node('master') as node:
            node.init()
            node.append_conf("postgresql.conf", "shared_preload_libraries='pg_pathman'\n")
            node.start()
            sql = """
=======
        with get_new_node() as node:
            node.init()
            node.append_conf("shared_preload_libraries='pg_pathman'")
            node.start()

            node.safe_psql("""
>>>>>>> master
                create extension pg_pathman;
                create table abc(id serial, t text);
                insert into abc select generate_series(1, 100000);
                select create_range_partitions('abc', 'id', 1, 50000);
<<<<<<< HEAD
            """
            node.safe_psql('postgres', sql)
=======
            """)
>>>>>>> master

            # Start transaction that will create partition
            with node.connect() as con:
                con.begin()
                con.execute("select append_range_partition('abc')")

                # Start threads that suppose to add new partitions and wait some
                # time
                query = (
                    "select prepend_range_partition('abc')",
                    "select append_range_partition('abc')",
<<<<<<< HEAD
                    "select add_range_partition('abc', 500000, 550000)", )
=======
                    "select add_range_partition('abc', 500000, 550000)",
                )

>>>>>>> master
                threads = []
                for i in range(3):
                    thread = threading.Thread(
                        target=add_partition, args=(node, flags[i], query[i]))
                    threads.append(thread)
                    thread.start()
                time.sleep(3)

<<<<<<< HEAD
                # This threads should wait until current transaction finished
=======
                # These threads should wait until current transaction finished
>>>>>>> master
                with lock:
                    for i in range(3):
                        self.assertEqual(flags[i].get(), False)

                # Commit transaction. Since then other sessions can create
                # partitions
                con.commit()

            # Now wait until each thread finishes
            for thread in threads:
                thread.join()

            # Check flags, it should be true which means that threads are
            # finished
            with lock:
                for i in range(3):
                    self.assertEqual(flags[i].get(), True)

            # Check that all partitions are created
            self.assertEqual(
                node.safe_psql(
<<<<<<< HEAD
                    'postgres',
=======
>>>>>>> master
                    "select count(*) from pg_inherits where inhparent='abc'::regclass"),
                b'6\n')

    def test_tablespace(self):
        """ Check tablespace support """

        def check_tablespace(node, tablename, tablespace):
<<<<<<< HEAD
            res = node.execute('postgres',
                               "select get_tablespace('{}')".format(tablename))
=======
            res = node.execute("select get_tablespace('{}')".format(tablename))
>>>>>>> master
            if len(res) == 0:
                return False

            return res[0][0] == tablespace

<<<<<<< HEAD
        with get_new_node('master') as node:
            node.init()
            node.append_conf('postgresql.conf',
                             "shared_preload_libraries='pg_pathman'\n")
            node.start()
            node.psql('postgres', 'create extension pg_pathman')
=======
        with get_new_node() as node:
            node.init()
            node.append_conf("shared_preload_libraries='pg_pathman'")
            node.start()
            node.psql('create extension pg_pathman')
>>>>>>> master

            # create tablespace
            path = os.path.join(node.data_dir, 'test_space_location')
            os.mkdir(path)
<<<<<<< HEAD
            node.psql('postgres',
                      "create tablespace test_space location '{}'".format(path))

            # create table in this tablespace
            node.psql('postgres',
                      'create table abc(a serial, b int) tablespace test_space')

            # create three partitions. Excpect that they will be created in the
            # same tablespace as the parent table
            node.psql('postgres',
                      "select create_range_partitions('abc', 'a', 1, 10, 3)")
            self.assertTrue(check_tablespace(node, 'abc', 'test_space'))

            # check tablespace for appended partition
            node.psql('postgres',
                      "select append_range_partition('abc', 'abc_appended')")
            self.assertTrue(check_tablespace(node, 'abc_appended', 'test_space'))

            # check tablespace for prepended partition
            node.psql('postgres',
                      "select prepend_range_partition('abc', 'abc_prepended')")
            self.assertTrue(check_tablespace(node, 'abc_prepended', 'test_space'))

            # check tablespace for prepended partition
            node.psql('postgres',
                      "select add_range_partition('abc', 41, 51, 'abc_added')")
            self.assertTrue(check_tablespace(node, 'abc_added', 'test_space'))

            # check tablespace for split
            node.psql('postgres',
                      "select split_range_partition('abc_added', 45, 'abc_splitted')")
=======
            node.psql("create tablespace test_space location '{}'".format(path))

            # create table in this tablespace
            node.psql('create table abc(a serial, b int) tablespace test_space')

            # create three partitions. Excpect that they will be created in the
            # same tablespace as the parent table
            node.psql("select create_range_partitions('abc', 'a', 1, 10, 3)")
            self.assertTrue(check_tablespace(node, 'abc', 'test_space'))

            # check tablespace for appended partition
            node.psql("select append_range_partition('abc', 'abc_appended')")
            self.assertTrue(check_tablespace(node, 'abc_appended', 'test_space'))

            # check tablespace for prepended partition
            node.psql("select prepend_range_partition('abc', 'abc_prepended')")
            self.assertTrue(check_tablespace(node, 'abc_prepended', 'test_space'))

            # check tablespace for prepended partition
            node.psql("select add_range_partition('abc', 41, 51, 'abc_added')")
            self.assertTrue(check_tablespace(node, 'abc_added', 'test_space'))

            # check tablespace for split
            node.psql("select split_range_partition('abc_added', 45, 'abc_splitted')")
>>>>>>> master
            self.assertTrue(check_tablespace(node, 'abc_splitted', 'test_space'))

            # now let's specify tablespace explicitly
            node.psql(
<<<<<<< HEAD
                'postgres',
                "select append_range_partition('abc', 'abc_appended_2', 'pg_default')"
            )
            node.psql(
                'postgres',
                "select prepend_range_partition('abc', 'abc_prepended_2', 'pg_default')"
            )
            node.psql(
                'postgres',
                "select add_range_partition('abc', 61, 71, 'abc_added_2', 'pg_default')"
            )
            node.psql(
                'postgres',
=======
                "select append_range_partition('abc', 'abc_appended_2', 'pg_default')"
            )
            node.psql(
                "select prepend_range_partition('abc', 'abc_prepended_2', 'pg_default')"
            )
            node.psql(
                "select add_range_partition('abc', 61, 71, 'abc_added_2', 'pg_default')"
            )
            node.psql(
>>>>>>> master
                "select split_range_partition('abc_added_2', 65, 'abc_splitted_2', 'pg_default')"
            )

            # yapf: disable
            self.assertTrue(check_tablespace(node, 'abc_appended_2',  'pg_default'))
            self.assertTrue(check_tablespace(node, 'abc_prepended_2', 'pg_default'))
            self.assertTrue(check_tablespace(node, 'abc_added_2',     'pg_default'))
            self.assertTrue(check_tablespace(node, 'abc_splitted_2',  'pg_default'))

<<<<<<< HEAD
    @if_fdw_enabled
=======
    @unittest.skipUnless(is_postgres_fdw_ready(), 'might be missing')
>>>>>>> master
    def test_foreign_table(self):
        """ Test foreign tables """

        # Start master server
<<<<<<< HEAD
        with get_new_node('test') as master, get_new_node('fserv') as fserv:
            master.init()
            master.append_conf('postgresql.conf', """
                shared_preload_libraries='pg_pathman, postgres_fdw'\n
            """)
            master.start()
            master.psql('postgres', 'create extension pg_pathman')
            master.psql('postgres', 'create extension postgres_fdw')
=======
        with get_new_node() as master, get_new_node() as fserv:
            master.init()
            master.append_conf("""
                shared_preload_libraries='pg_pathman, postgres_fdw'\n
            """)
            master.start()
            master.psql('create extension pg_pathman')
            master.psql('create extension postgres_fdw')
>>>>>>> master

            # RANGE partitioning test with FDW:
            #   - create range partitioned table in master
            #   - create foreign server
            #   - create foreign table and insert some data into it
            #   - attach foreign table to partitioned one
            #   - try inserting data into foreign partition via parent
            #   - drop partitions
<<<<<<< HEAD
            master.psql('postgres', """
=======
            master.psql("""
>>>>>>> master
                create table abc(id serial, name text);
                select create_range_partitions('abc', 'id', 0, 10, 2)
            """)

            # Current user name (needed for user mapping)
<<<<<<< HEAD
            username = master.execute('postgres', 'select current_user')[0][0]

            fserv.init().start()
            fserv.safe_psql('postgres', "create table ftable(id serial, name text)")
            fserv.safe_psql('postgres', "insert into ftable values (25, 'foreign')")

            # Create foreign table and attach it to partitioned table
            master.safe_psql('postgres', """
=======
            username = master.execute('select current_user')[0][0]

            fserv.init().start()
            fserv.safe_psql("create table ftable(id serial, name text)")
            fserv.safe_psql("insert into ftable values (25, 'foreign')")

            # Create foreign table and attach it to partitioned table
            master.safe_psql("""
>>>>>>> master
                create server fserv
                foreign data wrapper postgres_fdw
                options (dbname 'postgres', host '127.0.0.1', port '{}')
            """.format(fserv.port))

<<<<<<< HEAD
            master.safe_psql('postgres', """
=======
            master.safe_psql("""
>>>>>>> master
                create user mapping for {0} server fserv
                options (user '{0}')
            """.format(username))

<<<<<<< HEAD
            master.safe_psql('postgres', """
=======
            master.safe_psql("""
>>>>>>> master
                import foreign schema public limit to (ftable)
                from server fserv into public
            """)

            master.safe_psql(
<<<<<<< HEAD
                'postgres',
=======
>>>>>>> master
                "select attach_range_partition('abc', 'ftable', 20, 30)")

            # Check that table attached to partitioned table
            self.assertEqual(
<<<<<<< HEAD
                master.safe_psql('postgres', 'select * from ftable'),
                b'25|foreign\n')

            # Check that we can successfully insert new data into foreign partition
            master.safe_psql('postgres', "insert into abc values (26, 'part')")
            self.assertEqual(
                master.safe_psql('postgres', 'select * from ftable order by id'),
                b'25|foreign\n26|part\n')

            # Testing drop partitions (including foreign partitions)
            master.safe_psql('postgres', "select drop_partitions('abc')")
=======
                master.safe_psql('select * from ftable'),
                b'25|foreign\n')

            # Check that we can successfully insert new data into foreign partition
            master.safe_psql("insert into abc values (26, 'part')")
            self.assertEqual(
                master.safe_psql('select * from ftable order by id'),
                b'25|foreign\n26|part\n')

            # Testing drop partitions (including foreign partitions)
            master.safe_psql("select drop_partitions('abc')")
>>>>>>> master

            # HASH partitioning with FDW:
            #   - create hash partitioned table in master
            #   - create foreign table
            #   - replace local partition with foreign one
            #   - insert data
            #   - drop partitions
<<<<<<< HEAD
            master.psql('postgres', """
                create table hash_test(id serial, name text);
                select create_hash_partitions('hash_test', 'id', 2)
            """)
            fserv.safe_psql('postgres',
                            'create table f_hash_test(id serial, name text)')

            master.safe_psql('postgres', """
                import foreign schema public limit to (f_hash_test)
                from server fserv into public
            """)
            master.safe_psql('postgres', """
                select replace_hash_partition('hash_test_1', 'f_hash_test')
            """)
            master.safe_psql('postgres',
                             'insert into hash_test select generate_series(1,10)')

            self.assertEqual(
                master.safe_psql('postgres', 'select * from hash_test'),
                b'1|\n2|\n5|\n6|\n8|\n9|\n3|\n4|\n7|\n10|\n')
            master.safe_psql('postgres', "select drop_partitions('hash_test')")

    @if_fdw_enabled
=======
            master.psql("""
                create table hash_test(id serial, name text);
                select create_hash_partitions('hash_test', 'id', 2)
            """)
            fserv.safe_psql('create table f_hash_test(id serial, name text)')

            master.safe_psql("""
                import foreign schema public limit to (f_hash_test)
                from server fserv into public
            """)
            master.safe_psql("""
                select replace_hash_partition('hash_test_1', 'f_hash_test')
            """)
            master.safe_psql('insert into hash_test select generate_series(1,10)')

            self.assertEqual(
                master.safe_psql('select * from hash_test'),
                b'1|\n2|\n5|\n6|\n8|\n9|\n3|\n4|\n7|\n10|\n')
            master.safe_psql("select drop_partitions('hash_test')")

    @unittest.skipUnless(is_postgres_fdw_ready(), 'might be missing')
>>>>>>> master
    def test_parallel_nodes(self):
        """ Test parallel queries under partitions """

        # Init and start postgres instance with preload pg_pathman module
<<<<<<< HEAD
        with get_new_node('test') as node:
            node.init()
            node.append_conf(
                'postgresql.conf',
                "shared_preload_libraries='pg_pathman, postgres_fdw'\n")
=======
        with get_new_node() as node:
            node.init()
            node.append_conf(
                "shared_preload_libraries='pg_pathman, postgres_fdw'")
>>>>>>> master
            node.start()

            # Check version of postgres server
            # If version < 9.6 skip all tests for parallel queries
            if version < LooseVersion('9.6.0'):
                return

            # Prepare test database
<<<<<<< HEAD
            node.psql('postgres', 'create extension pg_pathman')
            node.psql('postgres', """
=======
            node.psql('create extension pg_pathman')
            node.psql("""
>>>>>>> master
                create table range_partitioned as
                select generate_series(1, 1e4::integer) i;

                alter table range_partitioned alter column i set not null;
                select create_range_partitions('range_partitioned', 'i', 1, 1e3::integer);

                create table hash_partitioned as
                select generate_series(1, 1e4::integer) i;

                alter table hash_partitioned alter column i set not null;
                select create_hash_partitions('hash_partitioned', 'i', 10);
            """)

            # create statistics for both partitioned tables
<<<<<<< HEAD
            node.psql('postgres', 'vacuum analyze')

            node.psql('postgres', """
=======
            node.psql('vacuum analyze')

            node.psql("""
>>>>>>> master
                create or replace function query_plan(query text)
                returns jsonb as $$
                    declare
                        plan jsonb;
                    begin
                        execute 'explain (costs off, format json)' || query into plan;
                        return plan;
                    end;
                $$ language plpgsql;
            """)

            # Test parallel select
            with node.connect() as con:
                con.execute('set max_parallel_workers_per_gather = 2')
                if version >= LooseVersion('10'):
                    con.execute('set min_parallel_table_scan_size = 0')
                else:
                    con.execute('set min_parallel_relation_size = 0')
                con.execute('set parallel_setup_cost = 0')
                con.execute('set parallel_tuple_cost = 0')

                # Check parallel aggregate plan
                test_query = 'select count(*) from range_partitioned where i < 1500'
                plan = con.execute("select query_plan('%s')" % test_query)[0][0]
                expected = json.loads("""
                        [
                            {
                                "Plan": {
                                  "Node Type": "Aggregate",
                                  "Strategy": "Plain",
                                  "Partial Mode": "Finalize",
                                  "Parallel Aware": false,
                                  "Plans": [
                                        {
                                          "Node Type": "Gather",
                                          "Parent Relationship": "Outer",
                                          "Parallel Aware": false,
                                          "Workers Planned": 2,
                                          "Single Copy": false,
                                          "Plans": [
                                                {
                                                  "Node Type": "Aggregate",
                                                  "Strategy": "Plain",
                                                  "Partial Mode": "Partial",
                                                  "Parent Relationship": "Outer",
                                                  "Parallel Aware": false,
                                                  "Plans": [
                                                        {
                                                          "Node Type": "Append",
                                                          "Parent Relationship": "Outer",
                                                          "Parallel Aware": false,
                                                          "Plans": [
                                                                {
                                                                  "Node Type": "Seq Scan",
                                                                  "Parent Relationship": "Member",
                                                                  "Parallel Aware": true,
                                                                  "Relation Name": "range_partitioned_2",
                                                                  "Alias": "range_partitioned_2",
                                                                  "Filter": "(i < 1500)"
                                                                },
                                                                {
                                                                  "Node Type": "Seq Scan",
                                                                  "Parent Relationship": "Member",
                                                                  "Parallel Aware": true,
                                                                  "Relation Name": "range_partitioned_1",
                                                                  "Alias": "range_partitioned_1"
                                                                }
                                                          ]
                                                        }
                                                  ]
                                                }
                                          ]
                                        }
                                  ]
                                }
                            }
                        ]
                """)
                self.assertEqual(ordered(plan), ordered(expected))

                # Check count of returned tuples
                count = con.execute(
                    'select count(*) from range_partitioned where i < 1500')[0][0]
                self.assertEqual(count, 1499)

                # Check simple parallel seq scan plan with limit
                test_query = 'select * from range_partitioned where i < 1500 limit 5'
                plan = con.execute("select query_plan('%s')" % test_query)[0][0]
                expected = json.loads("""
                            [
                              {
                                    "Plan": {
                                      "Node Type": "Limit",
                                      "Parallel Aware": false,
                                      "Plans": [
                                            {
                                              "Node Type": "Gather",
                                              "Parent Relationship": "Outer",
                                              "Parallel Aware": false,
                                              "Workers Planned": 2,
                                              "Single Copy": false,
                                              "Plans": [
                                                    {
                                                      "Node Type": "Append",
                                                      "Parent Relationship": "Outer",
                                                      "Parallel Aware": false,
                                                      "Plans": [
                                                            {
                                                              "Node Type": "Seq Scan",
                                                              "Parent Relationship": "Member",
                                                              "Parallel Aware": true,
                                                              "Relation Name": "range_partitioned_2",
                                                              "Alias": "range_partitioned_2",
                                                              "Filter": "(i < 1500)"
                                                            },
                                                            {
                                                              "Node Type": "Seq Scan",
                                                              "Parent Relationship": "Member",
                                                              "Parallel Aware": true,
                                                              "Relation Name": "range_partitioned_1",
                                                              "Alias": "range_partitioned_1"
                                                            }
                                                      ]
                                                    }
                                              ]
                                            }
                                      ]
                                    }
                              }
                            ]
                """)
                self.assertEqual(ordered(plan), ordered(expected))

                # Check tuples returned by query above
                res_tuples = con.execute(
                    'select * from range_partitioned where i < 1500 limit 5')
                res_tuples = sorted(map(lambda x: x[0], res_tuples))
                expected = [1, 2, 3, 4, 5]
                self.assertEqual(res_tuples, expected)

                # Check the case when none partition is selected in result plan
                test_query = 'select * from range_partitioned where i < 1'
                plan = con.execute("select query_plan('%s')" % test_query)[0][0]
                expected = json.loads("""
                    [
                        {
                            "Plan": {
                                "Node Type": "Result",
                                "Parallel Aware": false,
                                "One-Time Filter": "false"
                            }
                        }
                    ]
                """)
                self.assertEqual(ordered(plan), ordered(expected))

            # Remove all objects for testing
<<<<<<< HEAD
            node.psql('postgres', 'drop table range_partitioned cascade')
            node.psql('postgres', 'drop table hash_partitioned cascade')
            node.psql('postgres', 'drop extension pg_pathman cascade')
=======
            node.psql('drop table range_partitioned cascade')
            node.psql('drop table hash_partitioned cascade')
            node.psql('drop extension pg_pathman cascade')
>>>>>>> master

    def test_conc_part_drop_runtime_append(self):
        """ Test concurrent partition drop + SELECT (RuntimeAppend) """

        # Create and start new instance
        with self.start_new_pathman_cluster(allow_streaming=False) as node:
            # Create table 'drop_test' and partition it
            with node.connect() as con0:
                # yapf: disable
                con0.begin()
                con0.execute("create table drop_test(val int not null)")
                con0.execute("insert into drop_test select generate_series(1, 1000)")
                con0.execute("select create_range_partitions('drop_test', 'val', 1, 10)")
                con0.commit()

            # Create two separate connections for this test
            with node.connect() as con1, node.connect() as con2:
                try:
                    from queue import Queue
                except ImportError:
                    from Queue import Queue

                # return values from thread
                queue = Queue()

                # Thread for connection #2 (it has to wait)
                def con2_thread():
                    con1.begin()
                    con2.execute('set enable_hashjoin = f')
                    con2.execute('set enable_mergejoin = f')

                    res = con2.execute("""
                        explain (analyze, costs off, timing off)
                        select * from drop_test
                        where val = any (select generate_series(1, 40, 34))
                    """)  # query selects from drop_test_1 and drop_test_4

                    con2.commit()

                    has_runtime_append = False
                    has_drop_test_1 = False
                    has_drop_test_4 = False

                    for row in res:
                        if row[0].find('RuntimeAppend') >= 0:
                            has_runtime_append = True
                            continue

                        if row[0].find('drop_test_1') >= 0:
                            has_drop_test_1 = True
                            continue

                        if row[0].find('drop_test_4') >= 0:
                            has_drop_test_4 = True
                            continue

                    # return all values in tuple
                    queue.put((has_runtime_append, has_drop_test_1, has_drop_test_4))

                # Step 1: cache partitioned table in con1
                con1.begin()
                con1.execute('select count(*) from drop_test')  # load pathman's cache
                con1.commit()

                # Step 2: cache partitioned table in con2
                con2.begin()
                con2.execute('select count(*) from drop_test')  # load pathman's cache
                con2.commit()

                # Step 3: drop first partition of 'drop_test'
                con1.begin()
                con1.execute('drop table drop_test_1')

                # Step 4: try executing select (RuntimeAppend)
                t = threading.Thread(target=con2_thread)
                t.start()

                # Step 5: wait until 't' locks
                while True:
                    with node.connect() as con0:
                        locks = con0.execute("""
                            select count(*) from pg_locks where granted = 'f'
                        """)

                        if int(locks[0][0]) > 0:
                            break

                # Step 6: commit 'DROP TABLE'
                con1.commit()

                # Step 7: wait for con2
                t.join()

                rows = con1.execute("""
                    select * from pathman_partition_list
                    where parent = 'drop_test'::regclass
                    order by range_min, range_max
                """)

                # check number of partitions
                self.assertEqual(len(rows), 99)

                # check RuntimeAppend + selected partitions
                (has_runtime_append, has_drop_test_1, has_drop_test_4) = queue.get()
                self.assertTrue(has_runtime_append)
                self.assertFalse(has_drop_test_1)
                self.assertTrue(has_drop_test_4)

    def test_conc_part_creation_insert(self):
        """ Test concurrent partition creation on INSERT """

        # Create and start new instance
        with self.start_new_pathman_cluster(allow_streaming=False) as node:
            # Create table 'ins_test' and partition it
            with node.connect() as con0:
                # yapf: disable
                con0.begin()
                con0.execute("create table ins_test(val int not null)")
                con0.execute("insert into ins_test select generate_series(1, 50)")
                con0.execute("select create_range_partitions('ins_test', 'val', 1, 10)")
                con0.commit()

            # Create two separate connections for this test
            with node.connect() as con1, node.connect() as con2:

                # Thread for connection #2 (it has to wait)
                def con2_thread():
                    con2.execute('insert into ins_test values(51)')
                    con2.commit()

                # Step 1: lock partitioned table in con1
                con1.begin()
                con1.execute('select count(*) from ins_test')  # load pathman's cache
                con1.execute('lock table ins_test in share update exclusive mode')

                # Step 2: try inserting new value in con2 (waiting)
                con2.begin()
                con2.execute('select count(*) from ins_test')  # load pathman's cache
                t = threading.Thread(target=con2_thread)
                t.start()

                # Step 3: wait until 't' locks
                while True:
                    with node.connect() as con0:
                        locks = con0.execute("""
                            select count(*) from pg_locks where granted = 'f'
                        """)

                        if int(locks[0][0]) > 0:
                            break

                # Step 4: try inserting new value in con1 (success, unlock)
                con1.execute('insert into ins_test values(52)')
                con1.commit()

                # Step 5: wait for con2
                t.join()

                rows = con1.execute("""
                    select * from pathman_partition_list
                    where parent = 'ins_test'::regclass
                    order by range_min, range_max
                """)

                # check number of partitions
                self.assertEqual(len(rows), 6)

                # check range_max of partitions
                self.assertEqual(int(rows[0][5]), 11)
                self.assertEqual(int(rows[1][5]), 21)
                self.assertEqual(int(rows[2][5]), 31)
                self.assertEqual(int(rows[3][5]), 41)
                self.assertEqual(int(rows[4][5]), 51)
                self.assertEqual(int(rows[5][5]), 61)

    def test_conc_part_merge_insert(self):
        """ Test concurrent merge_range_partitions() + INSERT """

        # Create and start new instance
        with self.start_new_pathman_cluster(allow_streaming=False) as node:
            # Create table 'ins_test' and partition it
            with node.connect() as con0:
                # yapf: disable
                con0.begin()
                con0.execute("create table ins_test(val int not null)")
                con0.execute("select create_range_partitions('ins_test', 'val', 1, 10, 10)")
                con0.commit()

            # Create two separate connections for this test
            with node.connect() as con1, node.connect() as con2:

                # Thread for connection #2 (it has to wait)
                def con2_thread():
                    con2.begin()
                    con2.execute('insert into ins_test values(20)')
                    con2.commit()

                # Step 1: initilize con1
                con1.begin()
                con1.execute('select count(*) from ins_test')  # load pathman's cache

                # Step 2: initilize con2
                con2.begin()
                con2.execute('select count(*) from ins_test')  # load pathman's cache
                con2.commit()                                  # unlock relations

                # Step 3: merge 'ins_test1' + 'ins_test_2' in con1 (success)
                con1.execute(
                    "select merge_range_partitions('ins_test_1', 'ins_test_2')")

                # Step 4: try inserting new value in con2 (waiting)
                t = threading.Thread(target=con2_thread)
                t.start()

                # Step 5: wait until 't' locks
                while True:
                    with node.connect() as con0:
                        locks = con0.execute("""
                            select count(*) from pg_locks where granted = 'f'
                        """)

                        if int(locks[0][0]) > 0:
                            break

                # Step 6: finish merge in con1 (success, unlock)
                con1.commit()

                # Step 7: wait for con2
                t.join()

                rows = con1.execute("select *, tableoid::regclass::text from ins_test")

                # check number of rows in table
                self.assertEqual(len(rows), 1)

                # check value that has been inserted
                self.assertEqual(int(rows[0][0]), 20)

                # check partition that was chosen for insert
                self.assertEqual(str(rows[0][1]), 'ins_test_1')

    def test_pg_dump(self):
<<<<<<< HEAD
        """
        Test using dump and restore of partitioned table through pg_dump and pg_restore tools.

        Test strategy:
            - test range and hash partitioned tables;
            - for each partitioned table check on restorable side the following quantities:
                * constraints related to partitioning;
                * init callback function and enable parent flag;
                * number of rows in parent and child tables;
                * plan validity of simple SELECT query under partitioned table;
            - check dumping using the following parameters of pg_dump:
                * format = plain | custom;
                * using of inserts and copy.
            - all test cases are carried out on tables half-full with data located in parent part,
                the rest of data - in child tables.
        """

        # Init and start postgres instance with preload pg_pathman module
        with get_new_node('test') as node:
            node.init()
            node.append_conf('postgresql.conf', """
                shared_preload_libraries='pg_pathman'
                pg_pathman.override_copy=false
            """)
            node.start()

            # Init two databases: initial and copy
            node.psql('postgres', 'create database initial')
            node.psql('postgres', 'create database copy')
            node.psql('initial', 'create extension pg_pathman')

            # Create and fillin partitioned table in initial database
            with node.connect('initial') as con:

                # create and initailly fillin tables
                con.execute('create table range_partitioned (i integer not null)')
                con.execute(
                    'insert into range_partitioned select i from generate_series(1, 500) i'
                )
                con.execute('create table hash_partitioned (i integer not null)')
                con.execute(
                    'insert into hash_partitioned select i from generate_series(1, 500) i'
                )

                # partition table keeping data in base table
                # enable_parent parameter automatically becames true
                con.execute(
                    "select create_range_partitions('range_partitioned', 'i', 1, 200, partition_data := false)"
                )
                con.execute(
                    "select create_hash_partitions('hash_partitioned', 'i', 5, false)"
                )

                # fillin child tables with remain data
                con.execute(
                    'insert into range_partitioned select i from generate_series(501, 1000) i'
                )
                con.execute(
                    'insert into hash_partitioned select i from generate_series(501, 1000) i'
                )

                # set init callback
                con.execute("""
                    create or replace function init_partition_stub_callback(args jsonb)
                    returns void as $$
                        begin
                        end
                    $$ language plpgsql;
                """)
                con.execute(
                    "select set_init_callback('range_partitioned', 'init_partition_stub_callback(jsonb)')"
                )
                con.execute(
                    "select set_init_callback('hash_partitioned', 'init_partition_stub_callback(jsonb)')"
                )

                # turn off enable_parent option
                con.execute(
                    "select set_enable_parent('range_partitioned', false)")
                con.execute("select set_enable_parent('hash_partitioned', false)")
                con.commit()

            # compare strategies
            CMP_OK, PLANS_MISMATCH, CONTENTS_MISMATCH = range(3)

            def cmp_full(con1, con2):
                """
                Compare selection partitions in plan
                and contents in partitioned tables
                """

                plan_query = 'explain (costs off, format json) select * from %s'
                content_query = 'select * from %s order by i'
                table_refs = [
                    'range_partitioned', 'only range_partitioned',
                    'hash_partitioned', 'only hash_partitioned'
                ]
                for table_ref in table_refs:
                    plan_initial = con1.execute(
                        plan_query % table_ref)[0][0][0]['Plan']
                    plan_copy = con2.execute(
                        plan_query % table_ref)[0][0][0]['Plan']
                    if ordered(plan_initial) != ordered(plan_copy):
                        return PLANS_MISMATCH

                    content_initial = [
                        x[0] for x in con1.execute(content_query % table_ref)
                    ]
                    content_copy = [
                        x[0] for x in con2.execute(content_query % table_ref)
                    ]
                    if content_initial != content_copy:
                        return CONTENTS_MISMATCH

                    return CMP_OK

            def turnoff_pathman(node):
                node.psql('initial', 'alter system set pg_pathman.enable to off')
                node.reload()

            def turnon_pathman(node):
                node.psql('initial', 'alter system set pg_pathman.enable to on')
                node.psql('copy', 'alter system set pg_pathman.enable to on')
                node.psql('initial',
                          'alter system set pg_pathman.override_copy to off')
                node.psql('copy',
                          'alter system set pg_pathman.override_copy to off')
                node.reload()

            # Test dump/restore from init database to copy functionality
            test_params = [
                (None, None, [
                    get_bin_path("pg_dump"), "-p {}".format(node.port),
                    "initial"
                ], [get_bin_path("psql"), "-p {}".format(node.port), "copy"],
                    cmp_full),    # dump as plain text and restore via COPY
                (turnoff_pathman, turnon_pathman, [
                    get_bin_path("pg_dump"), "-p {}".format(node.port),
                    "--inserts", "initial"
                ], [get_bin_path("psql"), "-p {}".format(node.port), "copy"],
                    cmp_full),    # dump as plain text and restore via INSERTs
                (None, None, [
                    get_bin_path("pg_dump"), "-p {}".format(node.port),
                    "--format=custom", "initial"
                ], [
                    get_bin_path("pg_restore"), "-p {}".format(node.port),
                    "--dbname=copy"
                ], cmp_full),    # dump in archive format
            ]

            with open(os.devnull, 'w') as fnull:
                for preproc, postproc, pg_dump_params, pg_restore_params, cmp_dbs in test_params:

                    dump_restore_cmd = " | ".join((' '.join(pg_dump_params),
                                                   ' '.join(pg_restore_params)))

                    if (preproc is not None):
                        preproc(node)

                    # transfer and restore data
                    p1 = subprocess.Popen(pg_dump_params, stdout=subprocess.PIPE)
                    stdoutdata, _ = p1.communicate()
                    p2 = subprocess.Popen(
                        pg_restore_params,
                        stdin=subprocess.PIPE,
                        stdout=fnull,
                        stderr=fnull)
                    p2.communicate(input=stdoutdata)

                    if (postproc is not None):
                        postproc(node)

                    # validate data
                    with node.connect('initial') as con1, \
                            node.connect('copy') as con2:

                        # compare plans and contents of initial and copy
                        cmp_result = cmp_dbs(con1, con2)
                        self.assertNotEqual(
                            cmp_result, PLANS_MISMATCH,
                            "mismatch in plans of select query on partitioned tables under the command: %s"
                            % dump_restore_cmd)
                        self.assertNotEqual(
                            cmp_result, CONTENTS_MISMATCH,
                            "mismatch in contents of partitioned tables under the command: %s"
                            % dump_restore_cmd)

                        # compare enable_parent flag and callback function
                        config_params_query = """
                            select partrel, enable_parent, init_callback from pathman_config_params
                        """
                        config_params_initial, config_params_copy = {}, {}
                        for row in con1.execute(config_params_query):
                            config_params_initial[row[0]] = row[1:]
                        for row in con2.execute(config_params_query):
                            config_params_copy[row[0]] = row[1:]
                        self.assertEqual(config_params_initial, config_params_copy,
                                         "mismatch in pathman_config_params under the command: %s" % dump_restore_cmd)

                        # compare constraints on each partition
                        constraints_query = """
                            select r.relname, c.conname, c.consrc from
                            pg_constraint c join pg_class r on c.conrelid=r.oid
                            where relname similar to '(range|hash)_partitioned_\d+'
                        """
                        constraints_initial, constraints_copy = {}, {}
                        for row in con1.execute(constraints_query):
                            constraints_initial[row[0]] = row[1:]
                        for row in con2.execute(constraints_query):
                            constraints_copy[row[0]] = row[1:]
                        self.assertEqual(constraints_initial, constraints_copy,
                                         "mismatch in partitions' constraints under the command: %s" % dump_restore_cmd)

                    # clear copy database
                    node.psql('copy', 'drop schema public cascade')
                    node.psql('copy', 'create schema public')
                    node.psql('copy', 'drop extension pg_pathman cascade')
=======
        with self.start_new_pathman_cluster() as node:
            node.safe_psql('create database copy')

            node.safe_psql("""
                create table test_hash(val int not null);
                select create_hash_partitions('test_hash', 'val', 10);
                insert into test_hash select generate_series(1, 90);

                create table test_range(val int not null);
                select create_range_partitions('test_range', 'val', 1, 10, 10);
                insert into test_range select generate_series(1, 95);
            """)

            dump = node.dump()
            node.restore(dbname='copy', filename=dump)
            os.remove(dump)

            # HASH
            a = node.execute('postgres', 'select * from test_hash order by val')
            b = node.execute('copy', 'select * from test_hash order by val')
            self.assertEqual(a, b)
            c = node.execute('postgres', 'select * from only test_hash order by val')
            d = node.execute('copy', 'select * from only test_hash order by val')
            self.assertEqual(c, d)

            # RANGE
            a = node.execute('postgres', 'select * from test_range order by val')
            b = node.execute('copy', 'select * from test_range order by val')
            self.assertEqual(a, b)
            c = node.execute('postgres', 'select * from only test_range order by val')
            d = node.execute('copy', 'select * from only test_range order by val')
            self.assertEqual(c, d)

            # check partition sets
            p1 = node.execute('postgres', 'select * from pathman_partition_list')
            p2 = node.execute('copy', 'select * from pathman_partition_list')
            self.assertEqual(sorted(p1), sorted(p2))

>>>>>>> master

    def test_concurrent_detach(self):
        """
        Test concurrent detach partition with contiguous
        tuple inserting and spawning new partitions
        """

        # Init parameters
        num_insert_workers = 8
        detach_timeout = 0.1    # time in sec between successive inserts and detachs
        num_detachs = 100    # estimated number of detachs
        inserts_advance = 1    # abvance in sec of inserts process under detachs
        test_interval = int(math.ceil(detach_timeout * num_detachs))

        insert_pgbench_script = os.path.dirname(os.path.realpath(__file__)) \
            + "/pgbench_scripts/insert_current_timestamp.pgbench"
        detach_pgbench_script = os.path.dirname(os.path.realpath(__file__)) \
            + "/pgbench_scripts/detachs_in_timeout.pgbench"

        # Check pgbench scripts on existance
        self.assertTrue(
            os.path.isfile(insert_pgbench_script),
            msg="pgbench script with insert timestamp doesn't exist")

        self.assertTrue(
            os.path.isfile(detach_pgbench_script),
            msg="pgbench script with detach letfmost partition doesn't exist")

        # Create and start new instance
        with self.start_new_pathman_cluster(allow_streaming=False) as node:
            # Create partitioned table for testing that spawns new partition on each next *detach_timeout* sec
            with node.connect() as con0:
                con0.begin()
                con0.execute(
                    'create table ts_range_partitioned(ts timestamp not null)')

                # yapf: disable
                con0.execute("""
                    select create_range_partitions('ts_range_partitioned',
                                                   'ts',
                                                   current_timestamp,
                                                   interval '%f',
                                                   1)
                """ % detach_timeout)
                con0.commit()

            # Run in background inserts and detachs processes
            with open(os.devnull, 'w') as fnull:
                # init pgbench's utility tables
                init_pgbench = node.pgbench(stdout=fnull, stderr=fnull, options=["-i"])
                init_pgbench.wait()

                inserts = node.pgbench(
                    stdout=fnull,
                    stderr=subprocess.PIPE,
                    options=[
                        "-j",
                        "%i" % num_insert_workers, "-c",
                        "%i" % num_insert_workers, "-f", insert_pgbench_script, "-T",
                        "%i" % (test_interval + inserts_advance)
                    ])
                time.sleep(inserts_advance)
                detachs = node.pgbench(
                    stdout=fnull,
                    stderr=fnull,
                    options=[
                        "-D",
                        "timeout=%f" % detach_timeout, "-f", detach_pgbench_script,
                        "-T",
                        "%i" % test_interval
                    ])

                # Wait for completion of processes
                _, stderrdata = inserts.communicate()
                detachs.wait()

                # Obtain error log from inserts process
                self.assertIsNone(
                    re.search("ERROR|FATAL|PANIC", str(stderrdata)),
                    msg="""
                        Race condition between detach and concurrent
                        inserts with append partition is expired
                    """)
<<<<<<< HEAD

    def test_update_node_plan1(self):
        '''
        Test scan on all partititions when using update node.
        We can't use regression tests here because 9.5 and 9.6 give
        different plans
        '''

        with get_new_node('test_update_node') as node:
            node.init()
            node.append_conf('postgresql.conf', """
                shared_preload_libraries=\'pg_pathman\'
                pg_pathman.override_copy=false
                pg_pathman.enable_partitionrouter=on
            """)
            node.start()

            # Prepare test database
            node.psql('postgres', 'CREATE EXTENSION pg_pathman;')
            node.psql('postgres', 'CREATE SCHEMA test_update_node;')
            node.psql('postgres', 'CREATE TABLE test_update_node.test_range(val NUMERIC NOT NULL, comment TEXT)')
            node.psql('postgres', 'INSERT INTO test_update_node.test_range SELECT i, i FROM generate_series(1, 100) i;')
            node.psql('postgres', "SELECT create_range_partitions('test_update_node.test_range', 'val', 1, 10);")

            node.psql('postgres', """
                create or replace function query_plan(query text) returns jsonb as $$
                declare
                        plan jsonb;
                begin
                        execute 'explain (costs off, format json)' || query into plan;
                        return plan;
                end;
                $$ language plpgsql;
            """)

            with node.connect() as con:
                test_query = "UPDATE test_update_node.test_range SET val = 14 WHERE comment=''15''"
                plan = con.execute('SELECT query_plan(\'%s\')' % test_query)[0][0]
                plan = plan[0]["Plan"]

                self.assertEqual(plan["Node Type"], "ModifyTable")
                self.assertEqual(plan["Operation"], "Update")
                self.assertEqual(plan["Relation Name"], "test_range")
                self.assertEqual(len(plan["Target Tables"]), 11)

            expected_format = '''
                {
                    "Plans": [
                        {
                            "Plans": [
                                {
                                    "Filter": "(comment = '15'::text)",
                                    "Node Type": "Seq Scan",
                                    "Relation Name": "test_range%s",
                                    "Parent Relationship": "child"
                                }
                            ],
                            "Node Type": "Custom Scan",
                            "Parent Relationship": "child",
                            "Custom Plan Provider": "PartitionFilter"
                        }
                    ],
                    "Node Type": "Custom Scan",
                    "Parent Relationship": "Member",
                    "Custom Plan Provider": "PartitionRouter"
                }
            '''

            for i, f in enumerate([''] + list(map(str, range(1, 10)))):
                num = '_' + f if f else ''
                expected = json.loads(expected_format % num)
                p = ordered(plan["Plans"][i], skip_keys=['Parallel Aware', 'Alias'])
                self.assertEqual(p, ordered(expected))

            node.psql('postgres', 'DROP SCHEMA test_update_node CASCADE;')
            node.psql('postgres', 'DROP EXTENSION pg_pathman CASCADE;')
=======
>>>>>>> master


if __name__ == "__main__":
    unittest.main()
