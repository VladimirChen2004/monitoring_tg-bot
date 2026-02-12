from bot.tasks.base import BaseTask, TaskHealthReport


class TaskRegistry:

    def __init__(self):
        self._tasks: dict[str, BaseTask] = {}

    def register(self, task: BaseTask):
        self._tasks[task.name] = task

    def get(self, name: str) -> BaseTask | None:
        return self._tasks.get(name)

    def all(self) -> list[BaseTask]:
        return list(self._tasks.values())

    def names(self) -> list[str]:
        return list(self._tasks.keys())

    async def run_all_checks(self) -> dict[str, TaskHealthReport]:
        results = {}
        for name, task in self._tasks.items():
            results[name] = await task.run_health_checks()
        return results
