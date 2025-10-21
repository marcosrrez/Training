"""
Constraint data models
"""
from datetime import datetime
from typing import List, Dict, Optional
from enum import Enum
from pydantic import BaseModel


class DayOfWeek(str, Enum):
    MONDAY = "monday"
    TUESDAY = "tuesday"
    WEDNESDAY = "wednesday"
    THURSDAY = "thursday"
    FRIDAY = "friday"
    SATURDAY = "saturday"
    SUNDAY = "sunday"


class TimeOfDay(str, Enum):
    MORNING = "morning"
    MIDDAY = "midday"
    EVENING = "evening"
    FLEXIBLE = "flexible"


class ScheduleConsistency(str, Enum):
    STABLE = "stable"
    VARIABLE = "variable"
    UNPREDICTABLE = "unpredictable"


class SessionRange(BaseModel):
    """Range with min and max values"""
    min: int
    max: int
    target: Optional[int] = None


class TimeConstraints(BaseModel):
    """Time availability constraints"""
    sessions_per_week: SessionRange
    session_duration_minutes: SessionRange
    preferred_days: List[DayOfWeek] = []
    preferred_times: List[TimeOfDay] = []
    schedule_consistency: ScheduleConsistency = ScheduleConsistency.STABLE
    total_weekly_hours: Optional[float] = None


class TrainingLocation(str, Enum):
    COMMERCIAL_GYM = "commercial_gym"
    HOME_GYM = "home_gym"
    OUTDOOR = "outdoor"
    TRACK = "track"
    POOL = "pool"
    MULTIPLE = "multiple"


class Equipment(BaseModel):
    """Available equipment"""
    # Cardio equipment
    treadmill: bool = False
    stationary_bike: bool = False
    rowing_machine: bool = False
    outdoor_running: bool = True
    track_access: bool = False
    pool_access: bool = False

    # Strength equipment
    full_squat_rack: bool = False
    barbells_and_plates: bool = False
    dumbbells: bool = False
    dumbbell_max_weight: Optional[float] = None
    kettlebells: bool = False
    resistance_bands: bool = False
    pullup_bar: bool = False
    bodyweight_only: bool = False

    # Technology
    gps_watch: bool = False
    gps_watch_brand: Optional[str] = None
    heart_rate_monitor: bool = False
    power_meter: bool = False
    smart_trainer: bool = False
    lactate_meter: bool = False


class BudgetCategory(str, Enum):
    MINIMAL = "minimal"
    MODERATE = "moderate"
    FLEXIBLE = "flexible"


class Budget(BaseModel):
    """Budget constraints"""
    monthly_budget: Optional[float] = None
    category: BudgetCategory = BudgetCategory.MODERATE


class ResourceConstraints(BaseModel):
    """Resource availability constraints"""
    training_locations: List[TrainingLocation] = [TrainingLocation.OUTDOOR]
    equipment: Equipment = Equipment()
    budget: Budget = Budget()


class RiskTolerance(str, Enum):
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"


class ProgressionPreference(str, Enum):
    SLOW = "slow"
    MODERATE = "moderate"
    FAST = "fast"


class ComplexityPreference(str, Enum):
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"


class SupportLevel(str, Enum):
    HIGH = "high"
    MODERATE = "moderate"
    LOW = "low"


class CoachingPreference(str, Enum):
    SELF = "self"
    APP_ONLY = "app_only"
    REMOTE = "remote"
    IN_PERSON = "in_person"


class SupportSystem(BaseModel):
    """Support system"""
    training_partners: bool = False
    family_support: SupportLevel = SupportLevel.MODERATE
    coaching_preference: CoachingPreference = CoachingPreference.APP_ONLY


class PersonalConstraints(BaseModel):
    """Personal preferences and constraints"""
    injury_risk_tolerance: RiskTolerance = RiskTolerance.MODERATE
    progression_preference: ProgressionPreference = ProgressionPreference.MODERATE
    complexity_preference: ComplexityPreference = ComplexityPreference.MODERATE
    support_system: SupportSystem = SupportSystem()


class Constraints(BaseModel):
    """Complete set of user constraints"""
    user_id: str
    constraint_id: str
    updated_at: datetime = datetime.utcnow()

    time: TimeConstraints
    resources: ResourceConstraints = ResourceConstraints()
    personal: PersonalConstraints = PersonalConstraints()

    class Config:
        from_attributes = True
