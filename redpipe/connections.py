# -*- coding: utf-8 -*-
"""
Bind instances of the redis-py client to redpipe.
Assign named connections to be able to talk to multiple redis servers in your
project.

The ConnectionManager is a singleton class.

These functions are all you will need to call from your code:

* connect_redis
* disconnect
* reset

Everything else is for internal use.
"""
import redis
from typing import (Optional, Callable, Dict, Union)
from typing_extensions import TypeAlias
from .exceptions import AlreadyConnected, InvalidPipeline

__all__ = [
    'connect_redis',
    'disconnect',
    'reset'
]


RedisClient: TypeAlias = Union[redis.Redis, redis.RedisCluster]


class ConnectionManager(object):
    """
    A Connection manager. Used as a singleton.

    Don't invoke methods on this class directly.
    Instead use the convenience methods defined in this module:

    * connect_redis
    * disconnect
    * reset

    """
    connections: Dict[Optional[str], Callable] = {}
    clients: Dict[Optional[str], Optional[RedisClient]] = {}

    @classmethod
    def get(cls, name: Optional[str] = None) -> redis.client.Pipeline:
        """
        Get a new redis-py pipeline object or similar object.
        Called by the redpipe.pipelines module.
        Don't call this directly.

        :param name: str
        :return: callable implementing the redis-py pipeline interface.
        """
        try:
            return cls.connections[name]()
        except KeyError:
            raise InvalidPipeline('%s is not configured' % name)

    @classmethod
    def get_client(cls, name: str) -> Optional[RedisClient]:
        """
        Returns a low-level Redis client for the connection
        Called by the redpipe.scripts module.
        Don't call this directly.

        :param name: str
        :return: RedisClient (redis.Redis, RedisCluster, etc.)
        """
        try:
            return cls.clients[name]
        except KeyError:
            raise InvalidPipeline('%s is not configured' % name)

    @classmethod
    def connect(cls, pipeline_method: Callable,
                name: Optional[str] = None,
                client: Optional[RedisClient] = None) -> None:
        """
        Low level logic to bind a callable method to a name.
        Don't call this directly unless you know what you are doing.

        :param pipeline_method: callable
        :param name: str optional
        :param client: RedisClient (redis.Redis, RedisCluster, etc.) optional
        :return: None
        """
        try:
            if cls.get(name).get_connection_kwargs() \
                    != pipeline_method().get_connection_kwargs():
                raise AlreadyConnected("can't change connection for %s" % name)
        except InvalidPipeline:
            pass

        cls.connections[name] = pipeline_method
        cls.clients[name] = client

    @classmethod
    def connect_redis(cls, redis_client, name=None, transaction=False) -> None:
        """
        Store the redis connection in our connector instance.

        Do this during your application bootstrapping.

        We call the pipeline method of the redis client.

        The ``redis_client`` can be either a redis or redis cluster client.
        We use the interface, not the actual class.

        That means we can handle either one identically.

        The transaction flag is a boolean value we hold on to and
        pass to the invocation of something equivalent to:

        .. code-block:: python

            redis_client.pipeline(transaction=transation)

        Unlike redis-py, this flag defaults to False.
        You can configure it to always use the MULTI/EXEC flags,
        but I don't see much point.

        If you need transactional support I recommend using a LUA script.

        **RedPipe** is about improving network round-trip efficiency.

        :param redis_client: redis.Redis()
        :param name: identifier for the connection, optional
        :param transaction: bool, defaults to False
        :return: None
        """
        if redis_client.get_connection_kwargs().get('decode_responses', False):
            raise InvalidPipeline('decode_responses set to True')

        def pipeline_method():
            """
            A closure wrapping the pipeline.

            :return: pipeline object
            """
            return redis_client.pipeline(transaction=transaction)

        # set up the connection.
        cls.connect(pipeline_method=pipeline_method, name=name,
                    client=redis_client)

    @classmethod
    def disconnect(cls, name: Optional[str] = None) -> None:
        """
        remove a connection by name.
        If no name is passed in, it assumes default.

        Useful for testing.

        :param name:
        :return:
        """
        try:
            del cls.connections[name]
            del cls.clients[name]
        except KeyError:
            pass

    @classmethod
    def reset(cls) -> None:
        """
        remove all connections.
        Useful for testing scenarios.

        :return: None
        """
        cls.connections = {}
        cls.clients = {}


def connect_redis(redis_client, name=None, transaction=False) -> None:
    """
    Connect your redis-py instance to redpipe.

    Example:

    .. code:: python

        redpipe.connect_redis(redis.Redis(), name='users')


    Do this during your application bootstrapping.

    You can also pass a redis cluster instance to this method.

    .. code:: python

        redpipe.connect_redis(redis.RedisCluster(), name='users')


    You are allowed to pass in any redis-py client instance.

    .. code:: python

        redpipe.connect_redis(redis.Redis(), name='a')
        redpipe.connect_redis(redis.RedisCluster(...), name='b')

    :param redis_client:
    :param name: nickname you want to give to your connection.
    :param transaction:
    :return:
    """
    ConnectionManager.connect_redis(
        redis_client=redis_client, name=name, transaction=transaction)


def disconnect(name: Optional[str] = None) -> None:
    """
    remove a connection by name.
    If no name is passed in, it assumes default.

    .. code-block:: python

        redpipe.disconnect('users')
        redpipe.disconnect()


    Useful for testing.

    :param name:
    :return: None
    """
    ConnectionManager.disconnect(name=name)


def reset() -> None:
    """
    remove all connections.

    .. code-block:: python

        redpipe.reset()

    Useful for testing scenarios.

    Not sure when you'd want to call this explicitly
    unless you need an explicit teardown of your application.
    In most cases, python garbage collection will do the right thing
    on shutdown and close all the redis connections.

    :return: None
    """
    ConnectionManager.reset()
