import asyncio
import time

from asyncpg.exceptions import PostgresError

from app.core.constants import DEFAULT_TIMEOUT_SECONDS
from app.schemas.execution_schema import ExecutionResult
from app.tools.db_connector.base_connector import BaseConnector


class ExecutionEngine:
    """
    Deterministic execution wrapper.
    Does NOT validate SQL or inject limits.
    Only executes and structures output.
    """

    def __init__(self, connector: BaseConnector) -> None:
        self.connector = connector

    async def execute(self, sql: str) -> ExecutionResult:
        start = time.perf_counter()

        try:
            rows = await asyncio.wait_for(
                self.connector.execute(sql),
                timeout=DEFAULT_TIMEOUT_SECONDS,
            )

            elapsed_ms = int((time.perf_counter() - start) * 1000)

            return ExecutionResult(
                status="success",
                rows=rows,
                row_count=len(rows),
                elapsed_ms=elapsed_ms,
            )

        except asyncio.TimeoutError:
            return ExecutionResult(
                status="failed",
                error_type="timeout",
                error_message="Query execution exceeded timeout.",
            )

        except PostgresError as e:
            return ExecutionResult(
                status="failed",
                error_type="postgres_error",
                error_message=str(e),
            )

        except Exception as e:
            return ExecutionResult(
                status="failed",
                error_type="unknown_error",
                error_message=str(e),
            )
