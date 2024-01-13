import asyncio
import time
import pytest

from main.main import SlidingWindowCounterLimiter, SlidingWindowLogLimiter, FixedWindowCounterLimiterUserLevel, \
    FixedWindowCounterLimiterServerLevel, TokenBucketRateLimiter


@pytest.fixture
def event_loop():
    loop = asyncio.get_event_loop()
    yield loop
    loop.close()


@pytest.mark.asyncio
async def test_consume_within_limit():
    limiter = SlidingWindowCounterLimiter(window_size=10, number_requests=5)

    # Simulate five requests within the limit
    for _ in range(5):
        result = await limiter.consume("test_ip")
        assert result is True


@pytest.mark.asyncio
async def test_consume_exceed_limit():
    limiter = SlidingWindowCounterLimiter(window_size=10, number_requests=5)

    # Simulate six requests, exceeding the limit

    tasks = [limiter.consume("test_ip") for _ in range(6)]
    results = await asyncio.gather(*tasks)

    # The last request should return False, indicating limit exceeded
    assert False in results


@pytest.mark.asyncio
async def test_consume_reset_window():
    limiter = SlidingWindowCounterLimiter(window_size=10, number_requests=5)

    # Simulate requests in two different windows
    for _ in range(5):
        result = await limiter.consume("test_ip")

    # Sleep for more than 10 seconds to reset the window
    await asyncio.sleep(11)

    # Simulate five more requests in the new window
    for _ in range(5):
        result = await limiter.consume("test_ip")
        assert result is True


@pytest.mark.asyncio
async def test_sliding_window_log_limiter_within_limit():
    limiter = SlidingWindowLogLimiter(threshold=3, number_requests=5)
    ip_address = "test_ip"
    # Create five tasks running concurrently
    tasks = [limiter.consume(ip_address) for _ in range(5)]
    results = await asyncio.gather(*tasks)
    assert all(results)

    assert len(limiter.get_logs(ip_address)) == 5

    await asyncio.sleep(4)

    tasks = [limiter.consume(ip_address) for _ in range(10)]
    results = await asyncio.gather(*tasks)

    assert len(limiter.get_logs(ip_address)) == 10

    # All tasks should be within the limit
    consumed = [consumed for consumed in results if consumed]
    rejected = [consumed for consumed in results if not consumed]
    assert len(consumed) == 5
    assert len(rejected) == len(results) - len(consumed)


@pytest.mark.asyncio
async def test_sliding_window_log_limiter_exceed_limit():
    limiter = SlidingWindowLogLimiter(threshold=10, number_requests=5)

    # Create six tasks running concurrently
    tasks = [limiter.consume("test_ip") for _ in range(6)]
    results = await asyncio.gather(*tasks)

    # The sixth task should return False, indicating limit exceeded
    assert any([result is False for result in results])


@pytest.mark.asyncio
async def test_sliding_window_log_limiter_reset_window():
    limiter = SlidingWindowLogLimiter(threshold=10, number_requests=5)

    # Simulate requests in two different windows
    for _ in range(5):
        result = await limiter.consume("test_ip")

    assert result


    # Sleep for more than 10 seconds to reset the window
    await asyncio.sleep(11)

    # Simulate five more requests in the new window
    tasks = [limiter.consume("test_ip") for _ in range(5)]
    results = await asyncio.gather(*tasks)

    # All tasks in the new window should be within the limit
    assert all(result is True for result in results)


@pytest.mark.asyncio
async def test_fixed_window_counter_user_level_within_limit():
    limiter = FixedWindowCounterLimiterUserLevel(duration=10, capacity=5)

    # Simulate five requests within the limit
    tasks_user1 = [limiter.consume("test_ip") for _ in range(5)]
    tasks_user2 = [limiter.consume("test_ip2") for _ in range(5)]
    results = await asyncio.gather(*tasks_user1, *tasks_user2)
    assert all(results)

# Add similar tests for FixedWindowCounterLimiterUserLevel exceeding limit and resetting window...

# Test for FixedWindowCounterLimiterServerLevel
@pytest.mark.asyncio
async def test_fixed_window_counter_server_level_within_limit():
    limiter = FixedWindowCounterLimiterServerLevel(duration=10, capacity=5)

    # Simulate five requests within the limit
    tasks_user1 = [limiter.consume("test_ip") for _ in range(5)]
    tasks_user2 = [limiter.consume("test_ip2") for _ in range(5)]
    results = await asyncio.gather(*tasks_user1, *tasks_user2)
    #should fail as its handled on server level
    assert any([result is False for result in results])


# Add similar tests for FixedWindowCounterLimiterServerLevel exceeding limit and resetting window...

# Test for TokenBucketRateLimiter
@pytest.mark.asyncio
async def test_token_bucket_rate_limiter_within_limit():
    limiter = TokenBucketRateLimiter(capacity=10, rate=2)

    # Simulate five requests within the limit but not rate
    result = None
    for _ in range(10):
        result = await limiter.consume("test_ip")
    assert result is True

    result = await limiter.consume("test_ip")
    assert result is False

    print(f"sleep 3 seconds")
    await asyncio.sleep(3)
    # Simulate five requests within the limit
    for _ in range(5):
        result = await limiter.consume("test_ip")
    assert result is True




