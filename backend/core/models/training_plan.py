"""
Training plan data models
"""
from datetime import datetime, date
from typing import List, Optional, Dict
from enum import Enum
from pydantic import BaseModel


class PeriodizationModel(str, Enum):
    LINEAR = "linear"
    BLOCK = "block"
    CONJUGATE = "conjugate"
    UNDULATING = "undulating"


class VolumeProgression(str, Enum):
    BUILD = "build"
    MAINTAIN = "maintain"
    REDUCE = "reduce"


class IntensityZone(str, Enum):
    ZONE_1 = "zone_1"  # Recovery/Easy
    ZONE_2 = "zone_2"  # Aerobic/Base
    ZONE_3 = "zone_3"  # Tempo
    ZONE_4 = "zone_4"  # Threshold
    ZONE_5 = "zone_5"  # VO2max/Intervals


class IntensityDistribution(BaseModel):
    """Intensity distribution across zones"""
    zone_1_percentage: float = 0.0
    zone_2_percentage: float = 0.0
    zone_3_percentage: float = 0.0
    zone_4_percentage: float = 0.0
    zone_5_percentage: float = 0.0


class Methodology(BaseModel):
    """Training methodology"""
    name: str  # "polarized", "norwegian", "maf", "time_efficient_hiit", "hybrid"
    description: str
    periodization_model: PeriodizationModel
    intensity_distribution: IntensityDistribution


class Phase(BaseModel):
    """Macrocycle phase"""
    name: str
    start_week: int
    end_week: int
    duration_weeks: int
    focus: str
    description: str
    expected_outcomes: List[str] = []


class Macrocycle(BaseModel):
    """Overall periodization structure"""
    phases: List[Phase]
    total_weeks: int
    periodization_model: PeriodizationModel


class WorkoutTemplate(BaseModel):
    """Key workout template reference"""
    workout_id: str
    name: str
    description: str


class Mesocycle(BaseModel):
    """Training block (3-6 weeks)"""
    cycle_number: int
    start_week: int
    end_week: int
    duration_weeks: int
    focus: str
    volume_progression: VolumeProgression
    intensity_distribution: IntensityDistribution
    key_workouts: List[WorkoutTemplate] = []
    base_weekly_volume: float = 0.0  # hours
    recovery_frequency: int = 4  # recovery week every N weeks


class Volume(BaseModel):
    """Training volume metrics"""
    total_duration_minutes: float = 0.0
    total_distance_miles: Optional[float] = None
    running_volume: Optional[float] = None
    cycling_volume: Optional[float] = None
    strength_volume: Optional[float] = None


class SessionType(str, Enum):
    RUN = "run"
    CYCLE = "cycle"
    SWIM = "swim"
    STRENGTH = "strength"
    CROSS_TRAIN = "cross_train"
    REST = "rest"
    ACTIVE_RECOVERY = "active_recovery"


class SessionCategory(str, Enum):
    EASY = "easy"
    MODERATE = "moderate"
    HARD = "hard"
    RACE = "race"
    RECOVERY = "recovery"


class Session(BaseModel):
    """Individual training session"""
    session_id: str
    date: date
    type: SessionType
    category: SessionCategory

    # Workout reference (will be populated)
    workout_id: Optional[str] = None

    # Session planning
    estimated_duration_minutes: int
    estimated_tss: Optional[float] = None  # Training Stress Score
    required_equipment: List[str] = []
    coaching_notes: str = ""

    # Execution tracking
    completed: bool = False
    completed_at: Optional[datetime] = None
    workout_log_id: Optional[str] = None


class Microcycle(BaseModel):
    """Single week of training"""
    week_number: int
    start_date: date
    sessions: List[Session] = []
    total_volume: Volume = Volume()
    intensity_score: float = 0.0
    recovery_days: int = 0
    is_recovery_week: bool = False


class PlanAdjustment(BaseModel):
    """Record of plan adjustment"""
    adjustment_id: str
    timestamp: datetime
    type: str
    reason: str
    changes_made: Dict = {}


class PlanStatus(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    ABANDONED = "abandoned"
    PAUSED = "paused"


class TrainingPlan(BaseModel):
    """Complete training plan"""
    plan_id: str
    user_id: str
    goal_ids: List[str]

    # Plan metadata
    generated_at: datetime = datetime.utcnow()
    start_date: date
    end_date: date
    total_duration_weeks: int
    methodology: Methodology

    # Plan structure
    macrocycle: Macrocycle
    mesocycles: List[Mesocycle] = []
    microcycles: List[Microcycle] = []

    # Adaptation tracking
    adaptation_history: List[PlanAdjustment] = []
    last_adapted_at: Optional[datetime] = None

    # Status
    status: PlanStatus = PlanStatus.ACTIVE
    completion_rate: float = 0.0  # 0-1
    current_week: int = 0

    class Config:
        from_attributes = True
