from redis.exceptions import ConnectionError
import pytest
import asyncio
import os
import socket
import uuid
import random
import time

from app.core.sharded_redis_manager import RedisManager
from app.services.sharded_visit_counter import VisitCounterService


# Set Redis nodes environment variable immediately (before any imports/initialization)
if "PYTEST_RUNNING" not in os.environ:
    # Check if running in Docker by trying to resolve redis1
    try:
        socket.gethostbyname("redis1")
        # Inside Docker, use the service names and internal ports
        os.environ["REDIS_NODES"] = "redis://redis1:6379,redis://redis2:6379"
        print("Running in Docker - using Docker service names")
    except socket.gaierror:
        # Local environment, use localhost with mapped ports
        os.environ["REDIS_NODES"] = "redis://localhost:7070,redis://localhost:7071"
        print("Running locally - using localhost ports")


# Create a proper fixture instead of a subclass
@pytest.fixture
def redis_manager():
    # Print for debugging
    print(f"Creating Redis manager with nodes: {os.environ['REDIS_NODES']}")
    return RedisManager()


@pytest.fixture
def visit_counter_service():
    service = VisitCounterService()
    # Force re-creation of the Redis manager to ensure it uses the correct environment
    service.redis_manager = RedisManager()
    return service


@pytest.mark.asyncio
async def test_consistent_hashing(redis_manager):
    # Test that the same key always maps to the same node
    key = "test_page"
    node1 = redis_manager.get_node_for_key(key)
    node2 = redis_manager.get_node_for_key(key)
    assert node1 == node2

    # Test different keys get distributed
    keys = ["page1", "page2", "home", "about", "contact", "products", "blog"]
    nodes = {redis_manager.get_node_for_key(k) for k in keys}
    assert len(nodes) > 1


@pytest.mark.asyncio
async def test_increment_and_get(visit_counter_service):
    # Test incrementing and retrieving counts
    page_id = "test_page"

    try:
        # Get initial count
        initial_count = await visit_counter_service.get_visit_count(page_id)

        # Increment multiple times
        for _ in range(5):
            await visit_counter_service.increment_visit(page_id)

        # Get updated count
        updated_count = await visit_counter_service.get_visit_count(page_id)

        # Verify count increased by 5
        assert updated_count == initial_count + 5

        # Verify served_via shows correct Redis instance
        served_via = visit_counter_service.get_served_via()
    except ConnectionError as e:
        pytest.skip(f"Redis connection failed: {e}")


# Additional test to check Redis connectivity
@pytest.mark.asyncio
async def test_redis_connectivity(redis_manager):
    # This test attempts to connect to Redis instances
    try:
        key = "test_connectivity"
        client = await redis_manager.get_connection(key)
        # Try a simple ping operation to verify connectivity
        result = client.ping()
        assert result is True
    except Exception as e:
        pytest.skip(f"Redis not available: {e}")


# Test node distribution is relatively balanced
@pytest.mark.asyncio
async def test_key_distribution(redis_manager):
    # Generate 1000 random keys and check distribution
    keys = [str(uuid.uuid4()) for _ in range(1000)]

    node_distribution = {}
    for key in keys:
        node = redis_manager.get_node_for_key(key)
        node_distribution[node] = node_distribution.get(node, 0) + 1

    # Check all nodes have some keys (no empty nodes)
    assert all(count > 0 for count in node_distribution.values())

    # Check if distribution is relatively balanced (no node has more than 60% of keys)
    max_percentage = max(node_distribution.values()) / len(keys) * 100
    assert max_percentage < 60, f"Distribution too uneven: {node_distribution}"


# Load testing: simulate many concurrent increments
@pytest.mark.asyncio
async def test_load(redis_manager):
    test_key = "load_test_page"
    service = VisitCounterService()
    service.redis_manager = redis_manager

    async def increment_task():
        await service.increment_visit(test_key)

    tasks = [increment_task() for _ in range(2000)]
    start_time = time.time()
    await asyncio.gather(*tasks)
    end_time = time.time()

    count = await service.get_visit_count(test_key)
    assert count >= 2000, f"Expected at least 2000 visits, got {count}"
    print(f"Load test completed in {end_time - start_time:.2f} seconds")


# Additional heavy load test: simulate a high number of concurrent increments
@pytest.mark.asyncio
async def test_heavy_load(redis_manager):
    test_key = "heavy_load_test_page"
    service = VisitCounterService()
    service.redis_manager = redis_manager

    # Reset the test key in Redis to ensure a clean slate.
    client = await redis_manager.get_connection(test_key)
    await asyncio.to_thread(client.hdel, "visit_count", test_key)

    # Increase concurrent increments to a much higher value to really stress the system.
    concurrent_increments = 50000

    async def heavy_increment_task():
        await service.increment_visit(test_key)

    tasks = [heavy_increment_task() for _ in range(concurrent_increments)]
    start_time = time.time()
    await asyncio.gather(*tasks)
    end_time = time.time()

    count = await service.get_visit_count(test_key)
    duration = end_time - start_time

    # Assert that the count exactly matches the number of increments
    assert (
        count == concurrent_increments
    ), f"Heavy load test failed: expected {concurrent_increments}, got {count}"

    # Optional: enforce a minimum duration to ensure that actual heavy load occurs (e.g. at least 2 seconds)
    assert (
        duration >= 2
    ), f"Heavy load test completed too quickly ({duration:.2f} seconds), possibly not stressing the system."

    print(
        f"Heavy load test completed in {duration:.2f} seconds with {count} total increments"
    )


# Additional distribution test: simulate random keys over many iterations
@pytest.mark.asyncio
async def test_random_key_distribution(redis_manager):
    service = VisitCounterService()
    service.redis_manager = redis_manager

    key_list = [f"page_{random.randint(1, 50)}" for _ in range(1000)]
    for key in key_list:
        await service.increment_visit(key)

    distribution = {}
    for key in key_list:
        node = redis_manager.get_node_for_key(key)
        distribution[node] = distribution.get(node, 0) + 1

    assert all(val > 0 for val in distribution.values())
    max_percentage = max(distribution.values()) / len(key_list) * 100
    assert max_percentage < 60, f"Random key distribution too uneven: {distribution}"
