from dataclasses import dataclass


@dataclass
class ProviderError(Exception):
    code: str
    message: str


# Stub implementation; replace with real provider APIs.
def call_provider(provider: str, payload: str):
    if not provider:
        raise ProviderError("UNKNOWN", "Missing provider")

    return {
        "output": f"{provider}:OK",
        "usage": 50,
    }
