from __future__ import annotations

from typing import TypeAliasType

from pydantic import BaseModel, ConfigDict, Field

JsonValue = TypeAliasType(
    "JsonValue",
    str | int | float | bool | None | list["JsonValue"] | dict[str, "JsonValue"],
)


class Identity(BaseModel):
    username: str
    role: str


class TaskCreateRequest(BaseModel):
    title: JsonValue = ""
    description: JsonValue = ""
    status: JsonValue = "TODO"
    priority: JsonValue = "MEDIUM"
    owner: JsonValue = None


class TaskResponse(BaseModel):
    id: int
    title: str
    description: str
    status: str
    owner: str
    priority: str
    created_at: str = Field(alias="createdAt")

    model_config = ConfigDict(populate_by_name=True)


class TaskSummaryResponse(BaseModel):
    owner: str
    total: int
    by_status: dict[str, int] = Field(alias="byStatus")
    high_priority_open: int = Field(alias="highPriorityOpen")

    model_config = ConfigDict(populate_by_name=True)


class BackendHealthResponse(BaseModel):
    requested_by: str = Field(alias="requestedBy")
    status: int
    body: str

    model_config = ConfigDict(populate_by_name=True)


class UploadResponse(BaseModel):
    owner: str
    file_name: str = Field(alias="fileName")
    stored_at: str = Field(alias="storedAt")
    size: int

    model_config = ConfigDict(populate_by_name=True)
