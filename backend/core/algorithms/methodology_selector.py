"""
Training Methodology Selection

Selects the optimal training methodology based on:
- User goals
- Fitness level
- Time constraints
- User preferences

Methodologies:
- Polarized Training (80/20 rule)
- Norwegian Method (threshold-focused)
- MAF Method (aerobic-only)
- Time-Efficient HIIT
- Hybrid Concurrent
"""
from typing import List
from core.models.goal import Goal, GoalType
from core.models.assessment import Assessment
from core.models.constraint import Constraints
from core.models.training_plan import Methodology, IntensityDistribution, PeriodizationModel


class MethodologySelector:
    """
    Selects optimal training methodology
    """

    def select(
        self,
        goals: List[Goal],
        assessment: Assessment,
        constraints: Constraints,
        user_preference: str = "auto"
    ) -> Methodology:
        """
        Select best methodology for user context

        TODO: Implement methodology selection logic based on:
        - Goal types and priorities
        - Training age and fitness level
        - Available time (hours per week)
        - User explicit preference
        """
        # Placeholder: Default to polarized training
        return Methodology(
            name="polarized_training",
            description="80/20 training with polarized intensity distribution",
            periodization_model=PeriodizationModel.BLOCK,
            intensity_distribution=IntensityDistribution(
                zone_1_percentage=50.0,
                zone_2_percentage=30.0,
                zone_3_percentage=5.0,
                zone_4_percentage=10.0,
                zone_5_percentage=5.0
            )
        )


def select_optimal_methodology(
    goals: List[Goal],
    assessment: Assessment,
    constraints: Constraints,
    user_preference: str = "auto"
) -> Methodology:
    """
    Convenience function to select methodology
    """
    selector = MethodologySelector()
    return selector.select(goals, assessment, constraints, user_preference)
