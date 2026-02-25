from db import transaction


def log_task_result(task: dict, outcome: str, result: dict | None = None) -> None:
    result = result or {}
    with transaction() as conn:
        conn.execute(
            """
            INSERT INTO task_logs(task_id, provider, token_estimate, token_actual, latency_ms, outcome)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                task["task_id"],
                result.get("provider"),
                task["token_estimate"],
                result.get("token_actual"),
                result.get("latency"),
                outcome,
            ),
        )
