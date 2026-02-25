from datetime import datetime, timedelta

BILLING_DAYS = 30


def _parse_datetime(value):
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(str(value).replace("Z", "+00:00")).replace(tzinfo=None)


def reset_if_needed(conn, provider: str) -> None:
    row = conn.execute(
        "SELECT used_tokens, monthly_limit, last_reset FROM provider_quota WHERE provider=?",
        (provider,),
    ).fetchone()

    if not row:
        return

    last_reset = _parse_datetime(row["last_reset"])

    if datetime.utcnow() >= last_reset + timedelta(days=BILLING_DAYS):
        conn.execute(
            "UPDATE provider_quota SET used_tokens=0, last_reset=? WHERE provider=?",
            (datetime.utcnow().isoformat(), provider),
        )


def increment_quota(conn, provider: str, tokens: int) -> None:
    cursor = conn.execute(
        """
        UPDATE provider_quota
        SET used_tokens = used_tokens + ?
        WHERE provider=? AND used_tokens + ? <= monthly_limit
        """,
        (tokens, provider, tokens),
    )
    if cursor.rowcount == 0:
        raise RuntimeError("QUOTA_EXCEEDED")


def quota_percent(conn, provider: str) -> float:
    row = conn.execute(
        "SELECT used_tokens, monthly_limit FROM provider_quota WHERE provider=?",
        (provider,),
    ).fetchone()
    if not row:
        return 0.0

    used = row["used_tokens"]
    limit = row["monthly_limit"]
    if not limit:
        return 1.0

    return used / limit
