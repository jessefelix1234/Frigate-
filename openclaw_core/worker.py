import time
from datetime import datetime, timedelta

from db import init_db, transaction
from logger import log_task_result
from model_gateway import route
from retry import classify_error, compute_backoff

STALE_TIMEOUT = 300  # seconds
IDLE_SLEEP_SECONDS = 1


def reclaim_stale(conn) -> None:
    conn.execute(
        """
        UPDATE tasks
        SET status='pending', updated_at=CURRENT_TIMESTAMP
        WHERE status='in_progress'
          AND strftime('%s','now') - strftime('%s',updated_at) > ?
        """,
        (STALE_TIMEOUT,),
    )


def _claim_next_task():
    with transaction() as conn:
        reclaim_stale(conn)

        task = conn.execute(
            """
            SELECT * FROM tasks
            WHERE status='pending'
              AND next_run_at <= CURRENT_TIMESTAMP
            ORDER BY priority ASC, created_at ASC
            LIMIT 1
            """
        ).fetchone()

        if not task:
            return None

        conn.execute(
            """
            UPDATE tasks
            SET status='in_progress', updated_at=CURRENT_TIMESTAMP
            WHERE task_id=?
            """,
            (task["task_id"],),
        )

        return dict(task)


def _handle_failure(task: dict, error_code: str) -> None:
    policy = classify_error(error_code)

    with transaction() as conn:
        if policy["retry"] and task["retry_count"] < task["max_retries"]:
            backoff = compute_backoff(policy["base_delay"], task["retry_count"])
            next_run = (datetime.utcnow() + timedelta(seconds=backoff)).isoformat()
            conn.execute(
                """
                UPDATE tasks
                SET status='pending',
                    retry_count=retry_count+1,
                    next_run_at=?,
                    last_error=?,
                    updated_at=CURRENT_TIMESTAMP
                WHERE task_id=?
                """,
                (next_run, error_code, task["task_id"]),
            )
        else:
            conn.execute(
                """
                INSERT INTO dead_letter_tasks (
                    task_id, task_type, payload, context_refs,
                    failure_type, failure_time, attempts, original_created
                )
                SELECT task_id, task_type, payload, context_refs,
                       ?, CURRENT_TIMESTAMP, retry_count, created_at
                FROM tasks
                WHERE task_id=?
                """,
                (error_code, task["task_id"]),
            )
            conn.execute("DELETE FROM tasks WHERE task_id=?", (task["task_id"],))


def worker_loop():
    init_db()

    while True:
        task = _claim_next_task()
        if not task:
            time.sleep(IDLE_SLEEP_SECONDS)
            continue

        try:
            result = route(task)
            with transaction() as conn:
                conn.execute(
                    """
                    UPDATE tasks
                    SET status='completed', updated_at=CURRENT_TIMESTAMP, last_error=NULL
                    WHERE task_id=?
                    """,
                    (task["task_id"],),
                )
            log_task_result(task, "success", result)
        except RuntimeError as error:
            error_code = str(error)
            _handle_failure(task, error_code)
            log_task_result(task, "failed", {})
        except Exception:
            _handle_failure(task, "UNKNOWN")
            log_task_result(task, "failed", {})


if __name__ == "__main__":
    worker_loop()
