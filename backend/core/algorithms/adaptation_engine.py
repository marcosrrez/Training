"""
Plan Adaptation Engine

Analyzes real-world performance and adapts training plans based on:
- Workout completion quality
- Perceived difficulty vs expected
- Load monitoring (acute:chronic workload ratio)
- Recovery quality
- Performance trends

Research basis:
- Gabbett (2016): Acute:Chronic Workload Ratio for injury prevention
- Foster (1998): Training load monitoring
- Banister (1975): Fitness-fatigue model
- Kiely (2012): Periodization paradigms and individualization
"""

from typing import List, Dict, Optional, Tuple
from datetime import datetime, date, timedelta
from enum import Enum

from core.models.training_plan import TrainingPlan, Microcycle, Session
from core.models.workout_log import WorkoutLog, CompletionQuality, PerceivedDifficulty
from core.models.assessment import Assessment
from core.models.constraint import Constraints


class AdaptationTrigger(str, Enum):
    """Reasons for plan adaptation"""
    CONSISTENT_UNDERPERFORMANCE = "consistent_underperformance"
    CONSISTENT_OVERPERFORMANCE = "consistent_overperformance"
    POOR_RECOVERY = "poor_recovery"
    INJURY_RISK = "injury_risk"  # High ACWR
    ILLNESS = "illness"
    LIFE_EVENT = "life_event"
    MISSED_SESSIONS = "missed_sessions"
    GOAL_ADJUSTMENT = "goal_adjustment"


class AdaptationType(str, Enum):
    """Types of adaptations"""
    MICRO = "micro"  # Next 1-3 sessions
    MESO = "meso"   # Rest of current week + next week
    MACRO = "macro"  # Adjust current phase
    REGENERATE = "regenerate"  # Full plan regeneration


class AdaptationRecommendation:
    """Recommendation for plan adaptation"""
    def __init__(
        self,
        trigger: AdaptationTrigger,
        adaptation_type: AdaptationType,
        severity: float,  # 0-1, how urgent is this
        description: str,
        suggested_changes: Dict,
        reasoning: str
    ):
        self.trigger = trigger
        self.adaptation_type = adaptation_type
        self.severity = severity
        self.description = description
        self.suggested_changes = suggested_changes
        self.reasoning = reasoning


class PerformanceAnalysis:
    """Analysis of recent performance"""
    def __init__(
        self,
        completion_rate: float,  # 0-1
        average_difficulty_delta: float,  # -2 to +2 (easier to harder than expected)
        volume_compliance: float,  # 0-1.5+ (actual/planned volume)
        intensity_compliance: float,  # 0-1.5+ (actual/planned TSS)
        recovery_quality: float,  # 0-1 (from wellness data)
        acute_chronic_workload_ratio: float,  # Injury risk metric
        training_monotony: float,  # Variation in daily load
        training_strain: float,  # Cumulative stress
        trend: str  # "improving", "stable", "declining"
    ):
        self.completion_rate = completion_rate
        self.average_difficulty_delta = average_difficulty_delta
        self.volume_compliance = volume_compliance
        self.intensity_compliance = intensity_compliance
        self.recovery_quality = recovery_quality
        self.acute_chronic_workload_ratio = acute_chronic_workload_ratio
        self.training_monotony = training_monotony
        self.training_strain = training_strain
        self.trend = trend


class AdaptationEngine:
    """
    Intelligent plan adaptation engine

    Monitors training execution and adapts plans based on real-world feedback
    """

    # ACWR thresholds (Gabbett 2016)
    ACWR_SWEET_SPOT = (0.8, 1.3)  # Optimal range
    ACWR_CAUTION = (1.3, 1.5)     # Elevated injury risk
    ACWR_DANGER = 1.5              # High injury risk

    # Compliance thresholds
    MIN_COMPLETION_RATE = 0.7      # 70% completion expected
    GOOD_COMPLETION_RATE = 0.85    # 85%+ is good

    def __init__(self):
        """Initialize adaptation engine"""
        self.analysis_window_days = 14  # Analyze last 2 weeks
        self.acute_load_days = 7        # Acute load = last 7 days
        self.chronic_load_days = 28     # Chronic load = last 28 days

    def analyze_performance(
        self,
        plan: TrainingPlan,
        workout_logs: List[WorkoutLog],
        current_date: date
    ) -> PerformanceAnalysis:
        """
        Analyze recent performance

        Args:
            plan: Current training plan
            workout_logs: Completed workout logs
            current_date: Today's date

        Returns:
            PerformanceAnalysis with key metrics
        """
        # Filter to analysis window
        cutoff_date = current_date - timedelta(days=self.analysis_window_days)
        recent_logs = [
            log for log in workout_logs
            if log.completed_at and log.completed_at.date() >= cutoff_date
        ]

        if not recent_logs:
            # No recent data - return neutral analysis
            return self._neutral_analysis()

        # 1. Completion rate
        completion_rate = self._calculate_completion_rate(recent_logs)

        # 2. Difficulty perception
        avg_difficulty_delta = self._calculate_difficulty_delta(recent_logs)

        # 3. Volume and intensity compliance
        volume_compliance = self._calculate_volume_compliance(recent_logs, plan)
        intensity_compliance = self._calculate_intensity_compliance(recent_logs, plan)

        # 4. Recovery quality (from wellness data)
        recovery_quality = self._calculate_recovery_quality(recent_logs)

        # 5. Load monitoring
        acwr = self._calculate_acwr(workout_logs, current_date)
        monotony = self._calculate_training_monotony(recent_logs)
        strain = self._calculate_training_strain(recent_logs, monotony)

        # 6. Performance trend
        trend = self._determine_trend(recent_logs)

        return PerformanceAnalysis(
            completion_rate=completion_rate,
            average_difficulty_delta=avg_difficulty_delta,
            volume_compliance=volume_compliance,
            intensity_compliance=intensity_compliance,
            recovery_quality=recovery_quality,
            acute_chronic_workload_ratio=acwr,
            training_monotony=monotony,
            training_strain=strain,
            trend=trend
        )

    def recommend_adaptations(
        self,
        plan: TrainingPlan,
        performance: PerformanceAnalysis,
        assessment: Assessment,
        constraints: Constraints
    ) -> List[AdaptationRecommendation]:
        """
        Generate adaptation recommendations based on performance

        Args:
            plan: Current training plan
            performance: Performance analysis
            assessment: User assessment
            constraints: User constraints

        Returns:
            List of adaptation recommendations, sorted by severity
        """
        recommendations = []

        # Check 1: Injury risk (ACWR)
        if performance.acute_chronic_workload_ratio >= self.ACWR_DANGER:
            recommendations.append(AdaptationRecommendation(
                trigger=AdaptationTrigger.INJURY_RISK,
                adaptation_type=AdaptationType.MESO,
                severity=0.9,
                description="High injury risk detected - immediate load reduction needed",
                suggested_changes={
                    "volume_multiplier": 0.7,
                    "intensity_reduction": True,
                    "extra_recovery_day": True
                },
                reasoning=f"ACWR is {performance.acute_chronic_workload_ratio:.2f}, "
                          f"well above safe threshold of {self.ACWR_DANGER}. "
                          f"Research shows this significantly increases injury risk."
            ))

        elif performance.acute_chronic_workload_ratio >= self.ACWR_CAUTION[0]:
            recommendations.append(AdaptationRecommendation(
                trigger=AdaptationTrigger.INJURY_RISK,
                adaptation_type=AdaptationType.MICRO,
                severity=0.6,
                description="Elevated injury risk - moderate load adjustment",
                suggested_changes={
                    "volume_multiplier": 0.85,
                    "next_hard_session_delay": 1  # Push hard session back 1 day
                },
                reasoning=f"ACWR is {performance.acute_chronic_workload_ratio:.2f}, "
                          f"in caution zone. Recommend slight load reduction."
            ))

        # Check 2: Poor recovery
        if performance.recovery_quality < 0.5:
            recommendations.append(AdaptationRecommendation(
                trigger=AdaptationTrigger.POOR_RECOVERY,
                adaptation_type=AdaptationType.MICRO,
                severity=0.7,
                description="Poor recovery detected - add rest day",
                suggested_changes={
                    "add_recovery_day": True,
                    "next_hard_session_to_moderate": True
                },
                reasoning=f"Recovery quality is {performance.recovery_quality:.1%}. "
                          f"User needs additional recovery before hard training."
            ))

        # Check 3: Consistent underperformance
        if (performance.completion_rate < self.MIN_COMPLETION_RATE and
            performance.average_difficulty_delta > 0.5 and
            performance.trend == "declining"):

            recommendations.append(AdaptationRecommendation(
                trigger=AdaptationTrigger.CONSISTENT_UNDERPERFORMANCE,
                adaptation_type=AdaptationType.MESO,
                severity=0.75,
                description="Consistent struggle with workouts - plan is too aggressive",
                suggested_changes={
                    "volume_multiplier": 0.8,
                    "intensity_multiplier": 0.9,
                    "regenerate_if_prolonged": True
                },
                reasoning=f"Completion rate is {performance.completion_rate:.1%}, "
                          f"workouts feel {performance.average_difficulty_delta:.1f} harder than expected, "
                          f"and trend is declining. Plan needs to be more realistic."
            ))

        # Check 4: Consistent overperformance (room to progress)
        if (performance.completion_rate > self.GOOD_COMPLETION_RATE and
            performance.average_difficulty_delta < -0.5 and
            performance.trend == "improving" and
            performance.acute_chronic_workload_ratio < self.ACWR_SWEET_SPOT[1]):

            recommendations.append(AdaptationRecommendation(
                trigger=AdaptationTrigger.CONSISTENT_OVERPERFORMANCE,
                adaptation_type=AdaptationType.MESO,
                severity=0.4,  # Lower severity - this is good news
                description="User is ready for more challenge",
                suggested_changes={
                    "volume_multiplier": 1.1,
                    "intensity_multiplier": 1.05,
                    "accelerate_progression": True
                },
                reasoning=f"Completion rate is {performance.completion_rate:.1%}, "
                          f"workouts feel easier than expected, trend is improving, "
                          f"and ACWR is safe. User has capacity for more."
            ))

        # Check 5: Missed sessions
        if performance.completion_rate < 0.5:
            recommendations.append(AdaptationRecommendation(
                trigger=AdaptationTrigger.MISSED_SESSIONS,
                adaptation_type=AdaptationType.MACRO,
                severity=0.85,
                description="Many missed sessions - may need plan regeneration",
                suggested_changes={
                    "evaluate_constraints": True,
                    "consider_regeneration": True,
                    "timeline_extension": True
                },
                reasoning=f"Only {performance.completion_rate:.1%} of sessions completed. "
                          f"May need to reassess available time and regenerate plan."
            ))

        # Sort by severity (highest first)
        recommendations.sort(key=lambda r: r.severity, reverse=True)

        return recommendations

    def apply_micro_adjustment(
        self,
        plan: TrainingPlan,
        recommendation: AdaptationRecommendation,
        current_date: date
    ) -> TrainingPlan:
        """
        Apply micro-adjustment (next 1-3 sessions)

        Args:
            plan: Current training plan
            recommendation: Adaptation recommendation
            current_date: Today's date

        Returns:
            Updated training plan
        """
        changes = recommendation.suggested_changes

        # Find next 3 incomplete sessions
        upcoming_sessions = self._get_upcoming_sessions(plan, current_date, count=3)

        for session in upcoming_sessions:
            # Volume adjustment
            if "volume_multiplier" in changes:
                multiplier = changes["volume_multiplier"]
                session.estimated_duration_minutes = int(
                    session.estimated_duration_minutes * multiplier
                )
                if session.estimated_tss:
                    session.estimated_tss *= multiplier

            # Convert hard to moderate
            if changes.get("next_hard_session_to_moderate") and session.category.value == "hard":
                from core.models.training_plan import SessionCategory
                session.category = SessionCategory.MODERATE
                session.coaching_notes += " [ADAPTED: Reduced to moderate due to recovery needs]"
                break  # Only convert the next hard session

            # Add recovery day
            if changes.get("add_recovery_day"):
                # Push this session back by 1 day
                session.date = session.date + timedelta(days=1)

        return plan

    def apply_meso_adjustment(
        self,
        plan: TrainingPlan,
        recommendation: AdaptationRecommendation,
        current_date: date
    ) -> TrainingPlan:
        """
        Apply meso-adjustment (current + next week)

        Args:
            plan: Current training plan
            recommendation: Adaptation recommendation
            current_date: Today's date

        Returns:
            Updated training plan
        """
        changes = recommendation.suggested_changes

        # Find current and next week's sessions
        upcoming_sessions = self._get_upcoming_sessions(plan, current_date, count=10)

        for session in upcoming_sessions:
            # Volume adjustment
            if "volume_multiplier" in changes:
                multiplier = changes["volume_multiplier"]
                session.estimated_duration_minutes = int(
                    session.estimated_duration_minutes * multiplier
                )
                if session.estimated_tss:
                    session.estimated_tss *= multiplier

            # Intensity adjustment
            if "intensity_multiplier" in changes:
                multiplier = changes["intensity_multiplier"]
                if session.estimated_tss:
                    session.estimated_tss *= multiplier

        # Add extra recovery day if needed
        if changes.get("extra_recovery_day"):
            # Find current microcycle and reduce session count
            current_week = self._get_current_microcycle(plan, current_date)
            if current_week and len(current_week.sessions) > 3:
                # Remove the least important session (first easy session)
                from core.models.training_plan import SessionCategory
                for session in current_week.sessions:
                    if session.category == SessionCategory.EASY and not session.completed:
                        current_week.sessions.remove(session)
                        break

        return plan

    def should_regenerate_plan(
        self,
        performance: PerformanceAnalysis,
        recommendations: List[AdaptationRecommendation],
        weeks_since_start: int
    ) -> Tuple[bool, str]:
        """
        Decide if plan should be fully regenerated

        Args:
            performance: Performance analysis
            recommendations: Current recommendations
            weeks_since_start: Weeks since plan started

        Returns:
            (should_regenerate, reason)
        """
        # Regenerate if high-severity recommendation with regeneration flag
        for rec in recommendations:
            if rec.severity > 0.8 and rec.suggested_changes.get("consider_regeneration"):
                return True, rec.description

        # Regenerate if consistently missing sessions for 3+ weeks
        if performance.completion_rate < 0.5 and weeks_since_start >= 3:
            return True, "Consistently missing sessions - plan may not fit lifestyle"

        # Regenerate if consistent underperformance for 4+ weeks
        if (performance.completion_rate < 0.7 and
            performance.average_difficulty_delta > 0.75 and
            weeks_since_start >= 4):
            return True, "Persistent struggle with plan difficulty - needs full reassessment"

        return False, ""

    # -------------------------------------------------------------------------
    # Internal calculation methods
    # -------------------------------------------------------------------------

    def _calculate_completion_rate(self, logs: List[WorkoutLog]) -> float:
        """Calculate percentage of workouts completed"""
        if not logs:
            return 0.0

        completed_count = sum(
            1 for log in logs
            if log.completion_quality in [CompletionQuality.FULL, CompletionQuality.PARTIAL]
        )

        return completed_count / len(logs)

    def _calculate_difficulty_delta(self, logs: List[WorkoutLog]) -> float:
        """
        Calculate average difficulty perception delta
        Returns: -2 (much easier) to +2 (much harder)
        """
        if not logs:
            return 0.0

        difficulty_map = {
            PerceivedDifficulty.EASIER: -1.0,
            PerceivedDifficulty.AS_EXPECTED: 0.0,
            PerceivedDifficulty.HARDER: 1.0
        }

        deltas = [
            difficulty_map.get(log.perceived_difficulty, 0.0)
            for log in logs
            if log.perceived_difficulty
        ]

        return sum(deltas) / len(deltas) if deltas else 0.0

    def _calculate_volume_compliance(
        self,
        logs: List[WorkoutLog],
        plan: TrainingPlan
    ) -> float:
        """Calculate actual/planned volume ratio"""
        if not logs:
            return 0.0

        total_planned_minutes = sum(
            self._get_planned_duration(log.session_id, plan) or 0
            for log in logs
        )

        total_actual_minutes = sum(
            log.duration_minutes or 0
            for log in logs
        )

        if total_planned_minutes == 0:
            return 0.0

        return total_actual_minutes / total_planned_minutes

    def _calculate_intensity_compliance(
        self,
        logs: List[WorkoutLog],
        plan: TrainingPlan
    ) -> float:
        """Calculate actual/planned TSS ratio"""
        if not logs:
            return 0.0

        total_planned_tss = sum(
            self._get_planned_tss(log.session_id, plan) or 0
            for log in logs
        )

        total_actual_tss = sum(
            log.training_load or 0
            for log in logs
        )

        if total_planned_tss == 0:
            return 0.0

        return total_actual_tss / total_planned_tss

    def _calculate_recovery_quality(self, logs: List[WorkoutLog]) -> float:
        """Calculate recovery quality from wellness data (0-1)"""
        if not logs:
            return 0.75  # Neutral default

        # Average wellness scores from logs
        wellness_scores = []
        for log in logs:
            if log.wellness:
                # Normalize each factor to 0-1
                sleep = log.wellness.sleep_quality / 5.0
                stress = (5.0 - log.wellness.stress) / 5.0  # Invert
                soreness = (5.0 - log.wellness.soreness) / 5.0  # Invert

                wellness_scores.append((sleep + stress + soreness) / 3.0)

        return sum(wellness_scores) / len(wellness_scores) if wellness_scores else 0.75

    def _calculate_acwr(
        self,
        logs: List[WorkoutLog],
        current_date: date
    ) -> float:
        """
        Calculate Acute:Chronic Workload Ratio (Gabbett 2016)

        ACWR = (Acute load - last 7 days) / (Chronic load - last 28 days)
        """
        # Get acute load (last 7 days)
        acute_cutoff = current_date - timedelta(days=self.acute_load_days)
        acute_logs = [
            log for log in logs
            if log.completed_at and log.completed_at.date() >= acute_cutoff
        ]
        acute_load = sum(log.training_load or 0 for log in acute_logs)

        # Get chronic load (last 28 days)
        chronic_cutoff = current_date - timedelta(days=self.chronic_load_days)
        chronic_logs = [
            log for log in logs
            if log.completed_at and log.completed_at.date() >= chronic_cutoff
        ]
        chronic_load = sum(log.training_load or 0 for log in chronic_logs) / 4.0  # Average per week

        if chronic_load == 0:
            return 1.0  # Neutral if no chronic load

        return acute_load / chronic_load

    def _calculate_training_monotony(self, logs: List[WorkoutLog]) -> float:
        """
        Calculate training monotony (Foster 1998)

        Monotony = mean daily load / std dev of daily load
        Higher = less variation (worse)
        """
        if len(logs) < 2:
            return 1.0

        daily_loads = [log.training_load or 0 for log in logs]
        mean_load = sum(daily_loads) / len(daily_loads)

        # Calculate standard deviation
        variance = sum((load - mean_load) ** 2 for load in daily_loads) / len(daily_loads)
        std_dev = variance ** 0.5

        if std_dev == 0:
            return 5.0  # Maximum monotony

        return mean_load / std_dev

    def _calculate_training_strain(self, logs: List[WorkoutLog], monotony: float) -> float:
        """
        Calculate training strain (Foster 1998)

        Strain = total load * monotony
        """
        total_load = sum(log.training_load or 0 for log in logs)
        return total_load * monotony

    def _determine_trend(self, logs: List[WorkoutLog]) -> str:
        """Determine performance trend from recent logs"""
        if len(logs) < 4:
            return "stable"

        # Split into first half and second half
        mid = len(logs) // 2
        first_half = logs[:mid]
        second_half = logs[mid:]

        # Compare completion quality
        first_half_quality = self._calculate_completion_rate(first_half)
        second_half_quality = self._calculate_completion_rate(second_half)

        if second_half_quality > first_half_quality + 0.1:
            return "improving"
        elif second_half_quality < first_half_quality - 0.1:
            return "declining"
        else:
            return "stable"

    def _neutral_analysis(self) -> PerformanceAnalysis:
        """Return neutral analysis when no data available"""
        return PerformanceAnalysis(
            completion_rate=1.0,
            average_difficulty_delta=0.0,
            volume_compliance=1.0,
            intensity_compliance=1.0,
            recovery_quality=0.75,
            acute_chronic_workload_ratio=1.0,
            training_monotony=1.5,
            training_strain=0.0,
            trend="stable"
        )

    def _get_planned_duration(self, session_id: str, plan: TrainingPlan) -> Optional[int]:
        """Get planned duration for a session"""
        for microcycle in plan.microcycles:
            for session in microcycle.sessions:
                if session.session_id == session_id:
                    return session.estimated_duration_minutes
        return None

    def _get_planned_tss(self, session_id: str, plan: TrainingPlan) -> Optional[float]:
        """Get planned TSS for a session"""
        for microcycle in plan.microcycles:
            for session in microcycle.sessions:
                if session.session_id == session_id:
                    return session.estimated_tss
        return None

    def _get_upcoming_sessions(
        self,
        plan: TrainingPlan,
        current_date: date,
        count: int
    ) -> List[Session]:
        """Get next N upcoming sessions"""
        upcoming = []

        for microcycle in plan.microcycles:
            for session in microcycle.sessions:
                if session.date >= current_date and not session.completed:
                    upcoming.append(session)
                    if len(upcoming) >= count:
                        return upcoming

        return upcoming

    def _get_current_microcycle(
        self,
        plan: TrainingPlan,
        current_date: date
    ) -> Optional[Microcycle]:
        """Get the microcycle containing current date"""
        for microcycle in plan.microcycles:
            if microcycle.start_date <= current_date < microcycle.start_date + timedelta(days=7):
                return microcycle
        return None


# Convenience function
def analyze_and_adapt(
    plan: TrainingPlan,
    workout_logs: List[WorkoutLog],
    assessment: Assessment,
    constraints: Constraints,
    current_date: date
) -> Tuple[TrainingPlan, List[AdaptationRecommendation]]:
    """
    Analyze performance and apply adaptations to plan

    Args:
        plan: Current training plan
        workout_logs: Completed workout logs
        assessment: User assessment
        constraints: User constraints
        current_date: Today's date

    Returns:
        (adapted_plan, recommendations)
    """
    engine = AdaptationEngine()

    # Analyze performance
    performance = engine.analyze_performance(plan, workout_logs, current_date)

    # Get recommendations
    recommendations = engine.recommend_adaptations(plan, performance, assessment, constraints)

    # Apply highest priority recommendation if exists
    if recommendations:
        top_rec = recommendations[0]

        if top_rec.adaptation_type == AdaptationType.MICRO:
            plan = engine.apply_micro_adjustment(plan, top_rec, current_date)
        elif top_rec.adaptation_type == AdaptationType.MESO:
            plan = engine.apply_meso_adjustment(plan, top_rec, current_date)
        elif top_rec.adaptation_type == AdaptationType.MACRO:
            # Macro adjustments would require more complex logic
            # For now, apply meso adjustment
            plan = engine.apply_meso_adjustment(plan, top_rec, current_date)

    return plan, recommendations
