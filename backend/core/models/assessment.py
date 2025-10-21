"""
Assessment data models
"""
from datetime import datetime
from typing import List, Dict, Optional
from pydantic import BaseModel


class BodyComposition(BaseModel):
    """Body composition data"""
    weight: float  # lbs or kg
    body_fat_percentage: Optional[float] = None
    lean_mass: Optional[float] = None
    height: Optional[float] = None


class RaceResult(BaseModel):
    """Race result record"""
    event: str  # "5k", "10k", "half_marathon", "marathon", etc.
    time_seconds: float
    date: datetime
    effort_level: str = "all_out"  # all_out, hard, moderate


class PaceZones(BaseModel):
    """Estimated pace zones"""
    zone1_min_per_mile: Optional[float] = None  # Easy/Recovery
    zone2_min_per_mile: Optional[float] = None  # Aerobic
    zone3_min_per_mile: Optional[float] = None  # Tempo
    zone4_min_per_mile: Optional[float] = None  # Threshold
    zone5_min_per_mile: Optional[float] = None  # VO2max


class EnduranceMetrics(BaseModel):
    """Endurance performance metrics"""
    vo2max: Optional[float] = None  # mL/kg/min
    lactate_threshold: Optional[float] = None  # % of VO2max or HR
    recent_races: List[RaceResult] = []
    estimated_paces: Optional[PaceZones] = None
    resting_heart_rate: Optional[int] = None
    max_heart_rate: Optional[int] = None


class BodyweightRatios(BaseModel):
    """Strength relative to bodyweight"""
    squat: float = 0.0  # multiple of bodyweight
    deadlift: float = 0.0
    bench: float = 0.0
    overhead_press: float = 0.0


class StrengthMetrics(BaseModel):
    """Strength performance metrics"""
    one_rep_maxes: Dict[str, float] = {}  # exercise_name: weight in lbs/kg
    bodyweight_ratios: BodyweightRatios = BodyweightRatios()
    estimated: bool = True  # whether values are estimated or tested


class PerformanceRecord(BaseModel):
    """Peak performance record"""
    type: str  # "race", "lift", "test"
    description: str
    value: float
    date: datetime


class TrainingHistory(BaseModel):
    """Training history"""
    years_of_training: float = 0.0
    recent_weekly_volume: float = 0.0  # hours per week
    detraining_period_months: float = 0.0
    peak_performances: List[PerformanceRecord] = []
    training_types: List[str] = []  # ["running", "cycling", "strength_training", etc.]


class Injury(BaseModel):
    """Injury record"""
    type: str
    location: str  # "knee", "lower_back", "shoulder", etc.
    status: str  # "current", "resolved", "recurring"
    description: str
    date_occurred: Optional[datetime] = None


class Health(BaseModel):
    """Health and limitations"""
    injuries: List[Injury] = []
    medical_conditions: List[str] = []
    movement_limitations: List[str] = []
    medications: List[str] = []
    pregnancy_status: Optional[str] = None  # "not_pregnant", "pregnant", "postpartum"
    healthcare_clearance: bool = False


class Lifestyle(BaseModel):
    """Lifestyle factors"""
    sleep_hours: float = 7.0
    sleep_quality: int = 3  # 1-5 scale
    stress_level: int = 3  # 1-5 scale
    work_type: str = "sedentary"  # "sedentary", "light", "moderate", "heavy"
    protein_intake_grams: Optional[float] = None
    nutrition_quality: int = 3  # 1-5 scale
    alcohol_consumption: str = "moderate"  # "none", "low", "moderate", "high"
    smoking: bool = False


class Assessment(BaseModel):
    """Complete fitness assessment"""
    user_id: str
    assessment_id: str
    completed_at: datetime = datetime.utcnow()

    # Physical stats
    body_composition: BodyComposition

    # Fitness benchmarks
    endurance_metrics: EnduranceMetrics = EnduranceMetrics()
    strength_metrics: StrengthMetrics = StrengthMetrics()

    # Training history
    training_history: TrainingHistory = TrainingHistory()

    # Health & limitations
    health: Health = Health()

    # Lifestyle context
    lifestyle: Lifestyle = Lifestyle()

    # Calculated fitness level
    fitness_score: Optional[float] = None  # 0-100
    fitness_category: Optional[str] = None  # "beginner", "novice", "intermediate", "advanced", "elite"

    class Config:
        from_attributes = True
