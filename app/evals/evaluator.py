import asyncio
import json
from pathlib import Path

from app.engine.context.chat_context import ChatContext
from app.engine.orchestration.execution_controller import ExecutionController
from app.evals.metrics.execution_accuracy import execution_accuracy
from app.runtime.chat.chat_memory import ChatMemory

DATASET_PATH = Path(__file__).parent / "datasets" / "golden_queries.json"


class Evaluator:

    def __init__(self, controller: ExecutionController):
        self.controller = controller

    async def run(self):

        dataset = json.loads(DATASET_PATH.read_text())

        results = []

        for case in dataset:

            query = case["query"]
            expected_fragment = case["expected_sql_contains"]

            chat_context = ChatContext(active_database_ids=["test_db"])
            chat_memory = ChatMemory(session_id="eval-session")

            trace = await self.controller.run(
                query,
                chat_context,
                chat_memory,
            )

            generated_sql = None
            ok = False

            if trace.per_db_results is not None:
                for db_ctx in trace.per_db_results.values():
                    generated_sql = db_ctx.get("generated_sql")

            if generated_sql is not None:
                ok = execution_accuracy(expected_fragment, generated_sql)

            results.append(
                {
                    "query": query,
                    "generated_sql": generated_sql,
                    "pass": ok,
                }
            )

        return results


async def main(controller: ExecutionController):

    evaluator = Evaluator(controller)

    results = await evaluator.run()

    passed = sum(1 for r in results if r["pass"])

    print("Evaluation results")
    print("------------------")

    for r in results:
        print(r)

    print(f"\nPassed: {passed}/{len(results)}")


# if __name__ == "__main__":
# asyncio.run(main())
