"""
Health Records Management System
Manages user injury records, first aid steps, recovery tracking, and medical history.
"""

import streamlit as st
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from PIL import Image
import io
import base64


# Initialize health records in session state
def init_health_records():
    """Initialize health records storage in session state."""
    if 'health_records' not in st.session_state:
        st.session_state.health_records = []
    if 'current_record_id' not in st.session_state:
        st.session_state.current_record_id = None


def create_injury_record(
    injury_description: str,
    severity: str = "UNKNOWN",
    emergency_level: str = "ROUTINE",
    ai_analysis: Optional[str] = None,
    first_aid_steps: Optional[List[str]] = None,
    body_part: Optional[str] = None,
    location: Optional[str] = None,
    images: Optional[List[Any]] = None
) -> Dict[str, Any]:
    """
    Create a new injury record.
    
    Args:
        injury_description: Description of the injury
        severity: MINOR/MODERATE/SEVERE
        emergency_level: EMERGENCY/URGENT/ROUTINE
        ai_analysis: AI-generated analysis
        first_aid_steps: Recommended first aid steps
        body_part: Body part affected
        location: Location where injury occurred
        images: List of uploaded images
    
    Returns:
        Dict containing the injury record
    """
    record = {
        "id": str(uuid.uuid4()),
        "timestamp": datetime.now().isoformat(),
        "injury_type": injury_description,
        "description": injury_description,
        "severity": severity,
        "emergency_level": emergency_level,
        "body_part": body_part,
        "location": location,
        "status": "active",  # active, healing, healed, archived
        "initial_analysis": {
            "ai_analysis": ai_analysis or "",
            "severity": severity,
            "timestamp": datetime.now().isoformat()
        },
        "first_aid_steps": {
            "recommended": first_aid_steps or [],
            "completed": [],
            "notes": "",
            "completed_at": None
        },
        "photos": {
            "before": [],
            "during": [],
            "after": []
        },
        "recovery": {
            "status": "initial",  # initial, healing, recovering, healed
            "progress_percentage": 0,
            "pain_level": None,
            "updates": []
        },
        "medications": [],
        "notes": [],
        "reminders": [],
        "tags": [],
        "follow_up_care": {
            "doctor_visit": False,
            "visit_date": None,
            "notes": ""
        }
    }
    
    # Add initial photo if provided
    if images:
        for img in images:
            add_photo_to_record(record["id"], img, "before")
    
    return record


def save_record(record: Dict[str, Any]) -> bool:
    """Save a record to session state."""
    init_health_records()
    
    # Check if record already exists (update) or is new (add)
    existing_index = None
    for idx, r in enumerate(st.session_state.health_records):
        if r.get("id") == record.get("id"):
            existing_index = idx
            break
    
    if existing_index is not None:
        # Update existing record
        st.session_state.health_records[existing_index] = record
    else:
        # Add new record
        st.session_state.health_records.append(record)
    
    return True


def get_record(record_id: str) -> Optional[Dict[str, Any]]:
    """Get a specific record by ID."""
    init_health_records()
    for record in st.session_state.health_records:
        if record.get("id") == record_id:
            return record
    return None


def get_all_records(sort_by: str = "timestamp", reverse: bool = True) -> List[Dict[str, Any]]:
    """Get all records, sorted by specified field."""
    init_health_records()
    records = st.session_state.health_records.copy()
    
    if sort_by == "timestamp":
        records.sort(key=lambda x: x.get("timestamp", ""), reverse=reverse)
    elif sort_by == "severity":
        severity_order = {"SEVERE": 3, "MODERATE": 2, "MINOR": 1, "UNKNOWN": 0}
        records.sort(key=lambda x: severity_order.get(x.get("severity", "UNKNOWN"), 0), reverse=reverse)
    elif sort_by == "status":
        status_order = {"active": 3, "healing": 2, "healed": 1, "archived": 0}
        records.sort(key=lambda x: status_order.get(x.get("status", "active"), 0), reverse=reverse)
    
    return records


def filter_records(
    severity: Optional[str] = None,
    status: Optional[str] = None,
    body_part: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    search_query: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Filter records based on criteria."""
    records = get_all_records()
    filtered = records
    
    if severity:
        filtered = [r for r in filtered if r.get("severity") == severity]
    if status:
        filtered = [r for r in filtered if r.get("status") == status]
    if body_part:
        filtered = [r for r in filtered if r.get("body_part", "").lower() == body_part.lower()]
    if date_from:
        filtered = [r for r in filtered if datetime.fromisoformat(r.get("timestamp", "")) >= date_from]
    if date_to:
        filtered = [r for r in filtered if datetime.fromisoformat(r.get("timestamp", "")) <= date_to]
    if search_query:
        query_lower = search_query.lower()
        filtered = [
            r for r in filtered
            if query_lower in r.get("injury_type", "").lower()
            or query_lower in r.get("description", "").lower()
            or query_lower in r.get("body_part", "").lower()
        ]
    
    return filtered


def add_photo_to_record(record_id: str, image: Any, photo_type: str = "before") -> bool:
    """
    Add a photo to a record.
    
    Args:
        record_id: ID of the record
        image: Uploaded image file
        photo_type: "before", "during", or "after"
    """
    record = get_record(record_id)
    if not record:
        return False
    
    # Convert image to base64 for storage
    try:
        img = Image.open(image)
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()
        
        photo_entry = {
            "data": img_str,
            "timestamp": datetime.now().isoformat(),
            "type": photo_type
        }
        
        if photo_type in record["photos"]:
            record["photos"][photo_type].append(photo_entry)
        
        save_record(record)
        return True
    except Exception as e:
        st.error(f"Error adding photo: {e}")
        return False


def update_recovery_progress(
    record_id: str,
    progress_percentage: int,
    pain_level: Optional[int] = None,
    notes: Optional[str] = None,
    photo: Optional[Any] = None
) -> bool:
    """Update recovery progress for a record."""
    record = get_record(record_id)
    if not record:
        return False
    
    record["recovery"]["progress_percentage"] = progress_percentage
    if pain_level is not None:
        record["recovery"]["pain_level"] = pain_level
    
    # Add progress update
    update_entry = {
        "date": datetime.now().isoformat(),
        "progress": progress_percentage,
        "pain_level": pain_level,
        "notes": notes or ""
    }
    record["recovery"]["updates"].append(update_entry)
    
    # Update status based on progress
    if progress_percentage >= 100:
        record["status"] = "healed"
        record["recovery"]["status"] = "healed"
    elif progress_percentage >= 75:
        record["status"] = "recovering"
        record["recovery"]["status"] = "recovering"
    elif progress_percentage > 0:
        record["status"] = "healing"
        record["recovery"]["status"] = "healing"
    
    # Add photo if provided
    if photo:
        add_photo_to_record(record_id, photo, "during")
    
    save_record(record)
    return True


def mark_first_aid_step_completed(record_id: str, step_index: int, notes: Optional[str] = None) -> bool:
    """Mark a first aid step as completed."""
    record = get_record(record_id)
    if not record:
        return False
    
    recommended = record["first_aid_steps"]["recommended"]
    completed = record["first_aid_steps"]["completed"]
    
    if 0 <= step_index < len(recommended) and step_index not in completed:
        completed.append(step_index)
        if not record["first_aid_steps"]["completed_at"]:
            record["first_aid_steps"]["completed_at"] = datetime.now().isoformat()
        if notes:
            record["first_aid_steps"]["notes"] = notes
        save_record(record)
        return True
    
    return False


def add_note_to_record(record_id: str, note_content: str) -> bool:
    """Add a note to a record."""
    record = get_record(record_id)
    if not record:
        return False
    
    note = {
        "timestamp": datetime.now().isoformat(),
        "content": note_content
    }
    record["notes"].append(note)
    save_record(record)
    return True


def add_medication(
    record_id: str,
    name: str,
    dosage: str,
    frequency: Optional[str] = None
) -> bool:
    """Add medication to a record."""
    record = get_record(record_id)
    if not record:
        return False
    
    medication = {
        "name": name,
        "dosage": dosage,
        "frequency": frequency,
        "added_at": datetime.now().isoformat(),
        "taken": []
    }
    record["medications"].append(medication)
    save_record(record)
    return True


def get_statistics() -> Dict[str, Any]:
    """Get statistics about health records."""
    records = get_all_records()
    
    if not records:
        return {
            "total_records": 0,
            "by_severity": {},
            "by_status": {},
            "most_common_body_part": None,
            "average_recovery_time": None
        }
    
    # Count by severity
    severity_count = {}
    for record in records:
        sev = record.get("severity", "UNKNOWN")
        severity_count[sev] = severity_count.get(sev, 0) + 1
    
    # Count by status
    status_count = {}
    for record in records:
        status = record.get("status", "active")
        status_count[status] = status_count.get(status, 0) + 1
    
    # Most common body part
    body_parts = {}
    for record in records:
        bp = record.get("body_part")
        if bp:
            body_parts[bp] = body_parts.get(bp, 0) + 1
    
    most_common_body_part = max(body_parts.items(), key=lambda x: x[1])[0] if body_parts else None
    
    return {
        "total_records": len(records),
        "by_severity": severity_count,
        "by_status": status_count,
        "most_common_body_part": most_common_body_part,
        "active_injuries": len([r for r in records if r.get("status") == "active"]),
        "healed_injuries": len([r for r in records if r.get("status") == "healed"])
    }


def export_record_to_dict(record_id: str) -> Optional[Dict[str, Any]]:
    """Export a record as a dictionary (for JSON export)."""
    return get_record(record_id)


def delete_record(record_id: str) -> bool:
    """Delete a record."""
    init_health_records()
    st.session_state.health_records = [
        r for r in st.session_state.health_records
        if r.get("id") != record_id
    ]
    return True


def format_record_date(record: Dict[str, Any]) -> str:
    """Format record timestamp for display."""
    try:
        dt = datetime.fromisoformat(record.get("timestamp", ""))
        return dt.strftime("%B %d, %Y at %I:%M %p")
    except:
        return "Unknown date"


def get_record_age_days(record: Dict[str, Any]) -> int:
    """Get the age of a record in days."""
    try:
        dt = datetime.fromisoformat(record.get("timestamp", ""))
        delta = datetime.now() - dt
        return delta.days
    except:
        return 0

