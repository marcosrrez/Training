"""
Workout log data models
"""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel


class CompletionQuality(str, Enum):
    FULL = "full"
    PARTIAL = "partial"
    MODIFIED = "modified"
    NOT_COMPLETED = "not_completed"


class PerceivedDifficulty(str, Enum):
    EASIER = "easier"
    AS_EXPECTED = "as_expected"
    HARDER = "harder"


class HeartRateData(BaseModel):
    """Heart rate data"""
    avg_bpm: int
    max_bpm: int
    time_in_zones: dict = {}  # zone: minutes


class PaceData(BaseModel):
    """Pace data"""
    avg_pace_min_per_mile: Optional[float] = None
    avg_pace_min_per_km: Optional[float] = None
    splits: List[float] = []  # pace for each mile/km


class PowerData(BaseModel):
    """Power data"""
    avg_watts: int
    max_watts: int
    normalized_power: Optional[int] = None


class ExerciseLog(BaseModel):
    """Log of a single exercise"""
    exercise_name: str
    sets_completed: int
    reps_completed: List[int]  # reps for each set
    weights_used: List[float]  # weight for each set
    rpe_per_set: List[int] = []  # RPE for each set
    notes: str = ""


class WellnessData(BaseModel):
    """Wellness metrics"""
    fatigue: int  # 1-5 scale
    soreness: int  # 1-5 scale
    mood: int  # 1-5 scale
    sleep_quality: int  # 1-5 scale
    sleep_hours: Optional[float] = None
    stress: int  # 1-5 scale
    motivation: int  # 1-5 scale
    hydration: Optional[int] = None  # 1-5 scale
    nutrition: Optional[int] = None  # 1-5 scale


class WorkoutLog(BaseModel):
    """Complete workout log"""
    log_id: str
    user_id: str
    session_id: str
    workout_id: str
    completed_at: datetime = datetime.utcnow()

    # Actual performance
    duration_minutes: float
    distance_miles: Optional[float] = None
    distance_km: Optional[float] = None
    elevation_feet: Optional[float] = None
    elevation_meters: Optional[float] = None

    # Recorded data
    heart_rate_data: Optional[HeartRateData] = None
    pace_data: Optional[PaceData] = None
    power_data: Optional[PowerData] = None

    # External tracking
    strava_activity_id: Optional[str] = None
    garmin_activity_id: Optional[str] = None

    # Strength data
    exercises_completed: List[ExerciseLog] = []

    # Subjective feedback
    perceived_exertion: int  # 1-10 (RPE)
    perceived_difficulty: PerceivedDifficulty
    completion_quality: CompletionQuality

    wellness: WellnessData

    # Notes
    notes: str = ""
    conditions: str = ""  # weather, location, etc.

    # Derived metrics
    training_load: Optional[float] = None  # TSS or similar
    fatigue_index: Optional[float] = None
    form_score: Optional[float] = None

    class Config:
        from_attributes = True


# Need to import Enum for CompletionQuality and PerceivedDifficulty
from enum import Enum
