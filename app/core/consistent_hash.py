import hashlib
from bisect import bisect
from typing import List, Dict


class ConsistentHash:
    def __init__(self, nodes: List[str], virtual_nodes: int = 100):
        """
        Initialize the consistent hash ring

        Args:
            nodes: List of node identifiers (parsed from comma-separated string)
            virtual_nodes: Number of virtual nodes per physical node
        """
        self.hash_ring: Dict[int, str] = {}
        self.sorted_keys: List[int] = []
        self.virtual_nodes = virtual_nodes
        for node in nodes:
            self.add_node(node)

    def _hash(self, key: str) -> int:
        """Return the hash for a key."""
        return int(hashlib.md5(key.encode()).hexdigest(), 16)

    def add_node(self, node: str) -> None:
        """
        Add a new node to the hash ring

        Args:
            node: Node identifier to add
        """
        for i in range(self.virtual_nodes):
            vnode = f"{node}-{i}"
            key = self._hash(vnode)
            self.hash_ring[key] = node
            self.sorted_keys.append(key)
        self.sorted_keys.sort()

    def remove_node(self, node: str) -> None:
        """
        Remove a node from the hash ring

        Args:
            node: Node identifier to remove
        """
        keys = [self._hash(f"{node}-{i}") for i in range(self.virtual_nodes)]
        for key in keys:
            self.hash_ring.pop(key, None)
            if key in self.sorted_keys:
                self.sorted_keys.remove(key)

    def get_node(self, key: str) -> str:
        """
        Get the node responsible for the given key

        Args:
            key: The key to look up

        Returns:
            The node responsible for the key
        """
        if not self.sorted_keys:
            raise Exception("Hash ring is empty")
        h = self._hash(key)
        pos = bisect(self.sorted_keys, h) % len(self.sorted_keys)
        return self.hash_ring[self.sorted_keys[pos]]
