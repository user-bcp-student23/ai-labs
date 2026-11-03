from __future__ import annotations

from fastapi import APIRouter, Query

from app.dependencies import IdentityDep, RepositoryDep
from app.repository import TaskRepository
from app.schemas import Identity, SummaryOut, TaskCreate, TaskOut
from app.services import resolve_owner, summarize_tasks

router = APIRouter(prefix="/api")


@router.get("/tasks", response_model=list[TaskOut])
def list_tasks(
    owner: str | None = Query(default=None),
    identity: Identity = IdentityDep,
    repository: TaskRepository = RepositoryDep,
) -> list[TaskOut]:
    owner_name = resolve_owner(owner, identity.username)
    return [TaskOut.from_row(row) for row in repository.list_by_owner(owner_name)]


@router.post("/tasks", status_code=201, response_model=TaskOut)
def create_task(
    task: TaskCreate,
    identity: Identity = IdentityDep,
    repository: TaskRepository = RepositoryDep,
) -> TaskOut:
    owner_name = resolve_owner(task.owner, identity.username)
    task_id = repository.insert(task, owner_name)
    return TaskOut.from_row(repository.get_by_id(task_id))


@router.get("/summary", response_model=SummaryOut)
def summary(
    owner: str | None = Query(default=None),
    identity: Identity = IdentityDep,
    repository: TaskRepository = RepositoryDep,
) -> SummaryOut:
    owner_name = resolve_owner(owner, identity.username)
    rows = repository.status_and_priority_by_owner(owner_name)
    return summarize_tasks(owner_name, rows)
