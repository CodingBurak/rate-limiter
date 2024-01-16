import argparse
import asyncio
import math
import time

from aiohttp import web
from collections import defaultdict

from aiohttp.web_middlewares import middleware
from aiohttp.web_request import Request


class TokenBucketRateLimiter:
    def __init__(self, capacity, rate):
        self.capacity = capacity
        self.rate = rate  # rate how many fills for the bucket
        self.tokens = defaultdict(lambda: asyncio.Semaphore(capacity))
        self.bucket = defaultdict(lambda: capacity)
        # use time monotonic for multithreaded time consumption, has always the seconds since start
        # used to calc the amount of tokens to add, after each request (time elapsed)
        self.last_update = defaultdict(lambda: 0.0)

    async def consume(self, ip_address):

        current_time = time.monotonic()
        print(f"{current_time=} {self.last_update[ip_address]}")
        time_elapsed = current_time - self.last_update[ip_address] if self.last_update[ip_address] > 0 else 0
        print(f"{time_elapsed=}")
        self.last_update[ip_address] = current_time
        print(f" bucket {self.bucket[ip_address]} calced {math.floor(time_elapsed * self.rate)}")
        self.bucket[ip_address] = min(self.capacity, self.bucket[ip_address] + math.floor(time_elapsed * self.rate))
        print(f" buckets number {self.bucket[ip_address]}")
        async with self.tokens[ip_address]:

            if self.bucket[ip_address] >= 1:
                self.bucket[ip_address] -= 1
                # comment out to see how semaphores are switched between coros and added to _waiters
                # processing_time = random.uniform(1, 5)
                # await asyncio.sleep(processing_time)
                print(f" buckets available {self.bucket[ip_address]}")
                return True
            print(f" buckets available {self.bucket[ip_address]}")
        return False


class FixedWindowCounterLimiterUserLevel:

    def __init__(self, duration, capacity):
        self.duration = duration
        self.capacity = capacity
        self.semaphores = defaultdict(lambda: asyncio.Semaphore(capacity))
        self.time_window = defaultdict(lambda: time.monotonic())
        self.counter = defaultdict(lambda: 0)

    async def consume(self, ip_address):
        current_request = time.monotonic()
        # await asyncio.sleep(0.2) uncomment to see how counter behaves and blocks requests
        print(f"duration {math.floor(current_request - self.time_window[ip_address])} {self.counter[ip_address]=}")
        if math.floor(current_request - self.time_window[ip_address]) > self.duration:
            async with self.semaphores[ip_address]:
                self.counter[ip_address] = 0
                self.time_window[ip_address] = current_request
                self.counter[ip_address] += 1
                if self.counter[ip_address] > self.capacity:
                    return False
                return True
        else:
            async with self.semaphores[ip_address]:
                self.counter[ip_address] += 1
                if self.counter[ip_address] > self.capacity:
                    return False
                return True


class FixedWindowCounterLimiterServerLevel:

    def __init__(self, duration, capacity):
        self.duration = duration
        self.capacity = capacity
        self.semaphore = asyncio.Semaphore(capacity)
        self.time_window = None
        self.counter = 0

    async def consume(self, _):
        if not self.time_window:
            self.time_window = time.monotonic()
        current_request = time.monotonic()
        print(f"duration {math.floor(current_request - self.time_window)} {self.counter}")
        if math.floor(current_request - self.time_window) > self.duration:
            async with self.semaphore:
                self.counter = 1
                self.time_window = current_request
                return True
        else:
            async with self.semaphore:
                self.counter += 1
                if self.counter > self.capacity:
                    return False
                return True


class SlidingWindowLogLimiter:

    def __init__(self, threshold, number_requests):
        self.threshold = threshold
        self.number_requests = number_requests
        self.lock = defaultdict(lambda: asyncio.Semaphore(number_requests))
        self.logs = defaultdict(lambda: [])

    async def consume(self, ip_address):
        current_time = time.monotonic()
        self.logs[ip_address].append(current_time)
        async with self.lock[ip_address]:
            rate = self._get_rate(current_time, ip_address)
            self._clean_up_logs(current_time, ip_address)
            print(f" {rate=} {ip_address=} {self.lock[ip_address]}")

            if rate > self.number_requests:
                return False
            return True

    def _get_rate(self, current_time, ip_address):
        return len([t for t in self.logs[ip_address] if current_time - t <= self.threshold])

    def _clean_up_logs(self, current_time, ip_address):
        self.logs[ip_address] = [log for log in self.logs[ip_address] if current_time - log <= self.threshold]

    def get_logs(self, ip_address):
        return self.logs[ip_address]


class SlidingWindowCounterLimiter:

    def __init__(self, window_size, number_requests):
        self.window_size = window_size
        self.counters = defaultdict(lambda: self._reset_dict())
        self.number_requests = number_requests

    async def consume(self, ip_address):
        request_time = time.monotonic()

        ctr = self.counters[ip_address]

        async with ctr["semaphore"]:
            elapsed_time = request_time - ctr.get("prev_window")
            print(f"current window {ip_address=} {ctr} {elapsed_time=} {request_time=} ")
            # update for the new window
            if self._is_elapsed_greater_window(elapsed_time):
                ctr['prev_window'] = ctr['window']
                ctr['window'] = request_time
                ctr['prev_count'] = ctr['cur_count']
                ctr['cur_count'] = 0
                print(f"new window {ctr}")

            # e.g 10 - (123 % 10) = 7 seconds remains
            remaining_time = self.window_size - (request_time % self.window_size)
            # weight of the request e.g 0.11
            prev_window_weight = remaining_time / self.window_size
            prev_weighted_cnt = prev_window_weight * ctr['prev_count']

            # add the weight to the current count
            if ctr['cur_count'] + prev_weighted_cnt < self.number_requests:
                ctr['cur_count'] += 1
                return True
            else:
                return False

    def _is_elapsed_greater_window(self, elapsed_time):
        greater = elapsed_time // self.window_size >= 1
        print(f"{greater=}")
        return greater

    def _reset_dict(self):
        return {'prev_count': 0,
                'window': time.monotonic(),
                'prev_window': time.monotonic(),
                'cur_count': 0,
                'semaphore': asyncio.Semaphore(self.number_requests)
                }


def rate_limit_middleware_factory(limiter):
    @middleware
    async def sample_middleware(request, handler):
        _, key, *rest = request.transport.get_extra_info('peername')
        # simulate ip addresses
        # key = random.choice(["peer1", "peer2", "peer3"])
        if request.path == '/limited':
            if await limiter.consume(key):  # await limiter.consume(key):
                return await handler(request)
            else:
                print("Too Many Requests")
                return web.Response(status=429, text="Too Many Requests")
        return await handler(request)

    return sample_middleware


async def limited_handler(req: Request):
    print("Limited, don't overuse me!")
    # await asyncio.sleep(random.uniform(1, 5))
    return web.Response(text="Limited, don't overuse me!")


async def unlimited_handler(req: Request):
    # await asyncio.sleep(random.uniform(1, 5))
    return web.Response(text="Unlimited! Let's Go!")


async def main(algorithm):
    limiter = limiter_map[algo](4, 20)

    app = web.Application(middlewares=[rate_limit_middleware_factory(limiter)])
    app.router.add_get('/limited', limited_handler)
    app.router.add_get('/unlimited', unlimited_handler)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8080)
    await site.start()


if __name__ == '__main__':
    limiter_map = defaultdict(lambda: TokenBucketRateLimiter, {"swc": SlidingWindowCounterLimiter,
                                                               "swl": SlidingWindowLogLimiter,
                                                               "fwcsl": FixedWindowCounterLimiterServerLevel,
                                                               "fwcul": FixedWindowCounterLimiterUserLevel,
                                                               "tbl": TokenBucketRateLimiter})

    parser = argparse.ArgumentParser(description="Limit your api requests")
    parser.add_argument("-limiteralgo", type=str, help="pick between SlidingWindowCounter (swc),"
                                                       " SlidingWindowLog (swl),"
                                                       " FixedWindowCounterServerLevel (fwcsl)"
                                                       " FixedWindowCounterUserLevel (fwcul"
                                                       " TokenBuckeLimiter (tbl)")
    args = parser.parse_args()
    algo = args.limiteralgo
    print(f"{algo=}")

    loop = asyncio.new_event_loop()
    loop.run_until_complete(main(algo))
    loop.run_forever()
    # asyncio.run(main())
