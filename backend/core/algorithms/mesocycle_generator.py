"""
Mesocycle Generator

Generates training blocks (mesocycles) within each macrocycle phase.

A mesocycle is typically 3-6 weeks and includes:
- Volume progression (build, maintain, reduce)
- Intensity distribution specific to phase
- Key workouts that define the block
- Recovery week placement
- Base weekly volume targets

Research basis:
- Mesocycle structure: Issurin 2010, Rønnestad & Mujika 2014
- Volume progression: Kiely 2012, Busso 2003
- Recovery integration: Aubry et al. 2014
"""
from typing import List, Dict
import math

from core.models.training_plan import (
    Mesocycle, Phase, VolumeProgression, IntensityDistribution,
    Methodology, WorkoutTemplate
)
from core.models.goal import Goal, GoalType
from core.models.constraint import Constraints
from core.models.assessment import Assessment


class MesocycleGenerator:
    """
    Generates mesocycles (training blocks) for each phase
    """

    def __init__(self):
        # Typical mesocycle length (weeks)
        self.STANDARD_MESOCYCLE_LENGTH = 4
        self.MIN_MESOCYCLE_LENGTH = 3
        self.MAX_MESOCYCLE_LENGTH = 6

        # Recovery week frequency
        self.BEGINNER_RECOVERY_FREQUENCY = 3  # Every 3 weeks
        self.INTERMEDIATE_RECOVERY_FREQUENCY = 4  # Every 4 weeks
        self.ADVANCED_RECOVERY_FREQUENCY = 5  # Every 5 weeks

    def generate(
        self,
        phase: Phase,
        methodology: Methodology,
        assessment: Assessment,
        constraints: Constraints,
        goals: List[Goal]
    ) -> List[Mesocycle]:
        """
        Generate mesocycles for a training phase

        Args:
            phase: The macrocycle phase to break into mesocycles
            methodology: Selected training methodology
            assessment: User's fitness assessment
            constraints: Training constraints
            goals: Training goals

        Returns:
            List of mesocycles for this phase
        """
        mesocycles = []
        phase_weeks = phase.duration_weeks

        # Determine mesocycle length based on phase duration and experience
        mesocycle_length = self._determine_mesocycle_length(phase_weeks, assessment)

        # Calculate how many mesocycles fit in this phase
        num_mesocycles = math.ceil(phase_weeks / mesocycle_length)

        # Determine recovery frequency
        recovery_frequency = self._determine_recovery_frequency(assessment)

        # Calculate base weekly volume from constraints
        base_volume = self._calculate_base_volume(constraints, assessment)

        # Generate each mesocycle
        current_week = phase.start_week
        for i in range(num_mesocycles):
            # Calculate actual weeks for this mesocycle
            weeks_remaining = phase.end_week - current_week
            cycle_weeks = min(mesocycle_length, weeks_remaining)

            if cycle_weeks <= 0:
                break

            # Determine volume progression for this mesocycle
            volume_progression = self._determine_volume_progression(
                phase=phase,
                mesocycle_number=i,
                total_mesocycles=num_mesocycles
            )

            # Adjust intensity distribution for this mesocycle within the phase
            intensity_dist = self._adjust_intensity_for_phase_and_cycle(
                base_distribution=methodology.intensity_distribution,
                phase=phase,
                mesocycle_number=i,
                total_mesocycles=num_mesocycles
            )

            # Identify key workouts for this mesocycle
            key_workouts = self._identify_key_workouts(
                phase=phase,
                mesocycle_number=i,
                goals=goals,
                methodology=methodology
            )

            # Create mesocycle
            mesocycle = Mesocycle(
                cycle_number=i + 1,
                start_week=current_week,
                end_week=current_week + cycle_weeks,
                duration_weeks=cycle_weeks,
                focus=self._generate_mesocycle_focus(phase, i, num_mesocycles),
                volume_progression=volume_progression,
                intensity_distribution=intensity_dist,
                key_workouts=key_workouts,
                base_weekly_volume=base_volume * self._get_volume_multiplier(
                    volume_progression, i, num_mesocycles
                ),
                recovery_frequency=recovery_frequency
            )

            mesocycles.append(mesocycle)
            current_week += cycle_weeks

        return mesocycles

    def _determine_mesocycle_length(self, phase_weeks: int, assessment: Assessment) -> int:
        """
        Determine optimal mesocycle length based on phase duration and experience

        Beginners: Shorter mesocycles (3 weeks) for more frequent variation
        Advanced: Longer mesocycles (4-5 weeks) for deeper adaptations
        """
        training_age = assessment.training_history.years_of_training

        if phase_weeks <= 6:
            # Short phase - just one or two mesocycles
            return max(self.MIN_MESOCYCLE_LENGTH, phase_weeks // 2)

        # Base on training age
        if training_age < 1:
            return 3  # Beginners - shorter blocks
        elif training_age < 3:
            return 4  # Intermediate - standard blocks
        else:
            return 4  # Advanced - could go 5, but 4 is good standard

    def _determine_recovery_frequency(self, assessment: Assessment) -> int:
        """
        Determine how often to include recovery weeks

        Based on training age and recovery capacity
        """
        training_age = assessment.training_history.years_of_training
        stress_level = assessment.lifestyle.stress_level
        sleep_quality = assessment.lifestyle.sleep_quality

        # Base frequency on training age
        if training_age < 1:
            base_frequency = self.BEGINNER_RECOVERY_FREQUENCY
        elif training_age < 3:
            base_frequency = self.INTERMEDIATE_RECOVERY_FREQUENCY
        else:
            base_frequency = self.ADVANCED_RECOVERY_FREQUENCY

        # Adjust for poor recovery capacity
        if stress_level >= 4 or sleep_quality <= 2:
            base_frequency = max(3, base_frequency - 1)  # More frequent recovery

        return base_frequency

    def _calculate_base_volume(self, constraints: Constraints, assessment: Assessment) -> float:
        """
        Calculate base weekly training volume in hours

        This is the "comfortable" volume the user can sustain
        """
        # Get total available hours from constraints
        available_hours = constraints.time.total_weekly_hours or 4.0

        # Adjust based on training history - don't jump to max volume immediately
        recent_volume = assessment.training_history.recent_weekly_volume
        detraining_months = assessment.training_history.detraining_period_months

        if detraining_months > 6:
            # Significantly detrained - start at 50% of available
            base_volume = available_hours * 0.5
        elif detraining_months > 3:
            # Moderately detrained - start at 60% of available
            base_volume = available_hours * 0.6
        elif recent_volume > 0:
            # Currently training - can start closer to current volume
            base_volume = min(recent_volume * 1.1, available_hours * 0.75)
        else:
            # No recent training - conservative start
            base_volume = available_hours * 0.6

        # Ensure minimum viable training
        return max(2.0, min(base_volume, available_hours))

    def _determine_volume_progression(
        self,
        phase: Phase,
        mesocycle_number: int,
        total_mesocycles: int
    ) -> VolumeProgression:
        """
        Determine volume progression for a specific mesocycle

        Volume progression varies by phase:
        - Base: BUILD (increasing volume)
        - Build: BUILD then MAINTAIN
        - Peak: MAINTAIN or slight REDUCE
        - Taper: REDUCE
        """
        phase_name = phase.name.lower()

        if "base" in phase_name:
            # Base phase - always building volume
            return VolumeProgression.BUILD

        elif "build" in phase_name:
            # Build phase - increase volume in first mesocycles, maintain in later
            if mesocycle_number < total_mesocycles - 1:
                return VolumeProgression.BUILD
            else:
                return VolumeProgression.MAINTAIN

        elif "peak" in phase_name or "competition" in phase_name:
            # Peak phase - maintain or slightly reduce
            if mesocycle_number == 0:
                return VolumeProgression.MAINTAIN
            else:
                return VolumeProgression.REDUCE

        elif "taper" in phase_name:
            # Taper - always reducing
            return VolumeProgression.REDUCE

        else:
            # Default - maintain
            return VolumeProgression.MAINTAIN

    def _adjust_intensity_for_phase_and_cycle(
        self,
        base_distribution: IntensityDistribution,
        phase: Phase,
        mesocycle_number: int,
        total_mesocycles: int
    ) -> IntensityDistribution:
        """
        Adjust intensity distribution based on phase and mesocycle position

        Early in phase: More aerobic work
        Later in phase: More intensity
        """
        phase_name = phase.name.lower()

        # Start with base methodology distribution
        z1 = base_distribution.zone_1_percentage
        z2 = base_distribution.zone_2_percentage
        z3 = base_distribution.zone_3_percentage
        z4 = base_distribution.zone_4_percentage
        z5 = base_distribution.zone_5_percentage

        # Adjust based on phase
        if "base" in phase_name:
            # Base phase - emphasize aerobic work
            # Shift 10% from hard zones to easy zones
            shift = 10.0
            z1 += shift * 0.6
            z2 += shift * 0.4
            z4 = max(0, z4 - shift * 0.6)
            z5 = max(0, z5 - shift * 0.4)

        elif "build" in phase_name:
            # Build phase - balanced approach, slightly more intensity as phase progresses
            progress = mesocycle_number / max(1, total_mesocycles - 1)
            # Gradually shift 5% to harder zones
            shift = 5.0 * progress
            z1 -= shift * 0.5
            z2 -= shift * 0.5
            z4 += shift * 0.6
            z5 += shift * 0.4

        elif "peak" in phase_name or "competition" in phase_name:
            # Peak phase - more high intensity work
            shift = 10.0
            z1 -= shift * 0.5
            z2 -= shift * 0.5
            z4 += shift * 0.4
            z5 += shift * 0.6

        elif "taper" in phase_name:
            # Taper - maintain intensity, reduce volume
            # Keep intensity distribution similar to base
            pass

        # Ensure no negative percentages and total = 100%
        z1 = max(0, z1)
        z2 = max(0, z2)
        z3 = max(0, z3)
        z4 = max(0, z4)
        z5 = max(0, z5)

        # Normalize to 100%
        total = z1 + z2 + z3 + z4 + z5
        if total > 0:
            z1 = (z1 / total) * 100
            z2 = (z2 / total) * 100
            z3 = (z3 / total) * 100
            z4 = (z4 / total) * 100
            z5 = (z5 / total) * 100

        return IntensityDistribution(
            zone_1_percentage=round(z1, 1),
            zone_2_percentage=round(z2, 1),
            zone_3_percentage=round(z3, 1),
            zone_4_percentage=round(z4, 1),
            zone_5_percentage=round(z5, 1)
        )

    def _identify_key_workouts(
        self,
        phase: Phase,
        mesocycle_number: int,
        goals: List[Goal],
        methodology: Methodology
    ) -> List[WorkoutTemplate]:
        """
        Identify key workouts that define this mesocycle

        Key workouts are the cornerstone sessions that drive adaptation
        """
        key_workouts = []
        phase_name = phase.name.lower()

        # Determine primary goal type
        primary_goal_type = goals[0].type if goals else GoalType.ENDURANCE

        if "base" in phase_name:
            # Base phase key workouts
            if primary_goal_type in [GoalType.ENDURANCE, GoalType.HYBRID]:
                key_workouts.extend([
                    WorkoutTemplate(
                        workout_id=f"base_long_run_{mesocycle_number}",
                        name="Progressive Long Run",
                        description="Build aerobic endurance with progressive long run"
                    ),
                    WorkoutTemplate(
                        workout_id=f"base_tempo_{mesocycle_number}",
                        name="Steady State Run",
                        description="Aerobic threshold development"
                    )
                ])

            if primary_goal_type in [GoalType.STRENGTH, GoalType.HYBRID]:
                key_workouts.append(
                    WorkoutTemplate(
                        workout_id=f"base_strength_{mesocycle_number}",
                        name="Foundation Strength",
                        description="Anatomical adaptation and movement quality"
                    )
                )

        elif "build" in phase_name:
            # Build phase key workouts - more intensity
            if primary_goal_type in [GoalType.ENDURANCE, GoalType.HYBRID]:
                key_workouts.extend([
                    WorkoutTemplate(
                        workout_id=f"build_threshold_{mesocycle_number}",
                        name="Threshold Intervals",
                        description="Lactate threshold development"
                    ),
                    WorkoutTemplate(
                        workout_id=f"build_vo2max_{mesocycle_number}",
                        name="VO2max Intervals",
                        description="Maximal aerobic power development"
                    ),
                    WorkoutTemplate(
                        workout_id=f"build_long_{mesocycle_number}",
                        name="Long Run with Tempo",
                        description="Endurance with race pace segments"
                    )
                ])

            if primary_goal_type in [GoalType.STRENGTH, GoalType.HYBRID]:
                key_workouts.append(
                    WorkoutTemplate(
                        workout_id=f"build_strength_{mesocycle_number}",
                        name="Strength Development",
                        description="Progressive overload for strength gains"
                    )
                )

        elif "peak" in phase_name or "competition" in phase_name:
            # Peak phase - race-specific workouts
            if primary_goal_type in [GoalType.ENDURANCE, GoalType.HYBRID]:
                key_workouts.extend([
                    WorkoutTemplate(
                        workout_id=f"peak_race_pace_{mesocycle_number}",
                        name="Race Pace Intervals",
                        description="Practice goal race pace"
                    ),
                    WorkoutTemplate(
                        workout_id=f"peak_sharpener_{mesocycle_number}",
                        name="Speed Sharpener",
                        description="Short, fast intervals to maintain sharpness"
                    )
                ])

            if primary_goal_type in [GoalType.STRENGTH, GoalType.HYBRID]:
                key_workouts.append(
                    WorkoutTemplate(
                        workout_id=f"peak_power_{mesocycle_number}",
                        name="Peak Power",
                        description="Low volume, high intensity strength work"
                    )
                )

        elif "taper" in phase_name:
            # Taper - reduced volume, maintain intensity
            key_workouts.append(
                WorkoutTemplate(
                    workout_id=f"taper_shakeout_{mesocycle_number}",
                    name="Taper Shakeout",
                    description="Short session to maintain feel without fatigue"
                )
            )

        return key_workouts

    def _generate_mesocycle_focus(
        self,
        phase: Phase,
        mesocycle_number: int,
        total_mesocycles: int
    ) -> str:
        """
        Generate focus description for this mesocycle
        """
        phase_name = phase.name.lower()
        position = "early" if mesocycle_number < total_mesocycles / 2 else "late"

        if "base" in phase_name:
            if position == "early":
                return "Aerobic base development and movement quality"
            else:
                return "Aerobic endurance and foundational strength"

        elif "build" in phase_name:
            if position == "early":
                return "Volume accumulation and threshold development"
            else:
                return "Intensity progression and VO2max development"

        elif "peak" in phase_name or "competition" in phase_name:
            if position == "early":
                return "Race-specific preparation"
            else:
                return "Final sharpening and race readiness"

        elif "taper" in phase_name:
            return "Recovery and freshness"

        else:
            return phase.focus

    def _get_volume_multiplier(
        self,
        progression: VolumeProgression,
        mesocycle_number: int,
        total_mesocycles: int
    ) -> float:
        """
        Get volume multiplier for this mesocycle

        Returns multiplier relative to base volume:
        - BUILD: 1.0 → 1.4 (progressively increasing)
        - MAINTAIN: 1.2 (steady)
        - REDUCE: 1.0 → 0.6 (progressively decreasing)
        """
        if progression == VolumeProgression.BUILD:
            # Progressive increase: 1.0 → 1.4
            progress = mesocycle_number / max(1, total_mesocycles - 1)
            return 1.0 + (progress * 0.4)

        elif progression == VolumeProgression.MAINTAIN:
            # Steady state
            return 1.2

        elif progression == VolumeProgression.REDUCE:
            # Progressive decrease: 1.0 → 0.6
            progress = mesocycle_number / max(1, total_mesocycles - 1)
            return 1.0 - (progress * 0.4)

        else:
            return 1.0


def generate_mesocycles(
    phase: Phase,
    methodology: Methodology,
    assessment: Assessment,
    constraints: Constraints,
    goals: List[Goal]
) -> List[Mesocycle]:
    """
    Convenience function to generate mesocycles

    Args:
        phase: Macrocycle phase to break into mesocycles
        methodology: Selected training methodology
        assessment: User fitness assessment
        constraints: Training constraints
        goals: Training goals

    Returns:
        List of mesocycles for the phase
    """
    generator = MesocycleGenerator()
    return generator.generate(phase, methodology, assessment, constraints, goals)
