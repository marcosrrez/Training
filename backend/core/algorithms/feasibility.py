"""
Goal Feasibility Analysis Engine

This module analyzes whether a user's goals are realistic given their:
- Current fitness level
- Training history
- Available time
- Timeline to goal

It provides evidence-based feedback and timeline recommendations.
"""
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import math

from core.models.goal import (
    Goal, GoalType, EnduranceGoal, StrengthGoal,
    FeasibilityAssessment, Adaptation, Risk
)
from core.models.assessment import Assessment
from core.models.constraint import Constraints


class FeasibilityAnalyzer:
    """
    Analyzes goal feasibility based on current state and constraints
    """

    def __init__(self):
        # Training adaptation rate constants (based on research)
        self.VO2MAX_IMPROVEMENT_RATE = 0.005  # ~0.5% per week with proper training
        self.STRENGTH_IMPROVEMENT_RATE = 0.01  # ~1% per week for beginners
        self.DETRAINING_DISCOUNT = 0.15  # 15% loss per month of detraining

    def analyze_goal(
        self,
        goal: Goal,
        assessment: Assessment,
        constraints: Constraints
    ) -> FeasibilityAssessment:
        """
        Main method to analyze goal feasibility
        """
        if goal.type == GoalType.ENDURANCE and goal.endurance_goal:
            return self._analyze_endurance_goal(goal, assessment, constraints)
        elif goal.type == GoalType.STRENGTH and goal.strength_goal:
            return self._analyze_strength_goal(goal, assessment, constraints)
        elif goal.type == GoalType.COMPOSITION and goal.composition_goal:
            return self._analyze_composition_goal(goal, assessment, constraints)
        elif goal.type == GoalType.HYBRID and goal.hybrid_goal:
            return self._analyze_hybrid_goal(goal, assessment, constraints)
        else:
            return self._default_assessment()

    def _analyze_endurance_goal(
        self,
        goal: Goal,
        assessment: Assessment,
        constraints: Constraints
    ) -> FeasibilityAssessment:
        """
        Analyze endurance performance goal feasibility
        """
        endurance_goal = goal.endurance_goal

        # Calculate required VO2max for target time
        required_vo2max = self._estimate_required_vo2max(
            event=endurance_goal.event,
            target_time_seconds=endurance_goal.target_time_seconds
        )

        # Estimate current VO2max from assessment
        current_vo2max = assessment.endurance_metrics.vo2max or self._estimate_vo2max_from_history(
            assessment
        )

        # Calculate required improvement
        required_improvement = required_vo2max - current_vo2max
        improvement_percentage = (required_improvement / current_vo2max) * 100

        # Account for detraining
        detraining_months = assessment.training_history.detraining_period_months
        detraining_factor = 1 - (self.DETRAINING_DISCOUNT * detraining_months)
        effective_current_vo2max = current_vo2max * detraining_factor

        # Calculate realistic timeline
        weeks_needed = self._calculate_weeks_needed_for_vo2max_improvement(
            current_vo2max=effective_current_vo2max,
            target_vo2max=required_vo2max,
            training_age=assessment.training_history.years_of_training,
            weekly_hours=constraints.time.total_weekly_hours or 5.0
        )

        # Calculate weeks until goal
        weeks_until_goal = (goal.target_date - datetime.now()).days / 7

        # Determine probability
        probability = self._calculate_probability(
            weeks_needed=weeks_needed,
            weeks_available=weeks_until_goal,
            training_age=assessment.training_history.years_of_training
        )

        # Build list of required adaptations
        adaptations = self._identify_required_adaptations(
            improvement_percentage=improvement_percentage,
            event=endurance_goal.event
        )

        # Identify risks
        risks = self._identify_risks(
            assessment=assessment,
            required_improvement=improvement_percentage,
            timeline_ratio=weeks_until_goal / weeks_needed if weeks_needed > 0 else 1.0
        )

        # Generate recommendation
        is_realistic = probability >= 0.6
        recommendation = self._generate_recommendation(
            is_realistic=is_realistic,
            weeks_needed=weeks_needed,
            weeks_available=weeks_until_goal,
            required_improvement=improvement_percentage
        )

        return FeasibilityAssessment(
            probability=probability,
            required_adaptations=adaptations,
            estimated_timeline_weeks=int(weeks_needed),
            realistic_timeline_weeks=int(weeks_needed * 1.2),  # Add 20% buffer
            risks=risks,
            is_realistic=is_realistic,
            recommendation=recommendation
        )

    def _estimate_required_vo2max(self, event: str, target_time_seconds: float) -> float:
        """
        Estimate required VO2max for a target race time

        Based on Jack Daniels' VDOT calculator and research correlations
        """
        # Convert to velocity (meters per second)
        event_distances = {
            "5k": 5000,
            "10k": 10000,
            "half_marathon": 21097,
            "marathon": 42195,
            "ultra": 50000  # 50K as baseline
        }

        distance_meters = event_distances.get(event, 10000)
        velocity = distance_meters / target_time_seconds

        # Empirical formula: VO2max ≈ velocity * efficiency_factor + baseline
        # This is a simplified version of more complex models
        if event == "5k":
            # 5K is ~95% VO2max effort
            vo2max = (velocity * 15.5) + 10
        elif event == "10k":
            # 10K is ~90% VO2max effort
            vo2max = (velocity * 16) + 12
        elif event == "half_marathon":
            # Half marathon is ~85% VO2max effort
            vo2max = (velocity * 16.5) + 14
        elif event == "marathon":
            # Marathon is ~80% VO2max effort
            vo2max = (velocity * 17) + 16
        else:
            # Ultra events at lower percentage
            vo2max = (velocity * 17.5) + 18

        return round(vo2max, 1)

    def _estimate_vo2max_from_history(self, assessment: Assessment) -> float:
        """
        Estimate current VO2max from training history and recent performances
        """
        # If we have recent race results, use those
        if assessment.endurance_metrics.recent_races:
            recent_race = assessment.endurance_metrics.recent_races[0]
            return self._estimate_required_vo2max(
                event=recent_race.event,
                target_time_seconds=recent_race.time_seconds
            )

        # Otherwise, estimate based on training status
        training_years = assessment.training_history.years_of_training

        # Age and gender adjustments
        age_factor = 1.0 - (max(0, assessment.lifestyle.sleep_hours - 30) * 0.005)

        # Base estimates by training status
        if training_years == 0:
            base_vo2max = 35  # Untrained
        elif training_years < 1:
            base_vo2max = 40  # Beginner
        elif training_years < 3:
            base_vo2max = 45  # Intermediate
        elif training_years < 5:
            base_vo2max = 50  # Advanced
        else:
            base_vo2max = 55  # Well-trained

        return base_vo2max * age_factor

    def _calculate_weeks_needed_for_vo2max_improvement(
        self,
        current_vo2max: float,
        target_vo2max: float,
        training_age: float,
        weekly_hours: float
    ) -> float:
        """
        Calculate weeks needed for VO2max improvement

        Based on research showing:
        - Beginners: 15-20% improvement in 12-16 weeks
        - Intermediate: 8-12% improvement in 12-16 weeks
        - Advanced: 4-8% improvement in 12-16 weeks
        """
        required_improvement = target_vo2max - current_vo2max
        improvement_percentage = (required_improvement / current_vo2max) * 100

        # Determine improvement rate based on training age
        if training_age < 1:
            # Beginners improve faster
            weekly_improvement_rate = 0.8  # 0.8% per week
        elif training_age < 3:
            # Intermediate
            weekly_improvement_rate = 0.5
        elif training_age < 5:
            # Advanced
            weekly_improvement_rate = 0.3
        else:
            # Elite - slower improvements
            weekly_improvement_rate = 0.15

        # Adjust for training volume
        volume_factor = min(1.0, weekly_hours / 6.0)  # Optimal around 6 hours/week
        adjusted_rate = weekly_improvement_rate * volume_factor

        # Calculate weeks
        if adjusted_rate > 0:
            weeks_needed = improvement_percentage / adjusted_rate
        else:
            weeks_needed = 999  # Unrealistic

        # Add base period for adaptation
        base_period = 8  # Minimum 8 weeks for any significant improvement

        return max(base_period, weeks_needed)

    def _calculate_probability(
        self,
        weeks_needed: float,
        weeks_available: float,
        training_age: float
    ) -> float:
        """
        Calculate probability of success (0-1)
        """
        if weeks_available <= 0:
            return 0.0

        ratio = weeks_available / weeks_needed if weeks_needed > 0 else 1.0

        # Base probability from timeline
        if ratio >= 1.5:
            base_prob = 0.9  # Plenty of time
        elif ratio >= 1.2:
            base_prob = 0.8  # Good timeline
        elif ratio >= 1.0:
            base_prob = 0.65  # Tight but possible
        elif ratio >= 0.8:
            base_prob = 0.4  # Aggressive
        else:
            base_prob = 0.2  # Very unlikely

        # Adjust for training age (experienced athletes adapt better)
        experience_bonus = min(0.1, training_age * 0.02)

        final_probability = min(0.95, base_prob + experience_bonus)

        return round(final_probability, 2)

    def _identify_required_adaptations(
        self,
        improvement_percentage: float,
        event: str
    ) -> List[Adaptation]:
        """
        Identify physiological adaptations required
        """
        adaptations = []

        if improvement_percentage > 5:
            adaptations.append(Adaptation(
                name="VO2max development",
                description="Increase maximal aerobic capacity through high-intensity intervals",
                typical_timeline_weeks=12,
                difficulty="moderate"
            ))

        if improvement_percentage > 10:
            adaptations.append(Adaptation(
                name="Lactate threshold improvement",
                description="Increase sustainable pace through tempo and threshold training",
                typical_timeline_weeks=16,
                difficulty="moderate"
            ))

        if event in ["half_marathon", "marathon", "ultra"]:
            adaptations.append(Adaptation(
                name="Aerobic base development",
                description="Build aerobic endurance through volume accumulation",
                typical_timeline_weeks=20,
                difficulty="hard"
            ))

        if improvement_percentage > 20:
            adaptations.append(Adaptation(
                name="Running economy enhancement",
                description="Improve efficiency through form work and strength training",
                typical_timeline_weeks=16,
                difficulty="moderate"
            ))

        return adaptations

    def _identify_risks(
        self,
        assessment: Assessment,
        required_improvement: float,
        timeline_ratio: float
    ) -> List[Risk]:
        """
        Identify risk factors
        """
        risks = []

        # Injury history risk
        if len(assessment.health.injuries) > 0:
            current_injuries = [i for i in assessment.health.injuries if i.status == "current"]
            if current_injuries:
                risks.append(Risk(
                    factor="Current injuries",
                    severity="high",
                    mitigation="Address injuries before beginning training; modify plan to avoid aggravation"
                ))

        # Aggressive timeline risk
        if timeline_ratio < 1.0:
            risks.append(Risk(
                factor="Aggressive timeline",
                severity="high" if timeline_ratio < 0.8 else "moderate",
                mitigation="Consider extending timeline; focus on injury prevention; include recovery weeks"
            ))

        # Large improvement required
        if required_improvement > 20:
            risks.append(Risk(
                factor="Large improvement required",
                severity="moderate",
                mitigation="Break into intermediate milestones; allow for setbacks; maintain consistency"
            ))

        # Detraining period
        if assessment.training_history.detraining_period_months > 3:
            risks.append(Risk(
                factor="Recent detraining",
                severity="moderate",
                mitigation="Start conservatively; focus on rebuilding base; avoid early intensity"
            ))

        return risks

    def _generate_recommendation(
        self,
        is_realistic: bool,
        weeks_needed: float,
        weeks_available: float,
        required_improvement: float
    ) -> str:
        """
        Generate human-readable recommendation
        """
        if is_realistic:
            return (
                f"Your goal is realistic with proper training. "
                f"You need approximately {int(weeks_needed)} weeks, and you have {int(weeks_available)} weeks available. "
                f"This requires a {required_improvement:.1f}% improvement, which is achievable with consistent training."
            )
        else:
            realistic_weeks = int(weeks_needed * 1.2)
            return (
                f"Your timeline is aggressive. "
                f"You have {int(weeks_available)} weeks, but we recommend {realistic_weeks} weeks for this goal. "
                f"Consider adjusting your timeline or setting an intermediate goal. "
                f"Required improvement: {required_improvement:.1f}%."
            )

    def _analyze_strength_goal(
        self,
        goal: Goal,
        assessment: Assessment,
        constraints: Constraints
    ) -> FeasibilityAssessment:
        """
        Analyze strength goal feasibility

        TODO: Implement detailed strength goal analysis
        """
        return FeasibilityAssessment(
            probability=0.7,
            required_adaptations=[],
            estimated_timeline_weeks=16,
            realistic_timeline_weeks=20,
            risks=[],
            is_realistic=True,
            recommendation="Strength goal analysis will be fully implemented in next phase."
        )

    def _analyze_composition_goal(
        self,
        goal: Goal,
        assessment: Assessment,
        constraints: Constraints
    ) -> FeasibilityAssessment:
        """
        Analyze body composition goal feasibility

        TODO: Implement detailed composition goal analysis
        """
        return FeasibilityAssessment(
            probability=0.75,
            required_adaptations=[],
            estimated_timeline_weeks=12,
            realistic_timeline_weeks=16,
            risks=[],
            is_realistic=True,
            recommendation="Body composition goal analysis will be fully implemented in next phase."
        )

    def _analyze_hybrid_goal(
        self,
        goal: Goal,
        assessment: Assessment,
        constraints: Constraints
    ) -> FeasibilityAssessment:
        """
        Analyze hybrid goal feasibility (concurrent training)

        TODO: Implement detailed hybrid goal analysis with interference assessment
        """
        return FeasibilityAssessment(
            probability=0.65,
            required_adaptations=[],
            estimated_timeline_weeks=20,
            realistic_timeline_weeks=24,
            risks=[],
            is_realistic=True,
            recommendation="Hybrid goal analysis will be fully implemented in next phase."
        )

    def _default_assessment(self) -> FeasibilityAssessment:
        """
        Default assessment for unknown goal types
        """
        return FeasibilityAssessment(
            probability=0.5,
            required_adaptations=[],
            estimated_timeline_weeks=16,
            realistic_timeline_weeks=20,
            risks=[],
            is_realistic=True,
            recommendation="Goal analysis pending."
        )


def analyze_goal_feasibility(
    goal: Goal,
    assessment: Assessment,
    constraints: Constraints
) -> FeasibilityAssessment:
    """
    Convenience function to analyze goal feasibility
    """
    analyzer = FeasibilityAnalyzer()
    return analyzer.analyze_goal(goal, assessment, constraints)
