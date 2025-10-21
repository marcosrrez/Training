"""
Goal data models
"""
from datetime import datetime
from typing import List, Optional, Union
from enum import Enum
from pydantic import BaseModel


class GoalType(str, Enum):
    ENDURANCE = "endurance"
    STRENGTH = "strength"
    COMPOSITION = "composition"
    HYBRID = "hybrid"
    GENERAL_FITNESS = "general_fitness"


class GoalPriority(str, Enum):
    PRIMARY = "primary"
    SECONDARY = "secondary"


class GoalStatus(str, Enum):
    ACTIVE = "active"
    ACHIEVED = "achieved"
    ABANDONED = "abandoned"
    ADJUSTED = "adjusted"


class EventType(str, Enum):
    FIVE_K = "5k"
    TEN_K = "10k"
    HALF_MARATHON = "half_marathon"
    MARATHON = "marathon"
    ULTRA = "ultra"
    CYCLING = "cycling"
    TRIATHLON = "triathlon"
    OTHER = "other"


class EnduranceGoal(BaseModel):
    """Endurance performance goal"""
    event: EventType
    target_time_seconds: float
    required_pace_min_per_mile: Optional[float] = None
    required_pace_min_per_km: Optional[float] = None


class ExerciseTarget(BaseModel):
    """Target for a specific exercise"""
    name: str
    target_weight: float  # lbs or kg
    target_reps: int = 1
    current_weight: Optional[float] = None


class StrengthGoal(BaseModel):
    """Strength performance goal"""
    exercises: List[ExerciseTarget]
    focus: str = "general"  # "powerlifting", "olympic_lifting", "hypertrophy", "general"


class CompositionGoal(BaseModel):
    """Body composition goal"""
    target_weight: float  # lbs or kg
    target_body_fat: Optional[float] = None  # percentage
    approach_rate: float = 1.0  # lbs or kg per week
    priority_balance: float = 0.0  # -1 (performance focus) to +1 (aesthetics focus)
    approach: str = "lose_fat"  # "lose_fat", "build_muscle", "recomposition"


class HybridGoal(BaseModel):
    """Hybrid goal combining multiple components"""
    endurance_component: Optional[EnduranceGoal] = None
    strength_component: Optional[StrengthGoal] = None
    composition_component: Optional[CompositionGoal] = None
    priority_weight: float = 0.5  # 0 (all endurance) to 1 (all strength)


class Adaptation(BaseModel):
    """Required physiological adaptation"""
    name: str
    description: str
    typical_timeline_weeks: int
    difficulty: str  # "easy", "moderate", "hard", "very_hard"


class Risk(BaseModel):
    """Risk factor"""
    factor: str
    severity: str  # "low", "moderate", "high"
    mitigation: str


class FeasibilityAssessment(BaseModel):
    """Goal feasibility assessment"""
    probability: float  # 0-1
    required_adaptations: List[Adaptation] = []
    estimated_timeline_weeks: int
    realistic_timeline_weeks: int
    risks: List[Risk] = []
    is_realistic: bool = True
    recommendation: str = ""


class Goal(BaseModel):
    """Training goal"""
    goal_id: str
    user_id: str
    type: GoalType
    priority: GoalPriority = GoalPriority.PRIMARY
    target_date: datetime
    created_at: datetime = datetime.utcnow()
    status: GoalStatus = GoalStatus.ACTIVE

    # Specific goal details (one of these should be populated)
    endurance_goal: Optional[EnduranceGoal] = None
    strength_goal: Optional[StrengthGoal] = None
    composition_goal: Optional[CompositionGoal] = None
    hybrid_goal: Optional[HybridGoal] = None

    # Feasibility assessment
    feasibility: Optional[FeasibilityAssessment] = None

    # Progress tracking
    current_progress: float = 0.0  # 0-1
    milestones_achieved: List[str] = []

    class Config:
        from_attributes = True
