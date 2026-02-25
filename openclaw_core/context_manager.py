def append_summary(conn, task_id: str, summary: str) -> None:
    conn.execute(
        """
        INSERT INTO live_context(task_id, summary)
        VALUES (?, ?)
        """,
        (task_id, summary),
    )
