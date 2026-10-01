"""
The backoff counter, tested without a request in sight.

That is the payoff of keeping HTTP, usernames and addresses out of this module:
every property below — the doubling, the cap, the decay, the bound on the dict —
is checked by moving a fake clock, not by waiting and not by issuing seven failed
logins. The API-level wiring is covered separately in tests/test_auth_limits.py.
"""

import time

import pytest

from app.auth.throttle import Throttle


class FakeClock:
    """A clock the test moves by hand, so no test ever sleeps."""

    def __init__(self, now=1000.0):
        self.now = now

    def __call__(self):
        return self.now

    def advance(self, seconds):
        self.now += seconds


@pytest.fixture
def clock():
    return FakeClock()


@pytest.fixture
def throttle(clock):
    # A generous decay and cap so the properties under test are the only ones
    # in play; each test that cares rebuilds with its own values.
    return Throttle(
        threshold=2,
        base_delay=1.0,
        max_delay=1000.0,
        decay_seconds=3600.0,
        clock=clock,
    )


class TestDelayFor:
    def test_no_delay_at_or_below_the_threshold(self, throttle):
        assert throttle.delay_for(0) == 0.0
        assert throttle.delay_for(1) == 0.0
        assert throttle.delay_for(2) == 0.0

    def test_the_first_failure_past_the_threshold_costs_the_base_delay(self, throttle):
        # The regression this pins: with the exponent computed as
        # `count - threshold`, the first delayed response is 2 x base_delay and
        # base_delay itself is a value nothing ever produces.
        assert throttle.delay_for(3) == 1.0

    def test_the_delay_doubles_from_there(self, throttle):
        assert throttle.delay_for(4) == 2.0
        assert throttle.delay_for(5) == 4.0
        assert throttle.delay_for(6) == 8.0

    def test_the_delay_is_capped(self, clock):
        throttle = Throttle(threshold=0, base_delay=1.0, max_delay=10.0, clock=clock)

        assert throttle.delay_for(4) == 8.0
        assert throttle.delay_for(5) == 10.0
        assert throttle.delay_for(500) == 10.0

    def test_an_enormous_count_returns_promptly(self, throttle):
        # The exponent is capped before the shift. Without that, 2 ** 10**9 is
        # computed on the request path and the limiter becomes the outage.
        assert throttle.delay_for(10**9) == 1000.0


class TestRetryAfter:
    def test_an_unknown_key_may_always_try(self, throttle):
        assert throttle.retry_after("nobody") == 0.0

    def test_a_key_below_the_threshold_may_always_try(self, throttle):
        throttle.record("k")
        throttle.record("k")

        assert throttle.retry_after("k") == 0.0

    def test_a_key_past_the_threshold_must_wait(self, throttle):
        for _ in range(3):
            throttle.record("k")

        assert throttle.retry_after("k") == 1.0

    def test_the_wait_counts_down(self, throttle, clock):
        for _ in range(3):
            throttle.record("k")

        clock.advance(0.4)

        assert throttle.retry_after("k") == pytest.approx(0.6)

    def test_the_wait_never_goes_negative(self, throttle, clock):
        for _ in range(3):
            throttle.record("k")

        clock.advance(60.0)

        assert throttle.retry_after("k") == 0.0

    def test_a_decayed_key_may_try_again(self, clock):
        throttle = Throttle(threshold=0, decay_seconds=100.0, clock=clock)

        throttle.record("k")

        clock.advance(100.1)

        assert throttle.retry_after("k") == 0.0

    def test_asking_changes_nothing(self, throttle, clock):
        # A check that mutated would make the answer depend on how many times
        # it had been asked, and the caller that asks twice is the caller that
        # counts twice.
        for _ in range(4):
            throttle.record("k")

        before = throttle.failures("k")

        throttle.retry_after("k")
        clock.advance(5.0)
        throttle.retry_after("k")

        assert throttle.failures("k") == before


class TestRecord:
    def test_failures_accumulate(self, throttle):
        for expected in (1, 2, 3):
            throttle.record("k")

            assert throttle.failures("k") == expected

    def test_a_failure_restarts_the_delay_from_now(self, throttle, clock):
        # The delay is measured from the last failure, not the first, so a slow
        # trickle of attempts never earns a reprieve.
        for _ in range(3):
            throttle.record("k")

        clock.advance(0.9)

        assert throttle.retry_after("k") == pytest.approx(0.1)

        throttle.record("k")

        assert throttle.retry_after("k") == pytest.approx(2.0)

    def test_a_quiet_key_starts_over_rather_than_resuming(self, clock):
        throttle = Throttle(threshold=0, decay_seconds=100.0, clock=clock)

        throttle.record("k")
        throttle.record("k")

        assert throttle.failures("k") == 2

        clock.advance(100.1)
        throttle.record("k")

        # Not 3: the earlier two have decayed, and carrying them forward would
        # leave a shared address at the maximum delay because of other people's
        # typos last hour.
        assert throttle.failures("k") == 1

    def test_a_failure_on_an_unknown_key_starts_at_one(self, throttle):
        throttle.record("fresh")

        assert throttle.failures("fresh") == 1

    def test_keys_are_independent(self, throttle):
        for _ in range(3):
            throttle.record("k")

        throttle.record("other")

        assert throttle.failures("k") == 3
        assert throttle.failures("other") == 1
        assert throttle.retry_after("other") == 0.0


class TestClear:
    def test_clearing_forgets_the_key(self, throttle):
        for _ in range(5):
            throttle.record("k")

        throttle.clear("k")

        assert throttle.failures("k") == 0
        assert throttle.retry_after("k") == 0.0

    def test_clearing_a_key_that_was_never_seen_is_harmless(self, throttle):
        throttle.clear("never")

        assert throttle.failures("never") == 0

    def test_clearing_one_key_leaves_the_others(self, throttle):
        throttle.record("a")
        throttle.record("b")

        throttle.clear("a")

        assert throttle.failures("a") == 0
        assert throttle.failures("b") == 1


class TestFailures:
    def test_an_unknown_key_has_no_failures(self, throttle):
        assert throttle.failures("never") == 0


class TestTheBoundOnTheDict:
    def test_the_dict_never_exceeds_max_entries(self, clock):
        throttle = Throttle(
            threshold=0, max_entries=3, decay_seconds=3600.0, clock=clock
        )

        for index in range(20):
            throttle.record(f"k{index}")

        assert len(throttle._failures) <= 3

    def test_a_small_bound_still_limits(self, clock):
        # At max_entries=1 the `>=` form of the eviction loop empties the dict
        # on every insert, so the limiter never fires at all.
        throttle = Throttle(
            threshold=0, base_delay=1.0, max_entries=1, decay_seconds=3600.0, clock=clock
        )

        throttle.record("k")
        throttle.record("k")

        assert throttle.failures("k") == 2
        assert throttle.retry_after("k") == 2.0

    def test_the_oldest_key_is_evicted_first(self, clock):
        throttle = Throttle(
            threshold=0, max_entries=2, decay_seconds=3600.0, clock=clock
        )

        throttle.record("oldest")
        throttle.record("middle")
        throttle.record("newest")

        assert throttle.failures("oldest") == 0
        assert throttle.failures("middle") == 1
        assert throttle.failures("newest") == 1

    def test_expired_keys_are_dropped_before_live_ones(self, clock):
        # The point of measuring eviction this way: a burst of one-shot keys
        # that have since decayed must not push out keys still in play.
        throttle = Throttle(
            threshold=0, max_entries=2, decay_seconds=100.0, clock=clock
        )

        throttle.record("stale")
        clock.advance(200.0)

        throttle.record("live")
        throttle.record("newer")

        assert throttle.failures("live") == 1
        assert throttle.failures("newer") == 1


class TestTheClock:
    def test_the_default_clock_is_monotonic(self):
        # A security control that a wall-clock step can reset for free is not a
        # control. `time.monotonic` cannot go backwards.
        assert Throttle().clock is time.monotonic

    def test_defaults_are_usable_as_they_stand(self):
        throttle = Throttle()

        assert throttle.threshold == 5
        assert throttle.delay_for(throttle.threshold) == 0.0
        assert throttle.delay_for(throttle.threshold + 1) == throttle.base_delay
