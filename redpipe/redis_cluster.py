import redis
import redis.commands
import redis.cluster
from typing import Optional, Union, Awaitable, Any


class CustomClusterPipeline(redis.cluster.ClusterPipeline):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cluster_response_callbacks['SCAN'] = self.intercept_scan_results

    def scan(self, cursor: int = 0, match: Optional[str] = None,
             count: Optional[int] = None, **kwargs) -> Union[Awaitable, Any]:
        shard_idx = cursor >> 48
        cursor = cursor & 0xffffffffffff

        # TODO: would be nice to be able to specify reading from replicas
        node = self.get_sorted_primaries()[shard_idx]

        options = kwargs.copy()
        options['shard_idx'] = shard_idx
        options['target_nodes'] = [node]

        # skip the "blocked" parent method for scan()
        return super(redis.cluster.ClusterPipeline, self).scan(
            cursor, match, count, **options)

    def intercept_scan_results(self, result, **kwargs):
        (new_cursor, keys) = result
        nodes = self.get_sorted_primaries()
        shard_idx = kwargs.pop('shard_idx')
        if new_cursor == 0:
            shard_idx += 1
        if shard_idx < len(nodes):
            new_cursor = (shard_idx << 48) | new_cursor

        return new_cursor, keys

    def get_sorted_primaries(self):
        return sorted(self.get_primaries(), key=lambda n: n.name)


class CustomRedisCluster(redis.RedisCluster):
    @classmethod
    def from_url(cls, url, **kwargs):
        """
        Return a Redis client object configured from the given URL
        """
        return cls(url=url, **kwargs)

    def __init__(self, *args, **kwargs,):
        super().__init__(*args, **kwargs)

    def pipeline(self, transaction=None, shard_hint=None):
        return CustomClusterPipeline(
            nodes_manager=self.nodes_manager,
            commands_parser=self.commands_parser,
            startup_nodes=self.nodes_manager.startup_nodes,
            result_callbacks=self.result_callbacks,
            cluster_response_callbacks=self.cluster_response_callbacks,
            cluster_error_retry_attempts=self.cluster_error_retry_attempts,
            read_from_replicas=self.read_from_replicas,
            reinitialize_steps=self.reinitialize_steps,
            lock=self._lock,
        )
