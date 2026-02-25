from datetime import datetime

from db import transaction
from provider_clients import ProviderError, call_provider
from quota import increment_quota, quota_percent, reset_if_needed

ROUTING = {
    1: ["openai", "local", "anthropic"],
    2: ["anthropic", "openai", "gpt4o"],
    3: ["gpt4o", "anthropic", "openai"],
}


def route(task: dict):
    routing_list = ROUTING.get(task["tier"], ROUTING[1])
    last_error = "ALL_PROVIDERS_FAILED"

    for provider in routing_list:
        # Keep DB work short and isolated.
        with transaction() as conn:
            reset_if_needed(conn, provider)
            if quota_percent(conn, provider) >= 0.95:
                last_error = "QUOTA_EXCEEDED"
                continue

        try:
            start = datetime.utcnow()
            resp = call_provider(provider, task["payload"])
            latency = int((datetime.utcnow() - start).total_seconds() * 1000)

            # Charge usage after successful call in a separate short transaction.
            with transaction() as conn:
                increment_quota(conn, provider, int(resp["usage"]))

            return {
                "provider": provider,
                "token_actual": int(resp["usage"]),
                "latency": latency,
                "output": resp["output"],
            }
        except ProviderError as error:
            last_error = error.code
            continue
        except RuntimeError as error:
            last_error = str(error)
            continue
        except Exception:
            last_error = "UNKNOWN"
            continue

    raise RuntimeError(last_error)
