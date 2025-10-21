"""
Tests for Methodology Selector

Run with: pytest tests/test_methodology_selector.py -v
"""
import pytest
from datetime import datetime, timedelta

from core.algorithms.methodology_selector import MethodologySelector, select_optimal_methodology
from core.models.goal import Goal, GoalType, EnduranceGoal, HybridGoal, StrengthGoal, ExerciseTarget
from core.models.assessment import (
    Assessment, BodyComposition, EnduranceMetrics, StrengthMetrics,
    TrainingHistory, Health, Lifestyle, Injury
)
from core.models.constraint import (
    Constraints, TimeConstraints, SessionRange, ResourceConstraints,
    PersonalConstraints
)


class TestMethodologySelector:
    """Test methodology selection logic"""

    def test_endurance_goal_intermediate_athlete(self):
        """Test methodology selection for intermediate endurance athlete"""
        # Intermediate runner training for half marathon
        goal = Goal(
            goal_id="g1",
            user_id="u1",
            type=GoalType.ENDURANCE,
            target_date=datetime.now() + timedelta(weeks=20),
            endurance_goal=EnduranceGoal(
                event="half_marathon",
                target_time_seconds=5400  # 1:30:00
            )
        )

        assessment = Assessment(
            user_id="u1",
            assessment_id="a1",
            body_composition=BodyComposition(weight=170),
            endurance_metrics=EnduranceMetrics(vo2max=45),
            training_history=TrainingHistory(
                years_of_training=2,
                detraining_period_months=0
            ),
            health=Health(),
            lifestyle=Lifestyle()
        )
        assessment.fitness_score = 60.0

        constraints = Constraints(
            user_id="u1",
            constraint_id="c1",
            time=TimeConstraints(
                sessions_per_week=SessionRange(min=4, max=6, target=5),
                session_duration_minutes=SessionRange(min=30, max=60, target=45),
                total_weekly_hours=5.0
            )
        )

        selector = MethodologySelector()
        methodology = selector.select([goal], assessment, constraints)

        # Should select polarized training for intermediate endurance athlete
        assert methodology.name == "polarized_training"
        assert methodology.periodization_model.value == "block"

    def test_time_constrained_athlete(self):
        """Test methodology selection for time-constrained athlete"""
        goal = Goal(
            goal_id="g2",
            user_id="u2",
            type=GoalType.ENDURANCE,
            target_date=datetime.now() + timedelta(weeks=12),
            endurance_goal=EnduranceGoal(
                event="5k",
                target_time_seconds=1200  # 20:00
            )
        )

        assessment = Assessment(
            user_id="u2",
            assessment_id="a2",
            body_composition=BodyComposition(weight=160),
            training_history=TrainingHistory(years_of_training=1),
            health=Health(),
            lifestyle=Lifestyle()
        )
        assessment.fitness_score = 50.0

        # Very limited time
        constraints = Constraints(
            user_id="u2",
            constraint_id="c2",
            time=TimeConstraints(
                sessions_per_week=SessionRange(min=3, max=4, target=3),
                session_duration_minutes=SessionRange(min=20, max=30, target=25),
                total_weekly_hours=2.5  # Only 2.5 hours per week
            )
        )

        selector = MethodologySelector()
        methodology = selector.select([goal], assessment, constraints)

        # Should select time-efficient HIIT for time-constrained athlete
        assert methodology.name == "time_efficient_hiit"

    def test_beginner_with_injury_history(self):
        """Test conservative methodology for beginner with injuries"""
        goal = Goal(
            goal_id="g3",
            user_id="u3",
            type=GoalType.ENDURANCE,
            target_date=datetime.now() + timedelta(weeks=16),
            endurance_goal=EnduranceGoal(
                event="10k",
                target_time_seconds=3000  # 50:00
            )
        )

        # Beginner with recent injury
        assessment = Assessment(
            user_id="u3",
            assessment_id="a3",
            body_composition=BodyComposition(weight=180),
            training_history=TrainingHistory(
                years_of_training=0.5,
                detraining_period_months=2
            ),
            health=Health(
                injuries=[
                    Injury(
                        type="overuse",
                        location="knee",
                        status="resolved",
                        description="Runner's knee 3 months ago"
                    )
                ]
            ),
            lifestyle=Lifestyle()
        )
        assessment.fitness_score = 30.0

        constraints = Constraints(
            user_id="u3",
            constraint_id="c3",
            time=TimeConstraints(
                sessions_per_week=SessionRange(min=3, max=4, target=4),
                session_duration_minutes=SessionRange(min=30, max=45, target=40),
                total_weekly_hours=3.5
            )
        )

        selector = MethodologySelector()
        methodology = selector.select([goal], assessment, constraints)

        # Should select MAF or polarized (conservative approaches)
        assert methodology.name in ["maf_method", "polarized_training"]

    def test_hybrid_athlete(self):
        """Test methodology for hybrid strength + endurance athlete"""
        goal = Goal(
            goal_id="g4",
            user_id="u4",
            type=GoalType.HYBRID,
            target_date=datetime.now() + timedelta(weeks=24),
            hybrid_goal=HybridGoal(
                endurance_component=EnduranceGoal(
                    event="10k",
                    target_time_seconds=2400  # 40:00
                ),
                strength_component=StrengthGoal(
                    exercises=[
                        ExerciseTarget(name="Squat", target_weight=315, target_reps=1),
                        ExerciseTarget(name="Deadlift", target_weight=405, target_reps=1)
                    ]
                ),
                priority_weight=0.5  # Equal priority
            )
        )

        assessment = Assessment(
            user_id="u4",
            assessment_id="a4",
            body_composition=BodyComposition(weight=185),
            training_history=TrainingHistory(years_of_training=3),
            health=Health(),
            lifestyle=Lifestyle()
        )
        assessment.fitness_score = 65.0

        constraints = Constraints(
            user_id="u4",
            constraint_id="c4",
            time=TimeConstraints(
                sessions_per_week=SessionRange(min=5, max=6, target=6),
                session_duration_minutes=SessionRange(min=45, max=75, target=60),
                total_weekly_hours=6.0
            )
        )

        selector = MethodologySelector()
        methodology = selector.select([goal], assessment, constraints)

        # Should select hybrid concurrent training
        assert methodology.name == "hybrid_concurrent"
        assert methodology.periodization_model.value == "conjugate"

    def test_advanced_endurance_athlete(self):
        """Test methodology for advanced athlete with high volume"""
        goal = Goal(
            goal_id="g5",
            user_id="u5",
            type=GoalType.ENDURANCE,
            target_date=datetime.now() + timedelta(weeks=26),
            endurance_goal=EnduranceGoal(
                event="marathon",
                target_time_seconds=10800  # 3:00:00 (Boston qualifier)
            )
        )

        assessment = Assessment(
            user_id="u5",
            assessment_id="a5",
            body_composition=BodyComposition(weight=155),
            endurance_metrics=EnduranceMetrics(vo2max=55),
            training_history=TrainingHistory(years_of_training=5),
            health=Health(),
            lifestyle=Lifestyle()
        )
        assessment.fitness_score = 75.0

        constraints = Constraints(
            user_id="u5",
            constraint_id="c5",
            time=TimeConstraints(
                sessions_per_week=SessionRange(min=6, max=7, target=7),
                session_duration_minutes=SessionRange(min=45, max=120, target=75),
                total_weekly_hours=8.0  # High volume
            )
        )

        selector = MethodologySelector()
        methodology = selector.select([goal], assessment, constraints)

        # Should select Norwegian method for advanced athlete with high volume
        assert methodology.name in ["norwegian_method", "polarized_training"]

    def test_user_preference_override(self):
        """Test that valid user preference is honored"""
        goal = Goal(
            goal_id="g6",
            user_id="u6",
            type=GoalType.ENDURANCE,
            target_date=datetime.now() + timedelta(weeks=16),
            endurance_goal=EnduranceGoal(
                event="10k",
                target_time_seconds=2700
            )
        )

        assessment = Assessment(
            user_id="u6",
            assessment_id="a6",
            body_composition=BodyComposition(weight=165),
            training_history=TrainingHistory(years_of_training=2),
            health=Health(),
            lifestyle=Lifestyle()
        )
        assessment.fitness_score = 55.0

        constraints = Constraints(
            user_id="u6",
            constraint_id="c6",
            time=TimeConstraints(
                sessions_per_week=SessionRange(min=4, max=5, target=4),
                session_duration_minutes=SessionRange(min=30, max=60, target=45),
                total_weekly_hours=4.0
            )
        )

        selector = MethodologySelector()

        # User wants MAF method specifically
        methodology = selector.select([goal], assessment, constraints, user_preference="maf_method")

        assert methodology.name == "maf_method"

    def test_methodology_scoring(self):
        """Test that scoring function returns reasonable scores"""
        goal = Goal(
            goal_id="g7",
            user_id="u7",
            type=GoalType.ENDURANCE,
            target_date=datetime.now() + timedelta(weeks=16),
            endurance_goal=EnduranceGoal(
                event="half_marathon",
                target_time_seconds=5400
            )
        )

        assessment = Assessment(
            user_id="u7",
            assessment_id="a7",
            body_composition=BodyComposition(weight=170),
            training_history=TrainingHistory(years_of_training=2),
            health=Health(),
            lifestyle=Lifestyle()
        )
        assessment.fitness_score = 60.0

        constraints = Constraints(
            user_id="u7",
            constraint_id="c7",
            time=TimeConstraints(
                sessions_per_week=SessionRange(min=4, max=6, target=5),
                session_duration_minutes=SessionRange(min=30, max=60, target=45),
                total_weekly_hours=5.0
            )
        )

        selector = MethodologySelector()
        scores = selector._score_all_methodologies([goal], assessment, constraints)

        # Check that all methodologies get scores
        assert len(scores) == 6  # We have 6 methodologies defined

        # Check that scores are in valid range
        for method, score in scores.items():
            assert 0.0 <= score <= 1.0, f"{method} score {score} out of range"

        # Polarized should score highly for this profile
        assert scores["polarized_training"] >= 0.7

    def test_current_injury_blocks_hiit(self):
        """Test that current injury prevents HIIT selection"""
        goal = Goal(
            goal_id="g8",
            user_id="u8",
            type=GoalType.ENDURANCE,
            target_date=datetime.now() + timedelta(weeks=12),
            endurance_goal=EnduranceGoal(
                event="5k",
                target_time_seconds=1500
            )
        )

        assessment = Assessment(
            user_id="u8",
            assessment_id="a8",
            body_composition=BodyComposition(weight=160),
            training_history=TrainingHistory(years_of_training=1),
            health=Health(
                injuries=[
                    Injury(
                        type="strain",
                        location="hamstring",
                        status="current",  # Currently injured
                        description="Hamstring strain"
                    )
                ]
            ),
            lifestyle=Lifestyle()
        )
        assessment.fitness_score = 45.0

        constraints = Constraints(
            user_id="u8",
            constraint_id="c8",
            time=TimeConstraints(
                sessions_per_week=SessionRange(min=3, max=4, target=3),
                session_duration_minutes=SessionRange(min=20, max=30, target=25),
                total_weekly_hours=2.0
            )
        )

        selector = MethodologySelector()

        # Even with limited time, should NOT select HIIT due to injury
        methodology = selector.select([goal], assessment, constraints)

        # Should select conservative approach
        assert methodology.name in ["maf_method", "polarized_training"]

    def test_methodology_explanation(self):
        """Test that methodology explanation is generated"""
        goal = Goal(
            goal_id="g9",
            user_id="u9",
            type=GoalType.ENDURANCE,
            target_date=datetime.now() + timedelta(weeks=20),
            endurance_goal=EnduranceGoal(
                event="half_marathon",
                target_time_seconds=5400
            )
        )

        assessment = Assessment(
            user_id="u9",
            assessment_id="a9",
            body_composition=BodyComposition(weight=170),
            training_history=TrainingHistory(years_of_training=2),
            health=Health(),
            lifestyle=Lifestyle()
        )
        assessment.fitness_score = 60.0

        constraints = Constraints(
            user_id="u9",
            constraint_id="c9",
            time=TimeConstraints(
                sessions_per_week=SessionRange(min=4, max=6, target=5),
                session_duration_minutes=SessionRange(min=30, max=60, target=45),
                total_weekly_hours=5.0
            )
        )

        selector = MethodologySelector()
        methodology = selector.select([goal], assessment, constraints)

        explanation = selector.get_methodology_explanation(methodology)

        # Check that explanation contains key information
        assert "Methodology" in explanation
        assert "Intensity Distribution" in explanation
        assert "Why This Works" in explanation
        assert "Weekly Commitment" in explanation
        assert len(explanation) > 100  # Should be substantial


# Integration test
def test_full_methodology_selection_flow():
    """End-to-end test of methodology selection"""
    # Realistic scenario: comeback athlete training for marathon
    goal = Goal(
        goal_id="marathon_goal",
        user_id="sarah",
        type=GoalType.ENDURANCE,
        target_date=datetime.now() + timedelta(weeks=78),  # 18 months
        endurance_goal=EnduranceGoal(
            event="marathon",
            target_time_seconds=12600  # 3:30:00 (BQ for 34F)
        )
    )

    assessment = Assessment(
        user_id="sarah",
        assessment_id="sarah_assessment",
        body_composition=BodyComposition(weight=145, height=66),
        endurance_metrics=EnduranceMetrics(vo2max=38),  # Detrained
        training_history=TrainingHistory(
            years_of_training=4,  # Trained in college
            detraining_period_months=36  # 3 years off
        ),
        health=Health(
            injuries=[
                Injury(
                    type="stress_fracture",
                    location="metatarsal",
                    status="resolved",
                    description="Stress fracture in college, 8 years ago"
                )
            ]
        ),
        lifestyle=Lifestyle(
            sleep_hours=6.5,
            stress_level=4  # High stress (2 kids)
        )
    )
    assessment.fitness_score = 40.0  # Currently detrained

    constraints = Constraints(
        user_id="sarah",
        constraint_id="sarah_constraints",
        time=TimeConstraints(
            sessions_per_week=SessionRange(min=4, max=6, target=5),
            session_duration_minutes=SessionRange(min=30, max=60, target=45),
            total_weekly_hours=5.0
        )
    )

    # Select methodology
    methodology = select_optimal_methodology([goal], assessment, constraints)

    # For this profile, should select polarized or MAF (conservative for comeback)
    assert methodology.name in ["polarized_training", "maf_method"]

    # Verify intensity distribution makes sense
    dist = methodology.intensity_distribution
    easy_percentage = dist.zone_1_percentage + dist.zone_2_percentage
    hard_percentage = dist.zone_4_percentage + dist.zone_5_percentage

    # Should be mostly easy work
    assert easy_percentage >= 70.0

    print(f"\n✓ Selected methodology: {methodology.name}")
    print(f"✓ Easy/Aerobic work: {easy_percentage:.0f}%")
    print(f"✓ Threshold/VO2max work: {hard_percentage:.0f}%")


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])
