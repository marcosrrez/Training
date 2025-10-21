"""
Training Plan Generation Engine

Core algorithm that generates complete personalized training plans.

This implements the main plan generation flow:
1. Analyze goals and feasibility
2. Select methodology
3. Build periodization structure (macrocycle)
4. Generate mesocycles (training blocks)
5. Create microcycles (weekly plans) - TODO
6. Populate individual workouts - TODO
7. Validate plan coherence

Research basis: Integration of multiple periodization models and training methods
"""
from typing import List
from datetime import datetime, date, timedelta

from core.models.training_plan import TrainingPlan, Macrocycle, Mesocycle, Microcycle
from core.models.goal import Goal
from core.models.assessment import Assessment
from core.models.constraint import Constraints

from .feasibility import analyze_goal_feasibility
from .methodology_selector import select_optimal_methodology
from .macrocycle_builder import build_macrocycle
from .mesocycle_generator import generate_mesocycles
from .microcycle_creator import create_microcycles


class TrainingPlanGenerator:
    """
    Generates complete personalized training plans
    """

    def generate(
        self,
        user_id: str,
        goals: List[Goal],
        assessment: Assessment,
        constraints: Constraints
    ) -> TrainingPlan:
        """
        Main plan generation method

        Args:
            user_id: User identifier
            goals: List of training goals (primary + secondary)
            assessment: Current fitness assessment
            constraints: Time and resource constraints

        Returns:
            Complete TrainingPlan object

        Raises:
            ValueError: If goals are incompatible or unrealistic
        """
        print("🚀 Starting training plan generation...")

        # Step 1: Analyze goal feasibility
        print("\n📊 Step 1: Analyzing goal feasibility...")
        primary_goal = goals[0] if goals else None
        if not primary_goal:
            raise ValueError("At least one goal is required")

        feasibility = analyze_goal_feasibility(primary_goal, assessment, constraints)

        if feasibility.probability < 0.3:
            print(f"⚠️  Warning: Goal has low probability of success ({feasibility.probability:.0%})")
            print(f"   Recommendation: {feasibility.recommendation}")
            # In production, might want to require user confirmation here

        print(f"✓ Goal feasibility analyzed: {feasibility.probability:.0%} probability")
        print(f"  Realistic timeline: {feasibility.realistic_timeline_weeks} weeks")

        # Step 2: Select methodology
        print("\n🎯 Step 2: Selecting optimal training methodology...")
        methodology = select_optimal_methodology(goals, assessment, constraints)

        print(f"✓ Selected methodology: {methodology.name}")
        print(f"  Periodization: {methodology.periodization_model.value}")

        # Step 3: Calculate training parameters
        print("\n📅 Step 3: Calculating training timeline...")
        start_date = date.today()
        end_date = primary_goal.target_date.date() if primary_goal.target_date else start_date + timedelta(weeks=16)
        total_weeks = (end_date - start_date).days // 7

        print(f"✓ Training duration: {total_weeks} weeks")
        print(f"  Start: {start_date}")
        print(f"  End: {end_date}")

        # Step 4: Build macrocycle structure (phases)
        print("\n🏗️  Step 4: Building macrocycle structure...")
        macrocycle = build_macrocycle(
            goals=goals,
            assessment=assessment,
            total_weeks=total_weeks,
            periodization_model=methodology.periodization_model
        )

        print(f"✓ Macrocycle built with {len(macrocycle.phases)} phases:")
        for phase in macrocycle.phases:
            print(f"  - {phase.name}: Weeks {phase.start_week}-{phase.end_week} ({phase.duration_weeks} weeks)")

        # Step 5: Generate mesocycles for each phase
        print("\n📦 Step 5: Generating mesocycles (training blocks)...")
        all_mesocycles = []

        for phase in macrocycle.phases:
            phase_mesocycles = generate_mesocycles(
                phase=phase,
                methodology=methodology,
                assessment=assessment,
                constraints=constraints,
                goals=goals
            )
            all_mesocycles.extend(phase_mesocycles)

            print(f"✓ {phase.name}: {len(phase_mesocycles)} mesocycles generated")

        print(f"✓ Total mesocycles: {len(all_mesocycles)}")

        # Step 6: Create microcycles (weekly plans)
        print("\n📅 Step 6: Creating microcycles (weekly plans)...")
        all_microcycles = []

        for mesocycle in all_mesocycles:
            meso_microcycles = create_microcycles(
                mesocycle=mesocycle,
                goals=goals,
                constraints=constraints,
                assessment=assessment,
                start_date=start_date
            )
            all_microcycles.extend(meso_microcycles)

            print(f"✓ Mesocycle {mesocycle.cycle_number}: {len(meso_microcycles)} weeks created")

        print(f"✓ Total microcycles: {len(all_microcycles)} weeks")

        # Step 7: Populate individual workouts
        print("\n🏃 Step 7: Populating individual workouts...")
        print("⚠️  Workout generation - TO BE IMPLEMENTED")
        # TODO: Implement workout generation

        # Step 8: Validate plan coherence
        print("\n✅ Step 8: Validating plan...")
        self._validate_plan(macrocycle, all_mesocycles, all_microcycles, constraints)
        print("✓ Plan validation passed")

        # Create the training plan object
        plan = TrainingPlan(
            plan_id=f"plan_{user_id}_{int(datetime.now().timestamp())}",
            user_id=user_id,
            goal_ids=[g.goal_id for g in goals],
            generated_at=datetime.now(),
            start_date=start_date,
            end_date=end_date,
            total_duration_weeks=total_weeks,
            methodology=methodology,
            macrocycle=macrocycle,
            mesocycles=all_mesocycles,
            microcycles=all_microcycles,
            current_week=0
        )

        # Update goal with feasibility assessment
        primary_goal.feasibility = feasibility

        print("\n🎉 Training plan generation complete!")
        print(f"   Plan ID: {plan.plan_id}")
        print(f"   Duration: {total_weeks} weeks")
        print(f"   Phases: {len(macrocycle.phases)}")
        print(f"   Mesocycles: {len(all_mesocycles)}")
        print(f"   Microcycles: {len(all_microcycles)}")
        print(f"   Total sessions: {sum(len(m.sessions) for m in all_microcycles)}")
        print(f"   Methodology: {methodology.name}")

        return plan

    def _validate_plan(
        self,
        macrocycle: Macrocycle,
        mesocycles: List[Mesocycle],
        microcycles: List[Microcycle],
        constraints: Constraints
    ):
        """
        Validate that the plan is coherent and feasible

        Checks:
        - Phases don't overlap and cover full duration
        - Mesocycles align with phases
        - Microcycles cover all weeks
        - Volume progression is reasonable
        - Time constraints are respected
        """
        # Check phases cover full duration without gaps
        total_weeks = macrocycle.total_weeks
        covered_weeks = sum(p.duration_weeks for p in macrocycle.phases)

        if covered_weeks != total_weeks:
            raise ValueError(f"Phase coverage mismatch: {covered_weeks} weeks != {total_weeks} weeks")

        # Check mesocycles align with phases
        total_mesocycle_weeks = sum(m.duration_weeks for m in mesocycles)
        if total_mesocycle_weeks != total_weeks:
            raise ValueError(f"Mesocycle coverage mismatch: {total_mesocycle_weeks} weeks != {total_weeks} weeks")

        # Check microcycles cover all weeks
        if len(microcycles) != total_weeks:
            raise ValueError(f"Microcycle count mismatch: {len(microcycles)} microcycles != {total_weeks} weeks")

        # Check volume constraints
        max_volume = constraints.time.total_weekly_hours or 10.0
        for meso in mesocycles:
            if meso.base_weekly_volume > max_volume * 1.2:  # Allow 20% overshoot
                raise ValueError(
                    f"Mesocycle {meso.cycle_number} volume ({meso.base_weekly_volume:.1f}h) "
                    f"exceeds constraint ({max_volume:.1f}h)"
                )

        # Check session counts
        sessions_per_week = constraints.time.sessions_per_week
        for micro in microcycles:
            if not micro.is_recovery_week:
                session_count = len(micro.sessions)
                if session_count < sessions_per_week.min or session_count > sessions_per_week.max:
                    raise ValueError(
                        f"Week {micro.week_number} has {session_count} sessions, "
                        f"but constraints specify {sessions_per_week.min}-{sessions_per_week.max}"
                    )

        # All checks passed
        return True


def generate_training_plan(
    user_id: str,
    goals: List[Goal],
    assessment: Assessment,
    constraints: Constraints
) -> TrainingPlan:
    """
    Convenience function to generate training plan
    """
    generator = TrainingPlanGenerator()
    return generator.generate(user_id, goals, assessment, constraints)
