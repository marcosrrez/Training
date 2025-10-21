"""
Workout data models
"""
from typing import List, Optional, Union
from enum import Enum
from pydantic import BaseModel


class WorkoutType(str, Enum):
    ENDURANCE = "endurance"
    STRENGTH = "strength"
    HYBRID = "hybrid"
    RECOVERY = "recovery"
    TEST = "test"


class BlockType(str, Enum):
    WARMUP = "warmup"
    MAIN = "main"
    COOLDOWN = "cooldown"
    RECOVERY = "recovery"


class IntensityType(str, Enum):
    ZONE = "zone"
    PACE = "pace"
    HEART_RATE = "heart_rate"
    POWER = "power"
    RPE = "rpe"  # Rate of Perceived Exertion
    PERCENTAGE_MAX = "percentage_max"


class Intensity(BaseModel):
    """Intensity specification"""
    type: IntensityType
    target: Union[float, str]  # zone number, pace (min/mile), HR (bpm), power (watts), RPE (1-10)
    range_min: Optional[float] = None
    range_max: Optional[float] = None
    description: str = ""


class Interval(BaseModel):
    """Interval specification"""
    work_duration: int  # seconds
    work_intensity: Intensity
    rest_duration: int  # seconds
    rest_intensity: Intensity
    repetitions: int
    notes: str = ""


class Exercise(BaseModel):
    """Strength exercise"""
    name: str
    sets: int
    reps: Union[int, List[int]]  # fixed or range [min, max]
    weight: Optional[Union[float, str]] = None  # lbs/kg or "bodyweight" or "75% 1RM"
    tempo: Optional[str] = None  # e.g., "3-1-2-1" (eccentric-pause-concentric-pause)
    rest_seconds: int = 60
    rpe_target: Optional[int] = None  # 1-10
    notes: str = ""


class WorkoutBlock(BaseModel):
    """Section of a workout"""
    order: int
    type: BlockType
    intervals: List[Interval] = []
    exercises: List[Exercise] = []
    duration_minutes: Optional[int] = None
    distance_miles: Optional[float] = None
    instructions: str = ""


class PaceTarget(BaseModel):
    """Pace target"""
    min_per_mile: Optional[float] = None
    min_per_km: Optional[float] = None


class HeartRateTarget(BaseModel):
    """Heart rate target"""
    min_bpm: int
    max_bpm: int
    avg_target: Optional[int] = None


class PowerTarget(BaseModel):
    """Power target"""
    min_watts: int
    max_watts: int
    avg_target: Optional[int] = None


class WeightTarget(BaseModel):
    """Weight target for exercise"""
    weight: float
    unit: str = "lbs"  # lbs or kg
    percentage_1rm: Optional[float] = None


class Workout(BaseModel):
    """Complete workout specification"""
    workout_id: str
    name: str
    description: str
    type: WorkoutType

    structure: List[WorkoutBlock] = []

    # Intensity prescription
    target_zones: List[str] = []
    pace_targets: List[PaceTarget] = []
    heart_rate_targets: List[HeartRateTarget] = []
    power_targets: List[PowerTarget] = []
    weight_targets: List[WeightTarget] = []

    # Metadata
    difficulty_rating: int  # 1-5
    focus_areas: List[str] = []
    research_basis: List[str] = []  # Citations
    estimated_duration_minutes: int = 0
    required_equipment: List[str] = []
    coaching_notes: str = ""

    # Alternatives
    substitute_workout_ids: List[str] = []

    class Config:
        from_attributes = True
