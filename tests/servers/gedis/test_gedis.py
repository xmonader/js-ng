import gevent
from gevent import monkey, pool
monkey.patch_all()

import unittest
from jumpscale.god import j
from jumpscale.servers.gedis.example_actor import Hamada


COUNT = 1
POOLS_COUNT = 100
ACTOR_PATH = "/sandbox/code/github/js-next/js-ng/jumpscale/servers/gedis/example_actor.py"


class TestGedis(unittest.TestCase):
    def test01(self):
        pool = gevent.pool.Pool(POOLS_COUNT)
      
        server = j.servers.gedis.get("test")
        gevent.spawn(server.start)

        cl = j.clients.gedis.get("test")
        cl.register_actor('memory', j.sals.fs.join_paths(j.sals.fs.parent(__file__), 'memory_profiler.py'))
        
        def register(i):
            j.logger.info('Registering actor test_{}', i)
            cl.register_actor('test_%s' % i, ACTOR_PATH)

        def execute(i):
            j.logger.info('executing actor no {}', i)
            hamada = Hamada()
            hamada.x = 1
            r = getattr(cl.actors, 'test_%s' % i).add_two_ints(1, hamada)
            self.assertEqual(r.x, hamada.x)

        def unregister(i):
            j.logger.info('Unregister actor test_{}', i)
            cl.actors.system.unregister_actor('test_%s' % i)
        
        jobs = []
        for i in range(COUNT):
            jobs.append(pool.spawn(register, i))

        gevent.joinall(jobs)

        jobs = []
        for i in range(COUNT):
            jobs.append(pool.spawn(execute, i))

        gevent.joinall(jobs)

        import ipdb; ipdb.set_trace()

        self.assertEqual(cl.actors.memory.object_count('Example'), COUNT)

        jobs = []
        for i in range(COUNT):
            jobs.append(pool.spawn(unregister, i))

        gevent.joinall(jobs)

        self.assertEqual(cl.actors.memory.object_count('Example'), 0)
