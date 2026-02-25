retry_policies = {
    "NETWORK_TIMEOUT": {"retry": True, "base_delay": 10},
    "PROVIDER_5XX": {"retry": True, "base_delay": 15},
    "HTTP_429": {"retry": False, "base_delay": 0},
    "QUOTA_EXCEEDED": {"retry": False, "base_delay": 0},
    "ALL_PROVIDERS_FAILED": {"retry": True, "base_delay": 20},
    "UNKNOWN": {"retry": True, "base_delay": 10},
}


def compute_backoff(base_delay: int, retry_count: int) -> int:
    return base_delay * (2 ** retry_count)


def classify_error(error_code: str):
    return retry_policies.get(error_code, retry_policies["UNKNOWN"])
