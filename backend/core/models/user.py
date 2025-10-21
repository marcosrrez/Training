"""
User data models
"""
from datetime import datetime
from typing import Optional
from enum import Enum
from pydantic import BaseModel, EmailStr


class SubscriptionTier(str, Enum):
    FREE = "free"
    PREMIUM = "premium"
    ELITE = "elite"


class SubscriptionStatus(str, Enum):
    ACTIVE = "active"
    CANCELED = "canceled"
    EXPIRED = "expired"


class UnitSystem(str, Enum):
    IMPERIAL = "imperial"
    METRIC = "metric"


class BiologicalSex(str, Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"


class UserProfile(BaseModel):
    """User profile information"""
    name: str
    age: int
    biological_sex: BiologicalSex
    timezone: str = "UTC"
    units: UnitSystem = UnitSystem.IMPERIAL


class NotificationPreferences(BaseModel):
    """Notification preferences"""
    daily_workout_reminders: bool = True
    weekly_progress_summaries: bool = True
    plan_adjustment_alerts: bool = True
    community_activity: bool = False
    educational_tips: bool = True


class PrivacySettings(BaseModel):
    """Privacy settings"""
    profile_visibility: str = "private"  # private, friends, public
    share_workouts: bool = False
    share_progress: bool = False


class TrainingPreferences(BaseModel):
    """Training preferences"""
    methodology_preference: str = "auto"  # auto, polarized, norwegian, maf, hiit
    progression_preference: str = "moderate"  # conservative, moderate, aggressive
    complexity_preference: str = "moderate"  # simple, moderate, complex
    flexibility_preference: str = "adaptive"  # rigid, flexible, adaptive
    feedback_detail_level: str = "moderate"  # minimal, moderate, detailed, research


class DisplayPreferences(BaseModel):
    """Display preferences"""
    theme: str = "light"  # light, dark, auto
    language: str = "en"
    distance_unit: str = "miles"  # miles, kilometers
    weight_unit: str = "lbs"  # lbs, kg
    temperature_unit: str = "fahrenheit"  # fahrenheit, celsius


class UserPreferences(BaseModel):
    """User preferences"""
    notifications: NotificationPreferences = NotificationPreferences()
    privacy: PrivacySettings = PrivacySettings()
    training: TrainingPreferences = TrainingPreferences()
    display: DisplayPreferences = DisplayPreferences()


class Subscription(BaseModel):
    """Subscription information"""
    tier: SubscriptionTier = SubscriptionTier.FREE
    status: SubscriptionStatus = SubscriptionStatus.ACTIVE
    expires_at: Optional[datetime] = None
    stripe_customer_id: Optional[str] = None
    stripe_subscription_id: Optional[str] = None


class User(BaseModel):
    """User model"""
    id: str
    email: EmailStr
    hashed_password: str
    profile: UserProfile
    subscription: Subscription = Subscription()
    preferences: UserPreferences = UserPreferences()
    created_at: datetime = datetime.utcnow()
    last_active: datetime = datetime.utcnow()
    is_active: bool = True
    is_verified: bool = False

    class Config:
        from_attributes = True
