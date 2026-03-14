from rest_framework.throttling import AnonRateThrottle


class LoginRateThrottle(AnonRateThrottle):
    """Strict throttle for login endpoint — protects against brute-force."""
    scope = "login"
