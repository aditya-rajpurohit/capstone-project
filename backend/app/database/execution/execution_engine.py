import asyncio
import time

from app.core.constants import DEFAULT_TIMEOUT_SECONDS
from app.core.exceptions import DataSourceExecutionError
from app.database.connectors.base_connector import BaseConnector
from app.engine.contracts.execution_contract import ExecutionResult


class ExecutionEngine:
    """
    Deterministic execution wrapper.
    - Does NOT validate SQL
    - Does NOT modify SQL
    - Only executes and wraps output
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

        except DataSourceExecutionError as e:
            return ExecutionResult(
                status="failed",
                error_type="datasource_error",
                error_message=str(e),
            )

        except Exception as e:
            return ExecutionResult(
                status="failed",
                error_type="unknown_error",
                error_message=str(e),
            )
