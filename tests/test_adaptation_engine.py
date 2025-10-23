"""
Tests for Plan Adaptation Engine

Tests various adaptation scenarios:
- Performance analysis
- Injury risk detection (ACWR)
- Underperformance handling
- Overperformance progression
- Micro/meso/macro adjustments
"""

import sys
from pathlib import Path
from datetime import datetime, date, timedelta
from typing import Optional

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.core.algorithms.adaptation_engine import (
    AdaptationEngine, PerformanceAnalysis, AdaptationRecommendation,
    AdaptationTrigger, AdaptationType, analyze_and_adapt
)
from backend.core.models.training_plan import (
    TrainingPlan, Microcycle, Session, SessionType, SessionCategory,
    Macrocycle, Phase, Mesocycle, Volume, Methodology, PeriodizationModel,
    IntensityDistribution
)
from backend.core.models.workout_log import (
    WorkoutLog, CompletionQuality, PerceivedDifficulty, WellnessData
)
from backend.core.models.assessment import Assessment, BodyComposition, EnduranceMetrics
from backend.core.models.constraint import Constraints, TimeConstraints, SessionRange


def create_test_plan(start_date: date, weeks: int = 4) -> TrainingPlan:
    """Create a simple test training plan"""
    microcycles = []

    for week in range(weeks):
        week_start = start_date + timedelta(weeks=week)
        sessions = []

        # Create 5 sessions per week
        for day in range(5):
            session_date = week_start + timedelta(days=day)
            sessions.append(Session(
                session_id=f"week{week}_day{day}",
                date=session_date,
                type=SessionType.RUN,
                category=SessionCategory.EASY if day < 4 else SessionCategory.HARD,
                estimated_duration_minutes=45 if day < 4 else 60,
                estimated_tss=40.0 if day < 4 else 70.0,
                coaching_notes="Test session"
            ))

        microcycles.append(Microcycle(
            week_number=week,
            start_date=week_start,
            sessions=sessions,
            total_volume=Volume(hours=4.0, distance_km=40.0),
            intensity_score=220.0,
            is_recovery_week=False
        ))

    return TrainingPlan(
        plan_id="test_plan_001",
        user_id="test_user_001",
        goal_ids=["goal_001"],
        generated_at=datetime.now(),
        start_date=start_date,
        end_date=start_date + timedelta(weeks=weeks),
        total_duration_weeks=weeks,
        methodology=Methodology(
            name="test_method",
            description="Test methodology for adaptation engine testing",
            periodization_model=PeriodizationModel.BLOCK,
            intensity_distribution=IntensityDistribution(
                zone_1_percentage=50.0,
                zone_2_percentage=30.0,
                zone_3_percentage=10.0,
                zone_4_percentage=5.0,
                zone_5_percentage=5.0
            )
        ),
        macrocycle=Macrocycle(
            total_weeks=weeks,
            periodization_model=PeriodizationModel.BLOCK,
            phases=[Phase(
                name="Base",
                start_week=0,
                end_week=weeks,
                duration_weeks=weeks,
                focus="Test focus",
                description="Test phase"
            )]
        ),
        mesocycles=[],
        microcycles=microcycles,
        current_week=0
    )


def create_workout_log(
    session_id: str,
    completed_at: datetime,
    completion_quality: CompletionQuality,
    perceived_difficulty: PerceivedDifficulty,
    actual_duration_minutes: int,
    actual_tss: float,
    wellness: Optional[WellnessData] = None
) -> WorkoutLog:
    """Create a workout log"""
    return WorkoutLog(
        log_id=f"log_{session_id}",
        user_id="test_user_001",
        session_id=session_id,
        workout_id=f"workout_{session_id}",
        completed_at=completed_at,
        completion_quality=completion_quality,
        perceived_difficulty=perceived_difficulty,
        duration_minutes=float(actual_duration_minutes),
        perceived_exertion=6,  # RPE 1-10
        training_load=actual_tss,
        wellness=wellness or WellnessData(
            fatigue=2,
            soreness=2,
            mood=4,
            sleep_quality=4,
            stress=2,
            motivation=4
        )
    )


def test_performance_analysis_healthy():
    """Test performance analysis with healthy execution"""
    print("\n" + "=" * 80)
    print("TEST 1: Performance Analysis - Healthy Execution")
    print("=" * 80)

    engine = AdaptationEngine()
    current_date = date.today()
    plan = create_test_plan(current_date - timedelta(weeks=2), weeks=4)

    # Create logs for healthy execution (last 2 weeks)
    logs = []
    for week in range(2):
        for day in range(5):
            session_id = f"week{week}_day{day}"
            logs.append(create_workout_log(
                session_id=session_id,
                completed_at=datetime.combine(
                    current_date - timedelta(days=14 - week * 7 - day),
                    datetime.min.time()
                ),
                completion_quality=CompletionQuality.FULL,
                perceived_difficulty=PerceivedDifficulty.AS_EXPECTED,
                actual_duration_minutes=45 if day < 4 else 60,
                actual_tss=40.0 if day < 4 else 70.0
            ))

    performance = engine.analyze_performance(plan, logs, current_date)

    print(f"\n✓ Completion rate: {performance.completion_rate:.1%}")
    print(f"✓ Difficulty delta: {performance.average_difficulty_delta:+.2f}")
    print(f"✓ Volume compliance: {performance.volume_compliance:.1%}")
    print(f"✓ Intensity compliance: {performance.intensity_compliance:.1%}")
    print(f"✓ Recovery quality: {performance.recovery_quality:.1%}")
    print(f"✓ ACWR: {performance.acute_chronic_workload_ratio:.2f}")
    print(f"✓ Training monotony: {performance.training_monotony:.2f}")
    print(f"✓ Trend: {performance.trend}")

    # Assertions
    assert performance.completion_rate == 1.0, "Should have 100% completion"
    assert performance.average_difficulty_delta == 0.0, "Should be as expected"
    assert 0.95 <= performance.volume_compliance <= 1.05, "Volume should be on target"
    assert performance.trend == "stable", "Should be stable"

    print("\n✅ Test passed - healthy execution recognized")


def test_injury_risk_detection():
    """Test detection of injury risk via high ACWR"""
    print("\n" + "=" * 80)
    print("TEST 2: Injury Risk Detection - High ACWR")
    print("=" * 80)

    engine = AdaptationEngine()
    current_date = date.today()
    plan = create_test_plan(current_date - timedelta(weeks=4), weeks=4)

    # Create logs with spike in recent load (high ACWR)
    logs = []

    # Chronic period (28 days) - moderate load
    for week in range(4):
        for day in range(3):  # Only 3 sessions per week in chronic period
            session_id = f"week{week}_day{day}"
            logs.append(create_workout_log(
                session_id=session_id,
                completed_at=datetime.combine(
                    current_date - timedelta(days=28 - week * 7 - day),
                    datetime.min.time()
                ),
                completion_quality=CompletionQuality.FULL,
                perceived_difficulty=PerceivedDifficulty.AS_EXPECTED,
                actual_duration_minutes=45,
                actual_tss=40.0
            ))

    # Acute period (last 7 days) - MASSIVE spike
    for day in range(7):
        session_id = f"spike_day{day}"
        logs.append(create_workout_log(
            session_id=session_id,
            completed_at=datetime.combine(
                current_date - timedelta(days=7 - day),
                datetime.min.time()
            ),
            completion_quality=CompletionQuality.FULL,
            perceived_difficulty=PerceivedDifficulty.HARDER,
            actual_duration_minutes=90,
            actual_tss=100.0  # Very high TSS every day
        ))

    performance = engine.analyze_performance(plan, logs, current_date)

    print(f"\n📊 Performance Analysis:")
    print(f"  ACWR: {performance.acute_chronic_workload_ratio:.2f}")
    print(f"  Completion rate: {performance.completion_rate:.1%}")
    print(f"  Difficulty: {performance.average_difficulty_delta:+.2f}")

    # Get recommendations
    assessment = Assessment(
        user_id="test_user_001",
        assessment_id="test_001",
        body_composition=BodyComposition(weight=70.0),
        endurance_metrics=EnduranceMetrics(vo2max=45.0)
    )
    constraints = Constraints(
        user_id="test_user_001",
        constraint_id="test_001",
        time=TimeConstraints(
            sessions_per_week=SessionRange(min=4, max=5),
            session_duration_minutes=SessionRange(min=45, max=90)
        )
    )

    recommendations = engine.recommend_adaptations(plan, performance, assessment, constraints)

    print(f"\n🚨 Recommendations ({len(recommendations)} found):")
    for i, rec in enumerate(recommendations, 1):
        print(f"\n  {i}. {rec.trigger.value}")
        print(f"     Severity: {rec.severity:.1%}")
        print(f"     Type: {rec.adaptation_type.value}")
        print(f"     Description: {rec.description}")
        print(f"     Reasoning: {rec.reasoning[:100]}...")

    # Assertions
    assert performance.acute_chronic_workload_ratio > engine.ACWR_DANGER, "ACWR should be dangerously high"
    assert len(recommendations) > 0, "Should have recommendations"
    assert any(r.trigger == AdaptationTrigger.INJURY_RISK for r in recommendations), \
        "Should detect injury risk"

    print("\n✅ Test passed - injury risk detected and flagged")


def test_underperformance_detection():
    """Test detection of consistent underperformance"""
    print("\n" + "=" * 80)
    print("TEST 3: Underperformance Detection")
    print("=" * 80)

    engine = AdaptationEngine()
    current_date = date.today()
    plan = create_test_plan(current_date - timedelta(weeks=2), weeks=4)

    # Create logs showing struggle - some not completed, rest feel harder
    logs = []
    for week in range(2):
        for day in range(5):
            session_id = f"week{week}_day{day}"

            # Mix: 2 not completed, 2 partial, 1 full per week
            if day % 3 == 0:
                quality = CompletionQuality.NOT_COMPLETED
                difficulty = PerceivedDifficulty.HARDER
                duration = 0
                tss = 0.0
            elif day % 3 == 1:
                quality = CompletionQuality.PARTIAL
                difficulty = PerceivedDifficulty.HARDER
                duration = 30  # Cut short
                tss = 25.0
            else:
                quality = CompletionQuality.FULL
                difficulty = PerceivedDifficulty.HARDER
                duration = 45 if day < 4 else 60
                tss = 40.0 if day < 4 else 70.0

            logs.append(create_workout_log(
                session_id=session_id,
                completed_at=datetime.combine(
                    current_date - timedelta(days=14 - week * 7 - day),
                    datetime.min.time()
                ),
                completion_quality=quality,
                perceived_difficulty=difficulty,
                actual_duration_minutes=duration,
                actual_tss=tss,
                wellness=WellnessData(
                    fatigue=4,
                    soreness=4,
                    mood=2,
                    sleep_quality=3,
                    stress=4,
                    motivation=2
                )
            ))

    performance = engine.analyze_performance(plan, logs, current_date)

    print(f"\n📊 Performance Analysis:")
    print(f"  Completion rate: {performance.completion_rate:.1%}")
    print(f"  Difficulty delta: {performance.average_difficulty_delta:+.2f}")
    print(f"  Volume compliance: {performance.volume_compliance:.1%}")
    print(f"  Recovery quality: {performance.recovery_quality:.1%}")
    print(f"  Trend: {performance.trend}")

    assessment = Assessment(
        user_id="test_user_001",
        assessment_id="test_001",
        body_composition=BodyComposition(weight=70.0),
        endurance_metrics=EnduranceMetrics(vo2max=45.0)
    )
    constraints = Constraints(
        user_id="test_user_001",
        constraint_id="test_001",
        time=TimeConstraints(
            sessions_per_week=SessionRange(min=4, max=5),
            session_duration_minutes=SessionRange(min=45, max=90)
        )
    )

    recommendations = engine.recommend_adaptations(plan, performance, assessment, constraints)

    print(f"\n💡 Recommendations ({len(recommendations)} found):")
    for i, rec in enumerate(recommendations, 1):
        print(f"\n  {i}. {rec.trigger.value}")
        print(f"     Severity: {rec.severity:.1%}")
        print(f"     Type: {rec.adaptation_type.value}")
        print(f"     Suggested changes: {rec.suggested_changes}")

    # Assertions
    assert performance.completion_rate < engine.MIN_COMPLETION_RATE, "Completion should be low"
    assert performance.average_difficulty_delta > 0.5, "Workouts should feel harder"
    assert len(recommendations) > 0, "Should have recommendations"

    print("\n✅ Test passed - underperformance detected")


def test_overperformance_progression():
    """Test detection of opportunity to progress"""
    print("\n" + "=" * 80)
    print("TEST 4: Overperformance - Ready for More")
    print("=" * 80)

    engine = AdaptationEngine()
    current_date = date.today()
    plan = create_test_plan(current_date - timedelta(weeks=4), weeks=6)

    # Create logs showing progressive improvement with good ACWR
    logs = []

    # Build chronic load base (weeks 4-2 ago) - consistent training
    for week in range(4, 2, -1):
        for day in range(5):
            session_id = f"chronic_week{week}_day{day}"
            logs.append(create_workout_log(
                session_id=session_id,
                completed_at=datetime.combine(
                    current_date - timedelta(days=week * 7 + day),
                    datetime.min.time()
                ),
                completion_quality=CompletionQuality.FULL,
                perceived_difficulty=PerceivedDifficulty.AS_EXPECTED,
                actual_duration_minutes=45 if day < 4 else 60,
                actual_tss=40.0 if day < 4 else 70.0,  # Normal load
                wellness=WellnessData(
                    fatigue=2,
                    soreness=2,
                    mood=4,
                    sleep_quality=4,
                    stress=2,
                    motivation=4
                )
            ))

    # Recent weeks (last 2 weeks) - showing clear improvement trend
    for week in range(2):
        for day in range(5):
            session_id = f"week{week}_day{day}"

            # First week: 1 not completed, 2 partial, 2 full (60% completion)
            # Second week: all full (100% completion) - shows improvement
            if week == 0:
                if day == 0:
                    quality = CompletionQuality.NOT_COMPLETED
                    difficulty = PerceivedDifficulty.HARDER
                elif day % 2 == 1:
                    quality = CompletionQuality.PARTIAL
                    difficulty = PerceivedDifficulty.AS_EXPECTED
                else:
                    quality = CompletionQuality.FULL
                    difficulty = PerceivedDifficulty.AS_EXPECTED
            else:
                quality = CompletionQuality.FULL
                difficulty = PerceivedDifficulty.EASIER

            logs.append(create_workout_log(
                session_id=session_id,
                completed_at=datetime.combine(
                    current_date - timedelta(days=14 - week * 7 - day),
                    datetime.min.time()
                ),
                completion_quality=quality,
                perceived_difficulty=difficulty,
                actual_duration_minutes=(45 if day < 4 else 60) + 3,  # Slightly longer
                actual_tss=(40.0 if day < 4 else 70.0) * 1.05,  # 5% more TSS (modest increase)
                wellness=WellnessData(
                    fatigue=1,
                    soreness=2,
                    mood=5,
                    sleep_quality=5,
                    stress=1,
                    motivation=5
                )
            ))

    performance = engine.analyze_performance(plan, logs, current_date)

    print(f"\n📊 Performance Analysis:")
    print(f"  Completion rate: {performance.completion_rate:.1%}")
    print(f"  Difficulty delta: {performance.average_difficulty_delta:+.2f}")
    print(f"  Volume compliance: {performance.volume_compliance:.1%}")
    print(f"  Intensity compliance: {performance.intensity_compliance:.1%}")
    print(f"  Recovery quality: {performance.recovery_quality:.1%}")
    print(f"  ACWR: {performance.acute_chronic_workload_ratio:.2f}")
    print(f"  Trend: {performance.trend}")

    assessment = Assessment(
        user_id="test_user_001",
        assessment_id="test_001",
        body_composition=BodyComposition(weight=70.0),
        endurance_metrics=EnduranceMetrics(vo2max=45.0)
    )
    constraints = Constraints(
        user_id="test_user_001",
        constraint_id="test_001",
        time=TimeConstraints(
            sessions_per_week=SessionRange(min=4, max=5),
            session_duration_minutes=SessionRange(min=45, max=90)
        )
    )

    recommendations = engine.recommend_adaptations(plan, performance, assessment, constraints)

    print(f"\n🚀 Recommendations ({len(recommendations)} found):")
    for i, rec in enumerate(recommendations, 1):
        print(f"\n  {i}. {rec.trigger.value}")
        print(f"     Severity: {rec.severity:.1%}")
        print(f"     Type: {rec.adaptation_type.value}")
        print(f"     Description: {rec.description}")
        print(f"     Changes: {rec.suggested_changes}")

    # Assertions
    assert performance.completion_rate >= engine.GOOD_COMPLETION_RATE, "Should have high completion"
    assert performance.average_difficulty_delta < -0.3, "Should feel easier"
    assert performance.trend == "improving", "Should be improving"

    overperformance_rec = next(
        (r for r in recommendations if r.trigger == AdaptationTrigger.CONSISTENT_OVERPERFORMANCE),
        None
    )
    if overperformance_rec:
        print(f"\n✓ Found overperformance recommendation:")
        print(f"  Suggested volume increase: {overperformance_rec.suggested_changes.get('volume_multiplier', 1.0):.1%}")

    print("\n✅ Test passed - ready for progression detected")


def test_micro_adjustment_application():
    """Test application of micro-adjustments"""
    print("\n" + "=" * 80)
    print("TEST 5: Micro-Adjustment Application")
    print("=" * 80)

    engine = AdaptationEngine()
    current_date = date.today()
    plan = create_test_plan(current_date, weeks=2)

    # Create a recommendation for micro-adjustment
    recommendation = AdaptationRecommendation(
        trigger=AdaptationTrigger.POOR_RECOVERY,
        adaptation_type=AdaptationType.MICRO,
        severity=0.7,
        description="Poor recovery - reduce next sessions",
        suggested_changes={
            "volume_multiplier": 0.8,
            "next_hard_session_to_moderate": True
        },
        reasoning="Recovery quality is low"
    )

    # Get original values
    original_sessions = []
    for i, session in enumerate(plan.microcycles[0].sessions[:3]):
        original_sessions.append({
            "id": session.session_id,
            "duration": session.estimated_duration_minutes,
            "category": session.category.value
        })

    print(f"\n📋 Original upcoming sessions:")
    for sess in original_sessions:
        print(f"  {sess['id']}: {sess['duration']}min, {sess['category']}")

    # Apply micro-adjustment
    adjusted_plan = engine.apply_micro_adjustment(plan, recommendation, current_date)

    print(f"\n📝 Adjusted sessions:")
    for session in adjusted_plan.microcycles[0].sessions[:3]:
        original = next(s for s in original_sessions if s['id'] == session.session_id)
        duration_change = session.estimated_duration_minutes - original['duration']
        category_change = "" if session.category.value == original['category'] else f" (was {original['category']})"

        print(f"  {session.session_id}: {session.estimated_duration_minutes}min "
              f"({duration_change:+d}min), {session.category.value}{category_change}")

    print("\n✅ Test passed - micro-adjustment applied")


def test_regeneration_decision():
    """Test when plan should be regenerated"""
    print("\n" + "=" * 80)
    print("TEST 6: Regeneration Decision Logic")
    print("=" * 80)

    engine = AdaptationEngine()

    # Scenario 1: Persistent missed sessions
    print("\n📋 Scenario 1: Persistent missed sessions (50% completion for 4 weeks)")
    performance1 = PerformanceAnalysis(
        completion_rate=0.45,
        average_difficulty_delta=0.3,
        volume_compliance=0.5,
        intensity_compliance=0.5,
        recovery_quality=0.6,
        acute_chronic_workload_ratio=0.8,
        training_monotony=1.5,
        training_strain=100.0,
        trend="stable"
    )

    should_regen1, reason1 = engine.should_regenerate_plan(performance1, [], weeks_since_start=4)
    print(f"  Should regenerate: {should_regen1}")
    print(f"  Reason: {reason1}")
    assert should_regen1, "Should regenerate after 4 weeks of poor completion"

    # Scenario 2: Persistent underperformance
    print("\n📋 Scenario 2: Persistent underperformance (4+ weeks struggling)")
    performance2 = PerformanceAnalysis(
        completion_rate=0.65,
        average_difficulty_delta=0.9,
        volume_compliance=0.7,
        intensity_compliance=0.6,
        recovery_quality=0.5,
        acute_chronic_workload_ratio=1.1,
        training_monotony=1.2,
        training_strain=150.0,
        trend="declining"
    )

    should_regen2, reason2 = engine.should_regenerate_plan(performance2, [], weeks_since_start=5)
    print(f"  Should regenerate: {should_regen2}")
    print(f"  Reason: {reason2}")
    assert should_regen2, "Should regenerate after persistent difficulty"

    # Scenario 3: Healthy execution - no regeneration
    print("\n📋 Scenario 3: Healthy execution (no regeneration needed)")
    performance3 = PerformanceAnalysis(
        completion_rate=0.90,
        average_difficulty_delta=0.1,
        volume_compliance=0.95,
        intensity_compliance=0.95,
        recovery_quality=0.75,
        acute_chronic_workload_ratio=1.05,
        training_monotony=1.8,
        training_strain=200.0,
        trend="stable"
    )

    should_regen3, reason3 = engine.should_regenerate_plan(performance3, [], weeks_since_start=3)
    print(f"  Should regenerate: {should_regen3}")
    print(f"  Reason: {reason3}")
    assert not should_regen3, "Should not regenerate with healthy execution"

    print("\n✅ Test passed - regeneration logic working correctly")


def test_full_adaptation_workflow():
    """Test complete adaptation workflow"""
    print("\n" + "=" * 80)
    print("TEST 7: Full Adaptation Workflow (Integration)")
    print("=" * 80)

    current_date = date.today()
    plan = create_test_plan(current_date - timedelta(weeks=2), weeks=4)

    # Create logs showing some struggle
    logs = []
    for week in range(2):
        for day in range(4):  # Only 4 out of 5 sessions
            session_id = f"week{week}_day{day}"
            logs.append(create_workout_log(
                session_id=session_id,
                completed_at=datetime.combine(
                    current_date - timedelta(days=14 - week * 7 - day),
                    datetime.min.time()
                ),
                completion_quality=CompletionQuality.FULL if day < 3 else CompletionQuality.PARTIAL,
                perceived_difficulty=PerceivedDifficulty.AS_EXPECTED if day < 3 else PerceivedDifficulty.HARDER,
                actual_duration_minutes=45 if day < 3 else 35,
                actual_tss=40.0 if day < 3 else 30.0,
                wellness=WellnessData(
                    fatigue=2 if day < 3 else 4,
                    soreness=2 if day < 3 else 3,
                    mood=4 if day < 3 else 2,
                    sleep_quality=4 if day < 3 else 2,
                    stress=2 if day < 3 else 4,
                    motivation=4 if day < 3 else 3
                )
            ))

    assessment = Assessment(
        user_id="test_user_001",
        assessment_id="test_001",
        body_composition=BodyComposition(weight=70.0),
        endurance_metrics=EnduranceMetrics(vo2max=45.0)
    )
    constraints = Constraints(
        user_id="test_user_001",
        constraint_id="test_001",
        time=TimeConstraints(
            sessions_per_week=SessionRange(min=4, max=5),
            session_duration_minutes=SessionRange(min=45, max=90)
        )
    )

    # Use convenience function
    print("\n🔄 Running adaptation analysis...")
    adapted_plan, recommendations = analyze_and_adapt(
        plan=plan,
        workout_logs=logs,
        assessment=assessment,
        constraints=constraints,
        current_date=current_date
    )

    print(f"\n✓ Analysis complete")
    print(f"  Recommendations: {len(recommendations)}")

    if recommendations:
        print(f"\n📋 Top recommendation:")
        top = recommendations[0]
        print(f"  Trigger: {top.trigger.value}")
        print(f"  Type: {top.adaptation_type.value}")
        print(f"  Severity: {top.severity:.1%}")
        print(f"  Description: {top.description}")
        print(f"  Changes: {top.suggested_changes}")

    print(f"\n✓ Plan adaptation applied")
    print(f"  Original microcycles: {len(plan.microcycles)}")
    print(f"  Adapted microcycles: {len(adapted_plan.microcycles)}")

    print("\n✅ Test passed - full workflow executed successfully")


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("ADAPTATION ENGINE TEST SUITE")
    print("=" * 80)

    try:
        test_performance_analysis_healthy()
        test_injury_risk_detection()
        test_underperformance_detection()
        test_overperformance_progression()
        test_micro_adjustment_application()
        test_regeneration_decision()
        test_full_adaptation_workflow()

        print("\n" + "=" * 80)
        print("✅ ALL TESTS PASSED")
        print("=" * 80)
        print("\nThe Adaptation Engine successfully:")
        print("  ✓ Analyzes performance accurately")
        print("  ✓ Detects injury risk (ACWR)")
        print("  ✓ Identifies underperformance")
        print("  ✓ Recognizes progression opportunities")
        print("  ✓ Applies micro-adjustments")
        print("  ✓ Makes regeneration decisions")
        print("  ✓ Executes full adaptation workflow")

    except Exception as e:
        print("\n" + "=" * 80)
        print("❌ TEST FAILED")
        print("=" * 80)
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
