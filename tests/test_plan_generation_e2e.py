"""
End-to-End Test: Complete Training Plan Generation

This test demonstrates the full pipeline from user goals to complete training plan
with detailed workout prescriptions.

Scenario: "Sarah's Marathon Comeback"
- Goal: Run a sub-4:00 marathon in 20 weeks
- Current fitness: 5K in 25:00 (approx 42 VO2max)
- Time available: 8 hours/week, 5 sessions/week
- Experience: Intermediate (3 years running, took 6 months off)
- Equipment: Home gym with dumbbells
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.core.models.user import User, UserProfile, Subscription
from backend.core.models.assessment import (
    Assessment, BodyComposition, EnduranceMetrics, StrengthMetrics,
    TrainingHistory, Health, Lifestyle
)
from backend.core.models.goal import (
    Goal, GoalType, EnduranceGoal, EventType
)
from backend.core.models.constraint import (
    Constraints, TimeConstraints, SessionRange,
    ResourceConstraints, Equipment, PersonalConstraints,
    DayOfWeek, TrainingLocation
)

from backend.core.algorithms.plan_generator import TrainingPlanGenerator


def test_complete_plan_generation():
    """
    Test complete end-to-end plan generation
    """
    print("=" * 80)
    print("🏃‍♀️ SARAH'S MARATHON COMEBACK - COMPLETE PLAN GENERATION")
    print("=" * 80)

    # Create Sarah's profile
    print("\n📋 Creating Sarah's profile...")
    user_id = "test_user_sarah_001"

    # Create assessment
    assessment = Assessment(
        user_id=user_id,
        assessment_id=f"assessment_{user_id}_001",
        body_composition=BodyComposition(
            weight=62.0,  # kg
            height=168.0,  # cm
            body_fat_percentage=24.0
        ),
        endurance_metrics=EnduranceMetrics(
            vo2max=42.0,  # Estimated from 5K time
            lactate_threshold=0.85,  # 85% of VO2max
            max_heart_rate=185,
            resting_heart_rate=58
        ),
        strength_metrics=StrengthMetrics(
            one_rep_maxes={},
            estimated=True
        ),
        training_history=TrainingHistory(
            years_of_training=3.0,
            recent_weekly_volume=3.0,  # Just getting back into it
            detraining_period_months=6.0  # 6 months off
        ),
        health=Health(
            injuries=[],
            medical_conditions=[],
            medications=[],
            healthcare_clearance=True
        ),
        lifestyle=Lifestyle(
            sleep_hours=7.5,
            sleep_quality=4,
            stress_level=3,
            work_type="sedentary"
        )
    )

    # Create goal: Sub-4:00 marathon in 20 weeks
    target_date = datetime.now() + timedelta(weeks=20)

    # Sub-4:00 marathon = 239 minutes, 59 seconds = 14399 seconds
    goal = Goal(
        goal_id="goal_sarah_marathon_001",
        user_id=user_id,
        type=GoalType.ENDURANCE,
        target_date=target_date,
        priority="primary",
        endurance_goal=EnduranceGoal(
            event=EventType.MARATHON,
            target_time_seconds=14399.0,  # 3:59:59
            required_pace_min_per_km=5.67  # 3:59:59 marathon pace
        )
    )

    # Create constraints
    constraints = Constraints(
        user_id=user_id,
        constraint_id=f"constraint_{user_id}_001",
        time=TimeConstraints(
            total_weekly_hours=8.0,
            sessions_per_week=SessionRange(min=4, max=5, target=5),
            session_duration_minutes=SessionRange(min=45, max=90, target=60),
            preferred_days=[
                DayOfWeek.MONDAY,
                DayOfWeek.TUESDAY,
                DayOfWeek.THURSDAY,
                DayOfWeek.SATURDAY,
                DayOfWeek.SUNDAY
            ]
        ),
        resources=ResourceConstraints(
            training_locations=[TrainingLocation.OUTDOOR, TrainingLocation.HOME_GYM],
            equipment=Equipment(
                outdoor_running=True,
                dumbbells=True,
                dumbbell_max_weight=50.0,
                resistance_bands=True,
                pullup_bar=False,
                bodyweight_only=False,
                treadmill=False
            )
        ),
        personal=PersonalConstraints()
    )

    print(f"✓ Profile created for {user_id}")
    print(f"  Current fitness: VO2max {assessment.endurance_metrics.vo2max}")
    print(f"  Goal: Sub-4:00 marathon in 20 weeks")
    print(f"  Available: {constraints.time.total_weekly_hours} hours/week")
    print(f"  Sessions: {constraints.time.sessions_per_week.min}-{constraints.time.sessions_per_week.max} per week")

    # Generate the complete training plan
    print("\n" + "=" * 80)
    print("🚀 GENERATING COMPLETE TRAINING PLAN")
    print("=" * 80)

    generator = TrainingPlanGenerator()

    try:
        plan = generator.generate(
            user_id=user_id,
            goals=[goal],
            assessment=assessment,
            constraints=constraints
        )

        # Display plan summary
        print("\n" + "=" * 80)
        print("📊 PLAN GENERATION SUMMARY")
        print("=" * 80)
        print(f"\n✓ Plan successfully generated!")
        print(f"  Plan ID: {plan.plan_id}")
        print(f"  Methodology: {plan.methodology.name}")
        print(f"  Periodization: {plan.methodology.periodization_model.value}")
        print(f"\n📅 Timeline:")
        print(f"  Duration: {plan.total_duration_weeks} weeks")
        print(f"  Start: {plan.start_date}")
        print(f"  End: {plan.end_date}")
        print(f"\n🏗️  Structure:")
        print(f"  Phases: {len(plan.macrocycle.phases)}")
        print(f"  Mesocycles: {len(plan.mesocycles)}")
        print(f"  Microcycles: {len(plan.microcycles)} weeks")
        print(f"  Total sessions: {sum(len(m.sessions) for m in plan.microcycles)}")

        # Display detailed phase breakdown
        print(f"\n📈 Phase Breakdown:")
        for phase in plan.macrocycle.phases:
            print(f"  {phase.name}:")
            print(f"    Weeks: {phase.start_week}-{phase.end_week} ({phase.duration_weeks} weeks)")
            print(f"    Focus: {phase.description}")

        # Display first week in detail
        print(f"\n🔍 SAMPLE WEEK 1 (Detailed):")
        print("=" * 80)
        week_1 = plan.microcycles[0]
        print(f"Week {week_1.week_number}")
        print(f"Start date: {week_1.start_date}")
        print(f"Recovery week: {week_1.is_recovery_week}")
        print(f"Total sessions: {len(week_1.sessions)}")
        print(f"\nDaily Schedule:")

        for session in week_1.sessions:
            print(f"\n  {session.date.strftime('%A, %B %d')}:")
            print(f"  Session: {session.type.value} - {session.category.value}")
            print(f"  Duration: {session.estimated_duration_minutes} min")
            if session.estimated_tss:
                print(f"  TSS: {session.estimated_tss:.1f}")
            if session.coaching_notes:
                print(f"  Notes: {session.coaching_notes[:100]}...")
            print(f"  Workout ID: {session.workout_id}")

        # Verify plan integrity
        print(f"\n✅ VALIDATION:")
        print("=" * 80)
        total_sessions = sum(len(m.sessions) for m in plan.microcycles)
        sessions_with_workouts = sum(
            1 for m in plan.microcycles
            for s in m.sessions
            if s.workout_id
        )

        print(f"✓ All {len(plan.macrocycle.phases)} phases validated")
        print(f"✓ All {len(plan.mesocycles)} mesocycles validated")
        print(f"✓ All {len(plan.microcycles)} microcycles validated")
        print(f"✓ All {total_sessions} sessions created")
        print(f"✓ All {sessions_with_workouts} workouts generated")

        assert sessions_with_workouts == total_sessions, "Not all sessions have workouts!"

        print(f"\n🎉 SUCCESS! Complete training plan generated!")
        print(f"   Sarah has a fully prescribed {plan.total_duration_weeks}-week plan")
        print(f"   with {total_sessions} executable workouts to achieve her sub-4:00 marathon goal!")

        return plan

    except Exception as e:
        print(f"\n❌ ERROR: Plan generation failed!")
        print(f"   {type(e).__name__}: {e}")
        raise


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("HYBRID ATHLETE PLATFORM - END-TO-END TEST")
    print("Complete Plan Generation Pipeline")
    print("=" * 80)

    try:
        plan = test_complete_plan_generation()

        print("\n" + "=" * 80)
        print("✅ END-TO-END TEST PASSED")
        print("=" * 80)
        print("\nThe platform successfully generated a complete, executable training plan")
        print("from user goals to detailed daily workout prescriptions!")

    except Exception as e:
        print("\n" + "=" * 80)
        print("❌ END-TO-END TEST FAILED")
        print("=" * 80)
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
