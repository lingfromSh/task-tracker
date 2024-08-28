import argparse
import json
import os
import typing
from dataclasses import dataclass
from datetime import datetime, UTC



class TaskNotFound(Exception):
    ...


class TaskStatus:

    TODO = "todo"
    IN_PROGRESS = "in-progress"
    DONE = "done"

@dataclass
class Task:

    id: int
    description: str
    status: str
    createdAt: datetime
    updatedAt: datetime
    isDeleted: bool

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "description": self.description,
            "status": self.status,
            "createdAt": self.createdAt.isoformat(),
            "updatedAt": self.updatedAt.isoformat(),
            "isDeleted": self.isDeleted,
        }

    @classmethod
    def from_dict(cls, data: dict) -> typing.Self:
        return cls(
            id = data["id"],
            description = data["description"],
            status = data["status"],
            createdAt = datetime.fromisoformat(data["createdAt"]),
            updatedAt = datetime.fromisoformat(data["updatedAt"]),
            isDeleted = data["isDeleted"],
        )

    def save(self, store: "TaskStore"):
        store.save_task(self)


class TaskStore:

    def __init__(self, file_path: str):
        self.file_path = file_path

    def init(self, force=True):
        """
        Initialize a new task store.
        """
        if os.path.exists(self.file_path) and not force:
            print("task store already exists!")
            return

        with open(self.file_path, "w+") as f:
            json.dump([], f)

    def load_tasks(self):
        """
        Load tasks from the task store.

        If the task store does not exist, it will be initialized.
        If the task store is in wrong format or broken, it will be recreated as a new one.
        """
        if not os.path.exists(self.file_path):
            self.init()

        with open(self.file_path, "r") as f:
            try:
                tasks = json.load(f)
                return [Task.from_dict(task) for task in tasks]
            except (json.JSONDecodeError, KeyError):
                print("task store is broken!")
                print("creating a new one...")
                self.init(force=True)
                return []

    def get_num_of_tasks(self) -> int:
        return len(self.load_tasks())

    def save_task(self, task: Task):
        tasks = self.load_tasks()
        task.updatedAt = datetime.now()
        if len(tasks) < task.id:
            tasks.insert(task.id-1, task)
        else:
            tasks[task.id - 1] = task
        with open(self.file_path, "w") as f:
            json.dump([task.to_dict() for task in tasks], f)

    def get_task(self, task_id: int) -> Task:
        try:
            tasks = self.load_tasks()
            task = tasks[task_id-1]
            if task.isDeleted:
                print(f"(ID: {task_id}) is not found")
                raise TaskNotFound
            return task
        except IndexError:
            print(f"(ID: {task_id}) is not found")
            raise TaskNotFound

class TaskManager:

    def __init__(self, task_store: TaskStore):
        self.store = task_store

    def list_tasks(self, status: typing.Literal["todo", "in-progress", "done"] | None = None) -> list[Task]:
        tasks = self.store.load_tasks()
        if status is None:
            allowed_status = ["todo", "in-progress", "done"]
        else:
            allowed_status = [status]
        tasks = [task for task in tasks if task.status in allowed_status and task.isDeleted is False]
        for task in tasks:
            print(f"Task(ID: {task.id}) desc={task.description} status={task.status} createdAt={task.createdAt.strftime('%Y-%m-%d %H:%M:%S')} updatedAt={task.updatedAt.strftime('%Y-%m-%d %H:%M:%S')}")
        return tasks

    def add_task(self, description: str) -> bool:
        try:
            task = Task(
                id=self.store.get_num_of_tasks() + 1,
                description=description,
                status=TaskStatus.TODO,
                createdAt=datetime.now(),
                updatedAt=datetime.now(),
                isDeleted=False
            )
            task.save(self.store)
            print(f"Task added successfully (ID: {task.id})")
            return True
        except Exception:
            return False

    def remove_task(self, task_id: int) -> bool:
        try:
            task = self.store.get_task(task_id)
            task.isDeleted = True
            task.save(self.store)
            print(f"Task removed successfully (ID: {task.id})")
            return True
        except TaskNotFound:
            return False

    def update_task_status(self, task_id: int , status: typing.Literal["todo", "in-progress", "done"]) -> bool:
        try:
            task = self.store.get_task(task_id)
            task.status = status
            task.save(self.store)
            print(f"Update task status successfully (ID: {task_id})")
            return True
        except Exception:
            return False


if __name__ == "__main__":
    s = TaskStore("todo.json")
    m = TaskManager(s)
    m.add_task("Buy something")
    m.remove_task(1)
    m.update_task_status(2, "done")
    m.list_tasks("done")
