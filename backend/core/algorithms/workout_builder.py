"""
Workout Builder

Generates specific, executable workout prescriptions for each training session.

Creates detailed workouts with:
- Specific intervals (duration, intensity, recovery)
- Target paces calculated from VO2max and zones
- Strength exercises with sets, reps, and weights
- Warmup and cooldown protocols
- Coaching cues and notes

Research basis:
- Zone calculation: Jack Daniels VDOT, Seiler zones
- Interval prescriptions: Billat 2001, Buchheit & Laursen 2013
- Strength progression: NSCA guidelines, Schoenfeld 2010
"""
from typing import List, Optional, Tuple
import math

from core.models.workout import (
    Workout, WorkoutBlock, Interval, Exercise, Intensity,
    WorkoutType, BlockType, IntensityType
)
from core.models.training_plan import Session, SessionType, SessionCategory
from core.models.assessment import Assessment, EnduranceMetrics, StrengthMetrics
from core.models.constraint import Constraints


class WorkoutBuilder:
    """
    Builds specific workout prescriptions
    """

    def __init__(self):
        # Zone definitions (% of threshold pace/HR)
        self.ZONE_DEFINITIONS = {
            1: {"name": "Recovery", "hr_pct": (0.50, 0.60), "pace_slower": 1.40},
            2: {"name": "Easy/Aerobic", "hr_pct": (0.60, 0.70), "pace_slower": 1.25},
            3: {"name": "Moderate/Tempo", "hr_pct": (0.70, 0.80), "pace_slower": 1.10},
            4: {"name": "Threshold", "hr_pct": (0.80, 0.90), "pace_slower": 1.00},
            5: {"name": "VO2max/Intervals", "hr_pct": (0.90, 1.00), "pace_slower": 0.92}
        }

    def build(
        self,
        session: Session,
        assessment: Assessment,
        constraints: Constraints,
        week_number: int,
        phase_name: str
    ) -> Workout:
        """
        Build a complete workout prescription

        Args:
            session: Session to create workout for
            assessment: User's fitness assessment
            constraints: Training constraints
            week_number: Current week in plan
            phase_name: Current phase name (for context)

        Returns:
            Complete Workout object with detailed prescription
        """
        if session.type == SessionType.RUN:
            return self._build_run_workout(session, assessment, constraints, week_number, phase_name)
        elif session.type == SessionType.STRENGTH:
            return self._build_strength_workout(session, assessment, constraints, week_number, phase_name)
        elif session.type == SessionType.CYCLE:
            return self._build_cycling_workout(session, assessment, constraints, week_number, phase_name)
        else:
            return self._build_generic_workout(session, assessment, constraints)

    def _build_run_workout(
        self,
        session: Session,
        assessment: Assessment,
        constraints: Constraints,
        week_number: int,
        phase_name: str
    ) -> Workout:
        """
        Build running workout based on session category
        """
        workout = Workout(
            workout_id=session.session_id,
            name=self._generate_workout_name(session, phase_name),
            description=session.coaching_notes,
            type=WorkoutType.ENDURANCE
        )

        # Calculate target paces from VO2max
        paces = self._calculate_training_paces(assessment.endurance_metrics)

        # Build workout structure based on category
        if session.category == SessionCategory.EASY:
            # Easy run - just duration at easy pace
            workout.structure = self._build_easy_run(
                duration_minutes=session.estimated_duration_minutes,
                paces=paces
            )

        elif session.category == SessionCategory.MODERATE:
            # Tempo/steady state run
            workout.structure = self._build_tempo_run(
                duration_minutes=session.estimated_duration_minutes,
                paces=paces,
                phase_name=phase_name
            )

        elif session.category == SessionCategory.HARD:
            # Intervals or long run based on phase and week
            if "long" in session.coaching_notes.lower() or session.estimated_duration_minutes > 50:
                workout.structure = self._build_long_run(
                    duration_minutes=session.estimated_duration_minutes,
                    paces=paces,
                    phase_name=phase_name
                )
            else:
                workout.structure = self._build_interval_workout(
                    duration_minutes=session.estimated_duration_minutes,
                    paces=paces,
                    phase_name=phase_name,
                    week_number=week_number
                )

        # Add workout metadata
        workout.difficulty_rating = self._rate_difficulty(session.category)
        workout.estimated_duration_minutes = session.estimated_duration_minutes
        workout.coaching_notes = session.coaching_notes

        return workout

    def _build_easy_run(self, duration_minutes: int, paces: dict) -> List[WorkoutBlock]:
        """Build an easy recovery run"""
        blocks = []

        # Simple structure: easy running only
        main_block = WorkoutBlock(
            order=1,
            type=BlockType.MAIN,
            duration_minutes=duration_minutes,
            instructions=f"Easy, conversational pace. Run {duration_minutes} minutes at Zone 2. "
                        f"Target pace: {self._format_pace(paces['zone_2'])}. "
                        f"Should be able to hold a conversation comfortably."
        )

        main_block.intervals = [
            Interval(
                work_duration=duration_minutes * 60,  # Convert to seconds
                work_intensity=Intensity(
                    type=IntensityType.ZONE,
                    target="2",
                    description="Easy/Aerobic - conversational pace"
                ),
                rest_duration=0,
                rest_intensity=Intensity(type=IntensityType.RPE, target="1"),
                repetitions=1
            )
        ]

        blocks.append(main_block)

        return blocks

    def _build_tempo_run(self, duration_minutes: int, paces: dict, phase_name: str) -> List[WorkoutBlock]:
        """Build a tempo/steady state run"""
        blocks = []

        # Warmup
        warmup = WorkoutBlock(
            order=1,
            type=BlockType.WARMUP,
            duration_minutes=10,
            instructions="10 minutes easy jog, gradually building to Zone 2. Focus on form and readiness."
        )
        blocks.append(warmup)

        # Main tempo section
        tempo_duration = duration_minutes - 15  # Subtract warmup and cooldown

        main = WorkoutBlock(
            order=2,
            type=BlockType.MAIN,
            duration_minutes=tempo_duration,
            instructions=f"Tempo effort - {tempo_duration} minutes at threshold/tempo pace. "
                        f"Target pace: {self._format_pace(paces['zone_3_4'])}. "
                        f"'Comfortably hard' - you could speak in short sentences."
        )

        main.intervals = [
            Interval(
                work_duration=tempo_duration * 60,
                work_intensity=Intensity(
                    type=IntensityType.ZONE,
                    target="3-4",
                    description="Tempo/Threshold pace"
                ),
                rest_duration=0,
                rest_intensity=Intensity(type=IntensityType.ZONE, target="1"),
                repetitions=1
            )
        ]

        blocks.append(main)

        # Cooldown
        cooldown = WorkoutBlock(
            order=3,
            type=BlockType.COOLDOWN,
            duration_minutes=5,
            instructions="5 minutes easy jog to cool down."
        )
        blocks.append(cooldown)

        return blocks

    def _build_interval_workout(
        self,
        duration_minutes: int,
        paces: dict,
        phase_name: str,
        week_number: int
    ) -> List[WorkoutBlock]:
        """Build interval workout (threshold or VO2max)"""
        blocks = []

        # Warmup
        warmup = WorkoutBlock(
            order=1,
            type=BlockType.WARMUP,
            duration_minutes=12,
            instructions="Warmup: 8 min easy jog, 2 min progressive build, 2 x 30s strides with 30s recovery."
        )
        blocks.append(warmup)

        # Determine interval type based on phase
        if "base" in phase_name.lower():
            # Base phase - threshold intervals
            interval_type = "threshold"
            work_duration = 4  # 4-minute intervals
            recovery_duration = 2  # 2-minute recovery
            reps = 4
            target_pace = paces['zone_4']
            intensity_desc = "Threshold (Zone 4) - hard but sustainable"

        elif "build" in phase_name.lower():
            # Build phase - mix of threshold and VO2max
            if week_number % 2 == 0:
                # Threshold
                interval_type = "threshold"
                work_duration = 5
                recovery_duration = 2
                reps = 4
                target_pace = paces['zone_4']
                intensity_desc = "Threshold (Zone 4)"
            else:
                # VO2max
                interval_type = "vo2max"
                work_duration = 3
                recovery_duration = 2
                reps = 6
                target_pace = paces['zone_5']
                intensity_desc = "VO2max (Zone 5) - hard effort"

        elif "peak" in phase_name.lower():
            # Peak phase - race pace and VO2max
            interval_type = "race_pace"
            work_duration = 6
            recovery_duration = 2
            reps = 4
            target_pace = paces['threshold']  # Race pace approximation
            intensity_desc = "Race pace - practice your goal effort"

        else:
            # Default to threshold
            interval_type = "threshold"
            work_duration = 4
            recovery_duration = 2
            reps = 4
            target_pace = paces['zone_4']
            intensity_desc = "Threshold effort"

        # Calculate if this fits in available time
        total_interval_time = (work_duration + recovery_duration) * reps
        available_time = duration_minutes - 15  # Subtract warmup and cooldown

        if total_interval_time > available_time:
            # Reduce reps to fit
            reps = int(available_time / (work_duration + recovery_duration))

        # Main interval block
        main = WorkoutBlock(
            order=2,
            type=BlockType.MAIN,
            duration_minutes=int((work_duration + recovery_duration) * reps),
            instructions=f"{interval_type.upper()} INTERVALS: {reps} x {work_duration} min @ {self._format_pace(target_pace)} "
                        f"with {recovery_duration} min easy jog recovery. {intensity_desc}."
        )

        main.intervals = [
            Interval(
                work_duration=work_duration * 60,
                work_intensity=Intensity(
                    type=IntensityType.PACE,
                    target=str(target_pace),
                    description=intensity_desc
                ),
                rest_duration=recovery_duration * 60,
                rest_intensity=Intensity(
                    type=IntensityType.ZONE,
                    target="1-2",
                    description="Easy jog recovery"
                ),
                repetitions=reps,
                notes=f"First rep should feel controlled. Maintain pace across all reps."
            )
        ]

        blocks.append(main)

        # Cooldown
        cooldown = WorkoutBlock(
            order=3,
            type=BlockType.COOLDOWN,
            duration_minutes=8,
            instructions="8 minutes easy jog, focus on form and recovery."
        )
        blocks.append(cooldown)

        return blocks

    def _build_long_run(self, duration_minutes: int, paces: dict, phase_name: str) -> List[WorkoutBlock]:
        """Build progressive long run"""
        blocks = []

        # Long runs are mostly easy with optional tempo segments in build/peak phases
        if "build" in phase_name.lower() or "peak" in phase_name.lower():
            # Long run with tempo finish
            easy_duration = int(duration_minutes * 0.75)
            tempo_duration = int(duration_minutes * 0.25)

            main = WorkoutBlock(
                order=1,
                type=BlockType.MAIN,
                duration_minutes=duration_minutes,
                instructions=f"Long run: {easy_duration} min easy (Zone 2), "
                            f"then {tempo_duration} min at tempo/marathon pace (Zone 3-4). "
                            f"Start VERY easy and build gradually."
            )

            # Add as two segments
            main.intervals = [
                Interval(
                    work_duration=easy_duration * 60,
                    work_intensity=Intensity(type=IntensityType.ZONE, target="2", description="Easy pace"),
                    rest_duration=0,
                    rest_intensity=Intensity(type=IntensityType.ZONE, target="1"),
                    repetitions=1
                ),
                Interval(
                    work_duration=tempo_duration * 60,
                    work_intensity=Intensity(type=IntensityType.ZONE, target="3-4", description="Tempo/marathon pace"),
                    rest_duration=0,
                    rest_intensity=Intensity(type=IntensityType.ZONE, target="1"),
                    repetitions=1,
                    notes="Build into this - don't start too hard"
                )
            ]

        else:
            # Pure easy long run
            main = WorkoutBlock(
                order=1,
                type=BlockType.MAIN,
                duration_minutes=duration_minutes,
                instructions=f"Long run: {duration_minutes} minutes at easy, conversational pace (Zone 2). "
                            f"Focus on building endurance. Start slow!"
            )

            main.intervals = [
                Interval(
                    work_duration=duration_minutes * 60,
                    work_intensity=Intensity(type=IntensityType.ZONE, target="2", description="Easy/aerobic"),
                    rest_duration=0,
                    rest_intensity=Intensity(type=IntensityType.ZONE, target="1"),
                    repetitions=1
                )
            ]

        blocks.append(main)

        return blocks

    def _build_strength_workout(
        self,
        session: Session,
        assessment: Assessment,
        constraints: Constraints,
        week_number: int,
        phase_name: str
    ) -> Workout:
        """Build strength training workout"""
        workout = Workout(
            workout_id=session.session_id,
            name=f"Strength Training - {session.category.value.title()}",
            description="Strength training to support running and build power",
            type=WorkoutType.STRENGTH
        )

        # Warmup
        warmup = WorkoutBlock(
            order=1,
            type=BlockType.WARMUP,
            duration_minutes=8,
            instructions="Dynamic warmup: 5 min light cardio, 3 min dynamic stretching (leg swings, hip circles, lunges)"
        )

        # Main strength work
        main = WorkoutBlock(
            order=2,
            type=BlockType.MAIN,
            duration_minutes=session.estimated_duration_minutes - 10,
            instructions="Main strength work - focus on quality movement and progressive overload"
        )

        # Select exercises based on available equipment
        exercises = self._select_strength_exercises(
            constraints=constraints,
            session_category=session.category,
            assessment=assessment,
            phase_name=phase_name
        )

        main.exercises = exercises

        # Cooldown/core
        cooldown = WorkoutBlock(
            order=3,
            type=BlockType.COOLDOWN,
            duration_minutes=5,
            instructions="Core work: Plank (3 x 45s), Dead bug (3 x 12), Bird dog (3 x 10 each side)"
        )

        workout.structure = [warmup, main, cooldown]
        workout.difficulty_rating = self._rate_difficulty(session.category)
        workout.estimated_duration_minutes = session.estimated_duration_minutes

        return workout

    def _select_strength_exercises(
        self,
        constraints: Constraints,
        session_category: SessionCategory,
        assessment: Assessment,
        phase_name: str
    ) -> List[Exercise]:
        """
        Select appropriate strength exercises based on equipment and goals
        """
        exercises = []

        # Get available equipment
        equipment = constraints.resources.equipment

        # Determine sets and reps based on phase
        if "base" in phase_name.lower():
            # Anatomical adaptation - higher reps, lower weight
            sets = 3
            reps = 12
            intensity_pct = 65  # % of 1RM
        elif "build" in phase_name.lower():
            # Strength building - moderate reps
            sets = 4
            reps = 8
            intensity_pct = 75
        else:
            # Peak/power - lower reps, higher weight
            sets = 4
            reps = 6
            intensity_pct = 80

        # Main compound movements
        if equipment.full_squat_rack and equipment.barbells_and_plates:
            # Full gym - use barbells
            exercises.append(Exercise(
                name="Back Squat",
                sets=sets,
                reps=reps,
                weight=f"{intensity_pct}% 1RM or RPE 7-8",
                rest_seconds=120,
                notes="Full depth, controlled tempo"
            ))

            exercises.append(Exercise(
                name="Romanian Deadlift",
                sets=3,
                reps=10,
                weight=f"{intensity_pct - 10}% 1RM",
                rest_seconds=90,
                notes="Feel the hamstring stretch"
            ))

        elif equipment.dumbbells:
            # Home gym with dumbbells
            exercises.append(Exercise(
                name="Goblet Squat",
                sets=sets,
                reps=reps,
                weight="Heavy dumbbell",
                rest_seconds=90,
                notes="Keep chest up, full depth"
            ))

            exercises.append(Exercise(
                name="Single Leg RDL",
                sets=3,
                reps=10,
                weight="Moderate dumbbell",
                rest_seconds=60,
                notes="Each leg, focus on balance"
            ))

        else:
            # Bodyweight only
            exercises.append(Exercise(
                name="Bulgarian Split Squat",
                sets=sets,
                reps=reps,
                weight="Bodyweight or light dumbbells if available",
                rest_seconds=60,
                notes="Each leg, rear foot elevated"
            ))

            exercises.append(Exercise(
                name="Single Leg Deadlift",
                sets=3,
                reps=12,
                weight="Bodyweight",
                rest_seconds=45,
                notes="Each leg, slow and controlled"
            ))

        # Accessory movements
        exercises.append(Exercise(
            name="Step-ups",
            sets=3,
            reps=10,
            weight="Bodyweight or light dumbbells",
            rest_seconds=60,
            notes="Each leg, drive through heel"
        ))

        if equipment.pullup_bar:
            exercises.append(Exercise(
                name="Pull-ups or Chin-ups",
                sets=3,
                reps=[6, 10],  # Range
                weight="Bodyweight (use band assist if needed)",
                rest_seconds=90,
                notes="Full range of motion"
            ))

        # Hip/glute work
        exercises.append(Exercise(
            name="Glute Bridge",
            sets=3,
            reps=15,
            weight="Bodyweight or barbell",
            rest_seconds=45,
            notes="Squeeze glutes at top, hold 2 seconds"
        ))

        return exercises[:5]  # Limit to 5 main exercises

    def _calculate_training_paces(self, endurance_metrics: EnduranceMetrics) -> dict:
        """
        Calculate training paces from VO2max

        Uses Jack Daniels VDOT method approximation
        """
        vo2max = endurance_metrics.vo2max or 45.0  # Default if not provided

        # Estimate threshold pace from VO2max
        # Threshold is typically ~85% of VO2max
        # Rough approximation: pace (min/mile) = 1 / (vo2max * 0.85 * 0.033)
        threshold_pace = 1 / (vo2max * 0.85 * 0.033)  # min per mile

        # Calculate other zones relative to threshold
        paces = {
            'threshold': threshold_pace,
            'zone_1': threshold_pace * 1.40,  # 40% slower (recovery)
            'zone_2': threshold_pace * 1.25,  # 25% slower (easy)
            'zone_3': threshold_pace * 1.10,  # 10% slower (tempo)
            'zone_4': threshold_pace * 1.00,  # Threshold
            'zone_5': threshold_pace * 0.92,  # 8% faster (VO2max)
            'zone_3_4': threshold_pace * 1.05,  # Tempo/threshold blend
        }

        return paces

    def _format_pace(self, pace_minutes_per_mile: float) -> str:
        """Format pace as MM:SS/mile"""
        minutes = int(pace_minutes_per_mile)
        seconds = int((pace_minutes_per_mile - minutes) * 60)
        return f"{minutes}:{seconds:02d}/mile"

    def _rate_difficulty(self, category: SessionCategory) -> int:
        """Rate workout difficulty 1-5"""
        if category == SessionCategory.EASY or category == SessionCategory.RECOVERY:
            return 2
        elif category == SessionCategory.MODERATE:
            return 3
        elif category == SessionCategory.HARD:
            return 4
        else:
            return 3

    def _generate_workout_name(self, session: Session, phase_name: str) -> str:
        """Generate descriptive workout name"""
        if session.category == SessionCategory.EASY:
            return "Easy Aerobic Run"
        elif session.category == SessionCategory.MODERATE:
            return "Tempo Run"
        elif session.category == SessionCategory.HARD:
            if "peak" in phase_name.lower():
                return "Race Pace Intervals"
            elif "build" in phase_name.lower():
                return "Threshold Intervals"
            else:
                return "Long Run"
        else:
            return "Training Run"

    def _build_cycling_workout(
        self,
        session: Session,
        assessment: Assessment,
        constraints: Constraints,
        week_number: int,
        phase_name: str
    ) -> Workout:
        """Build cycling workout (similar structure to running)"""
        # Simplified - similar to running but with cycling-specific notes
        workout = Workout(
            workout_id=session.session_id,
            name=f"Cycling - {session.category.value.title()}",
            description="Cycling session (low impact alternative to running)",
            type=WorkoutType.ENDURANCE
        )

        main = WorkoutBlock(
            order=1,
            type=BlockType.MAIN,
            duration_minutes=session.estimated_duration_minutes,
            instructions=f"Cycling: {session.estimated_duration_minutes} min at {session.category.value} effort"
        )

        workout.structure = [main]
        return workout

    def _build_generic_workout(
        self,
        session: Session,
        assessment: Assessment,
        constraints: Constraints
    ) -> Workout:
        """Build generic workout for other types"""
        workout = Workout(
            workout_id=session.session_id,
            name=f"{session.type.value.title()} Session",
            description=session.coaching_notes,
            type=WorkoutType.ENDURANCE
        )

        main = WorkoutBlock(
            order=1,
            type=BlockType.MAIN,
            duration_minutes=session.estimated_duration_minutes,
            instructions=session.coaching_notes
        )

        workout.structure = [main]
        return workout


def build_workout(
    session: Session,
    assessment: Assessment,
    constraints: Constraints,
    week_number: int,
    phase_name: str
) -> Workout:
    """
    Convenience function to build workout

    Args:
        session: Session to create workout for
        assessment: User fitness assessment
        constraints: Training constraints
        week_number: Current week number
        phase_name: Current phase name

    Returns:
        Complete Workout with detailed prescription
    """
    builder = WorkoutBuilder()
    return builder.build(session, assessment, constraints, week_number, phase_name)
