"""
Announcement endpoints for the High School Management System API
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from bson import ObjectId
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field, validator

from ..database import announcements_collection, teachers_collection

router = APIRouter(
    prefix="/announcements",
    tags=["announcements"],
)


class AnnouncementPayload(BaseModel):
    title: str = Field(..., min_length=2, max_length=80)
    message: str = Field(..., min_length=2, max_length=300)
    start_date: Optional[datetime] = None
    end_date: datetime

    @validator("title", "message")
    def normalize_text(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Text cannot be empty")
        return cleaned

    @validator("start_date", "end_date", pre=True)
    def ensure_timezone(cls, value: Optional[datetime]) -> Optional[datetime]:
        if value is None:
            return value
        if isinstance(value, datetime) and value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value

    @validator("end_date")
    def validate_date_range(cls, end_date: datetime, values: Dict[str, Any]) -> datetime:
        start_date = values.get("start_date")
        if start_date and end_date < start_date:
            raise ValueError("End date must be after start date")
        return end_date


class AnnouncementUpdatePayload(BaseModel):
    title: Optional[str] = Field(None, min_length=2, max_length=80)
    message: Optional[str] = Field(None, min_length=2, max_length=300)
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

    @validator("title", "message")
    def normalize_text(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Text cannot be empty")
        return cleaned

    @validator("start_date", "end_date", pre=True)
    def ensure_timezone(cls, value: Optional[datetime]) -> Optional[datetime]:
        if value is None:
            return value
        if isinstance(value, datetime) and value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value


def _serialize_announcement(doc: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": str(doc.get("_id")),
        "title": doc.get("title", ""),
        "message": doc.get("message", ""),
        "start_date": doc.get("start_date").isoformat() if doc.get("start_date") else None,
        "end_date": doc.get("end_date").isoformat() if doc.get("end_date") else None,
        "created_at": doc.get("created_at").isoformat() if doc.get("created_at") else None,
        "updated_at": doc.get("updated_at").isoformat() if doc.get("updated_at") else None,
    }


def _require_teacher(teacher_username: Optional[str]) -> None:
    if not teacher_username:
        raise HTTPException(status_code=401, detail="Authentication required")

    teacher = teachers_collection.find_one({"_id": teacher_username})
    if not teacher:
        raise HTTPException(status_code=401, detail="Invalid teacher credentials")


@router.get("", response_model=List[Dict[str, Any]])
@router.get("/", response_model=List[Dict[str, Any]])
def get_active_announcements() -> List[Dict[str, Any]]:
    """Get active announcements for display"""
    now = datetime.now(timezone.utc)
    query = {
        "$and": [
            {"end_date": {"$gte": now}},
            {
                "$or": [
                    {"start_date": {"$lte": now}},
                    {"start_date": None},
                    {"start_date": {"$exists": False}},
                ]
            },
        ]
    }

    announcements = announcements_collection.find(query).sort("end_date", 1)
    return [_serialize_announcement(doc) for doc in announcements]


@router.get("/manage", response_model=List[Dict[str, Any]])
def get_all_announcements(teacher_username: Optional[str] = Query(None)) -> List[Dict[str, Any]]:
    """Get all announcements for management"""
    _require_teacher(teacher_username)
    announcements = announcements_collection.find().sort("updated_at", -1)
    return [_serialize_announcement(doc) for doc in announcements]


@router.post("", response_model=Dict[str, Any])
@router.post("/", response_model=Dict[str, Any])
def create_announcement(
    payload: AnnouncementPayload,
    teacher_username: Optional[str] = Query(None),
) -> Dict[str, Any]:
    """Create a new announcement"""
    _require_teacher(teacher_username)

    now = datetime.now(timezone.utc)
    announcement = {
        "title": payload.title,
        "message": payload.message,
        "start_date": payload.start_date,
        "end_date": payload.end_date,
        "created_at": now,
        "updated_at": now,
    }

    result = announcements_collection.insert_one(announcement)
    announcement["_id"] = result.inserted_id
    return _serialize_announcement(announcement)


@router.put("/{announcement_id}", response_model=Dict[str, Any])
def update_announcement(
    announcement_id: str,
    payload: AnnouncementUpdatePayload,
    teacher_username: Optional[str] = Query(None),
) -> Dict[str, Any]:
    """Update an announcement"""
    _require_teacher(teacher_username)

    try:
        announcement_object_id = ObjectId(announcement_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid announcement id")

    existing = announcements_collection.find_one({"_id": announcement_object_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Announcement not found")

    updated_start = payload.start_date if payload.start_date is not None else existing.get("start_date")
    updated_end = payload.end_date if payload.end_date is not None else existing.get("end_date")
    if not updated_end:
        raise HTTPException(status_code=400, detail="End date is required")
    if updated_start and updated_end < updated_start:
        raise HTTPException(status_code=400, detail="End date must be after start date")

    update_fields: Dict[str, Any] = {"updated_at": datetime.now(timezone.utc)}
    if payload.title is not None:
        update_fields["title"] = payload.title
    if payload.message is not None:
        update_fields["message"] = payload.message
    if payload.start_date is not None:
        update_fields["start_date"] = payload.start_date
    if payload.end_date is not None:
        update_fields["end_date"] = payload.end_date

    announcements_collection.update_one(
        {"_id": announcement_object_id},
        {"$set": update_fields},
    )

    refreshed = announcements_collection.find_one({"_id": announcement_object_id})
    return _serialize_announcement(refreshed)


@router.delete("/{announcement_id}", response_model=Dict[str, Any])
def delete_announcement(
    announcement_id: str,
    teacher_username: Optional[str] = Query(None),
) -> Dict[str, Any]:
    """Delete an announcement"""
    _require_teacher(teacher_username)

    try:
        announcement_object_id = ObjectId(announcement_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid announcement id")

    result = announcements_collection.delete_one({"_id": announcement_object_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Announcement not found")

    return {"status": "deleted"}
