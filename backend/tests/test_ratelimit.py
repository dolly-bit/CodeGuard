from app.ratelimit import SlidingWindowLimiter


def test_limit_and_window_expiry():
    now = [0.0]
    lim = SlidingWindowLimiter(2, 10, clock=lambda: now[0])
    assert lim.check("ip")[0] and lim.check("ip")[0]
    ok, retry = lim.check("ip")
    assert not ok and retry >= 1
    assert lim.check("other")[0]
    now[0] = 11.0
    assert lim.check("ip")[0]
