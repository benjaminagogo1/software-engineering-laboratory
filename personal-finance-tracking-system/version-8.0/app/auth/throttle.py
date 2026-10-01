"""
Exponential backoff for repeated failures against one key.

Deliberately not a lockout. NIST SP 800-63B §5.2.2 recommends throttling over a
hard lockout, and the reason is the one an attacker exploits: a lockout keyed on
a username lets anyone lock a known user out of their own account by failing on
purpose. Something that refuses for a while and then lets you try again is
worse for an attacker and survivable for the person who simply mistyped.

Nothing in this module knows about HTTP, usernames or IP addresses. It counts
failures against opaque string keys and answers how long until the next attempt
is allowed, which is what makes it testable without a request in sight. Choosing
the keys — and choosing them badly — is the caller's problem, and the notes on
that are at the bottom of this file.
"""

import time


class Throttle:
    """
    Failures against one key, and a delay that doubles as they accumulate.

    The delay is applied from the *last* failure, not the first, so a steady
    trickle of attempts never earns a reprieve — each one restarts the clock at
    a longer interval.

    Time is `time.monotonic`, not wall clock. A clock that can be stepped
    backwards by an NTP correction would otherwise hand an attacker a free
    reset, and this is a security control rather than a timestamp.
    """

    def __init__(
        self,
        threshold=5,
        base_delay=2.0,
        max_delay=900.0,
        decay_seconds=3600.0,
        max_entries=10_000,
        clock=time.monotonic,
    ):
        """
        `threshold` failures are free; the next one costs `base_delay` seconds,
        and each after that doubles until `max_delay`.

        `decay_seconds` forgets a key that has been quiet for that long. Without
        it the count only ever rises, and a shared address — an office, a
        mobile carrier's NAT — would sit at the maximum delay forever because of
        other people's typos.

        `max_entries` bounds the dict. A limiter that grows without limit is a
        memory-exhaustion vector aimed at the defence itself: an attacker sends
        one request each for a hundred thousand usernames and the counter
        becomes the outage.
        """
        self.threshold = threshold
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.decay_seconds = decay_seconds
        self.max_entries = max_entries
        self.clock = clock

        # key -> (failure count, monotonic time of the last failure)
        self._failures = {}

    def delay_for(self, count):
        """
        How long the `count`-th failure costs, capped.

        count <= threshold is free, so a person who mistypes twice is not
        delayed at all — only a pattern is.
        """
        if count <= self.threshold:
            return 0.0

        # The `- 1` is what makes `base_delay` the first delay rather than a
        # value nothing ever produces: failure number threshold + 1 is the first
        # one that costs anything, so its exponent has to be zero.
        exponent = min(count - self.threshold - 1, 32)

        # Capped before the shift rather than after: 2 ** 100000 is a much
        # larger number than anyone wants to compute.

        return min(self.base_delay * (2 ** exponent), self.max_delay)

    def retry_after(self, key):
        """
        Seconds until this key may be tried again. Zero means now.

        Does not mutate anything: asking whether an attempt is allowed must not
        be the thing that decides it.
        """
        entry = self._failures.get(key)

        if entry is None:
            return 0.0

        count, last = entry

        if self.clock() - last > self.decay_seconds:
            return 0.0

        remaining = self.delay_for(count) - (self.clock() - last)

        return remaining if remaining > 0 else 0.0

    def record(self, key):
        """Counts one failure against a key and restarts its delay."""
        entry = self._failures.get(key)

        if entry is None or self.clock() - entry[1] > self.decay_seconds:
            count = 1
        else:
            count = entry[0] + 1

        self._failures[key] = (count, self.clock())

        self._prune()

    def clear(self, key):
        """
        Forgets a key, which is what a success does.

        Not called on success by default and not optional at the call sites
        either — a limiter that never clears turns every honest mistake into a
        permanent tax.
        """
        self._failures.pop(key, None)

    def failures(self, key):
        """The current count for a key. For tests and for a status endpoint."""
        entry = self._failures.get(key)

        if entry is None:
            return 0

        return entry[0]

    def _prune(self):
        if len(self._failures) < self.max_entries:
            return

        # Expired entries first — they are free to drop and would be forgotten
        # on their next read anyway.
        now = self.clock()

        for key in [
            key
            for key, (_, last) in self._failures.items()
            if now - last > self.decay_seconds
        ]:
            del self._failures[key]

        # Then, oldest first, until there is room. Dicts keep insertion order,
        # so the oldest surviving insert is the first key. An attacker who
        # rotates keys fast enough to trigger this evicts their own earlier
        # entries before anyone else's, which is the failure mode we want.
        #
        # `>` and not `>=`: the bound is the number of entries to keep. Written
        # the other way, a small `max_entries` evicts on the insert that reaches
        # it — at 1 the dict would be emptied every time, and the limiter would
        # never fire at all.
        while len(self._failures) > self.max_entries:
            del self._failures[next(iter(self._failures))]


# How the keys should be chosen, since a throttle is only as good as its key.
#
# **Keying on the username alone is wrong.** It lets an attacker lock a known
# user out of their own account — the exact attack the backoff exists to avoid,
# turned into a denial of service against a person.
#
# **Keying on the address alone is wrong too.** It misses the distributed case
# entirely: an attacker with a proxy pool gets one guess per address, and a
# per-address threshold never fires.
#
# So app/api.py applies two keys, at different thresholds:
#
#   * the (username, address) pair, tightly — this is guessing one account from
#     one place, and because the address is in the key, the real user on their
#     own connection is never affected by an attacker's failures.
#   * the address alone, loosely — this is one machine spraying many usernames,
#     which the pair key would never see.
#
# What that leaves open, stated rather than implied: someone with a large enough
# pool of addresses can still make many attempts against one account, because
# nothing here is keyed on the username alone — that being the deliberate
# trade. The trail in `audit_events` is what makes that pattern visible, since
# every `login.failed` is recorded with the account it was aimed at. A captcha
# or an out-of-band "someone is trying to sign in as you" is the next step for
# an account that matters, not a tighter counter.
