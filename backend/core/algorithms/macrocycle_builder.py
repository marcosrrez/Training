"""
Macrocycle Builder

Generates the overall periodization structure (macrocycle) for a training plan.

A macrocycle consists of multiple phases:
- Base Building: Develop aerobic foundation, movement quality, general strength
- Build Phase(s): Increase volume/intensity progressively
- Peak/Specific Phase: Race-specific preparation
- Taper: Recovery and preparation for goal event/test
- Transition: Recovery between cycles

Research basis:
- Block Periodization: Issurin 2010, Rønnestad & Mujika 2014
- Linear Periodization: Bompa & Haff 2009
- Concurrent Training Periodization: García-Pallarés et al. 2010
"""
from typing import List, Tuple
from datetime import date, timedelta

from core.models.training_plan import Macrocycle, Phase, PeriodizationModel
from core.models.goal import Goal, GoalType
from core.models.assessment import Assessment


class MacrocycleBuilder:
    """
    Builds macrocycle structure based on goals and timeline
    """

    def __init__(self):
        # Minimum phase durations (weeks)
        self.MIN_BASE_WEEKS = 4
        self.MIN_BUILD_WEEKS = 6
        self.MIN_PEAK_WEEKS = 3
        self.MIN_TAPER_WEEKS = 1
        self.MIN_TRANSITION_WEEKS = 1

    def build(
        self,
        goals: List[Goal],
        assessment: Assessment,
        total_weeks: int,
        periodization_model: PeriodizationModel
    ) -> Macrocycle:
        """
        Build macrocycle structure

        Args:
            goals: User's training goals
            assessment: Current fitness assessment
            total_weeks: Total weeks until goal date
            periodization_model: Type of periodization to use

        Returns:
            Macrocycle with phases defined
        """
        if periodization_model == PeriodizationModel.LINEAR:
            phases = self._build_linear_periodization(goals, assessment, total_weeks)
        elif periodization_model == PeriodizationModel.BLOCK:
            phases = self._build_block_periodization(goals, assessment, total_weeks)
        elif periodization_model == PeriodizationModel.CONJUGATE:
            phases = self._build_conjugate_periodization(goals, assessment, total_weeks)
        elif periodization_model == PeriodizationModel.UNDULATING:
            phases = self._build_undulating_periodization(goals, assessment, total_weeks)
        else:
            # Default to block periodization
            phases = self._build_block_periodization(goals, assessment, total_weeks)

        return Macrocycle(
            phases=phases,
            total_weeks=total_weeks,
            periodization_model=periodization_model
        )

    def _build_block_periodization(
        self,
        goals: List[Goal],
        assessment: Assessment,
        total_weeks: int
    ) -> List[Phase]:
        """
        Build block periodization structure

        Block periodization focuses on one quality at a time in each block:
        - Block 1: Aerobic base (high volume, low intensity)
        - Block 2: Lactate threshold / strength endurance
        - Block 3: VO2max / power
        - Block 4: Competition-specific / taper

        Research: Issurin 2010, Rønnestad & Mujika 2014
        """
        phases = []

        # Determine if athlete needs extended base building
        needs_base = self._needs_base_building(assessment, goals)

        # Calculate phase durations based on total weeks
        if total_weeks < 12:
            # Short cycle - simplified structure
            return self._build_short_cycle(goals, assessment, total_weeks)

        elif total_weeks < 24:
            # Medium cycle (12-24 weeks)
            if needs_base:
                base_weeks = max(self.MIN_BASE_WEEKS, int(total_weeks * 0.35))
                build_weeks = int(total_weeks * 0.45)
                peak_weeks = max(self.MIN_PEAK_WEEKS, int(total_weeks * 0.15))
                taper_weeks = total_weeks - base_weeks - build_weeks - peak_weeks

                phases = [
                    self._create_base_phase(0, base_weeks, goals),
                    self._create_build_phase(base_weeks, base_weeks + build_weeks, goals, phase_num=1),
                    self._create_peak_phase(base_weeks + build_weeks, base_weeks + build_weeks + peak_weeks, goals),
                    self._create_taper_phase(base_weeks + build_weeks + peak_weeks, total_weeks, goals)
                ]
            else:
                # Skip or minimize base if already trained
                base_weeks = max(2, int(total_weeks * 0.2))
                build_weeks = int(total_weeks * 0.55)
                peak_weeks = max(self.MIN_PEAK_WEEKS, int(total_weeks * 0.2))
                taper_weeks = total_weeks - base_weeks - build_weeks - peak_weeks

                phases = [
                    self._create_base_phase(0, base_weeks, goals),
                    self._create_build_phase(base_weeks, base_weeks + build_weeks, goals, phase_num=1),
                    self._create_peak_phase(base_weeks + build_weeks, base_weeks + build_weeks + peak_weeks, goals),
                    self._create_taper_phase(base_weeks + build_weeks + peak_weeks, total_weeks, goals)
                ]

        else:
            # Long cycle (24+ weeks) - multiple build phases
            if needs_base:
                base_weeks = max(self.MIN_BASE_WEEKS, int(total_weeks * 0.25))
            else:
                base_weeks = max(2, int(total_weeks * 0.15))

            # Peak and taper
            peak_weeks = max(self.MIN_PEAK_WEEKS, int(total_weeks * 0.12))
            taper_weeks = max(self.MIN_TAPER_WEEKS, int(total_weeks * 0.05))

            # Remaining weeks for build phases
            remaining = total_weeks - base_weeks - peak_weeks - taper_weeks

            # Split into 2-3 build phases
            if remaining >= 24:
                # 3 build phases
                build1_weeks = remaining // 3
                build2_weeks = remaining // 3
                build3_weeks = remaining - build1_weeks - build2_weeks

                phases = [
                    self._create_base_phase(0, base_weeks, goals),
                    self._create_build_phase(base_weeks, base_weeks + build1_weeks, goals, phase_num=1),
                    self._create_build_phase(base_weeks + build1_weeks, base_weeks + build1_weeks + build2_weeks, goals, phase_num=2),
                    self._create_build_phase(base_weeks + build1_weeks + build2_weeks, base_weeks + build1_weeks + build2_weeks + build3_weeks, goals, phase_num=3),
                    self._create_peak_phase(total_weeks - peak_weeks - taper_weeks, total_weeks - taper_weeks, goals),
                    self._create_taper_phase(total_weeks - taper_weeks, total_weeks, goals)
                ]
            else:
                # 2 build phases
                build1_weeks = remaining // 2
                build2_weeks = remaining - build1_weeks

                phases = [
                    self._create_base_phase(0, base_weeks, goals),
                    self._create_build_phase(base_weeks, base_weeks + build1_weeks, goals, phase_num=1),
                    self._create_build_phase(base_weeks + build1_weeks, base_weeks + build1_weeks + build2_weeks, goals, phase_num=2),
                    self._create_peak_phase(total_weeks - peak_weeks - taper_weeks, total_weeks - taper_weeks, goals),
                    self._create_taper_phase(total_weeks - taper_weeks, total_weeks, goals)
                ]

        return phases

    def _build_linear_periodization(
        self,
        goals: List[Goal],
        assessment: Assessment,
        total_weeks: int
    ) -> List[Phase]:
        """
        Build linear periodization structure

        Linear periodization gradually increases intensity while decreasing volume.
        Traditional model, works well for beginners.

        Research: Bompa & Haff 2009
        """
        # Linear periodization is simpler - continuous progression
        phases = []

        if total_weeks < 12:
            return self._build_short_cycle(goals, assessment, total_weeks)

        # Phase allocation for linear progression
        base_weeks = max(self.MIN_BASE_WEEKS, int(total_weeks * 0.35))
        build_weeks = int(total_weeks * 0.45)
        peak_weeks = max(self.MIN_PEAK_WEEKS, int(total_weeks * 0.15))
        taper_weeks = total_weeks - base_weeks - build_weeks - peak_weeks

        phases = [
            Phase(
                name="Foundation",
                start_week=0,
                end_week=base_weeks,
                duration_weeks=base_weeks,
                focus="Build general fitness and movement patterns",
                description="High volume, low intensity. Focus on aerobic base and strength foundation.",
                expected_outcomes=[
                    "Improved aerobic capacity",
                    "Movement pattern development",
                    "Injury resilience"
                ]
            ),
            Phase(
                name="Progressive Build",
                start_week=base_weeks,
                end_week=base_weeks + build_weeks,
                duration_weeks=build_weeks,
                focus="Gradual intensity increase with maintained volume",
                description="Progressive intensity increase while maintaining volume. Introduce threshold and tempo work.",
                expected_outcomes=[
                    "Lactate threshold improvement",
                    "Increased sustainable pace",
                    "Strength development"
                ]
            ),
            Phase(
                name="Competition Preparation",
                start_week=base_weeks + build_weeks,
                end_week=base_weeks + build_weeks + peak_weeks,
                duration_weeks=peak_weeks,
                focus="Race-specific intensity and volume",
                description="High intensity, race-specific work. Practice goal pace/effort.",
                expected_outcomes=[
                    "VO2max improvement",
                    "Race-specific fitness",
                    "Peak performance readiness"
                ]
            ),
            Phase(
                name="Taper",
                start_week=base_weeks + build_weeks + peak_weeks,
                end_week=total_weeks,
                duration_weeks=taper_weeks,
                focus="Recovery and peak preparation",
                description="Reduced volume, maintained intensity. Arrive fresh for goal event.",
                expected_outcomes=[
                    "Full recovery and freshness",
                    "Maintained fitness",
                    "Peak performance"
                ]
            )
        ]

        return phases

    def _build_conjugate_periodization(
        self,
        goals: List[Goal],
        assessment: Assessment,
        total_weeks: int
    ) -> List[Phase]:
        """
        Build conjugate periodization for hybrid athletes

        Conjugate method trains multiple qualities simultaneously:
        - Max strength + speed/power on one day
        - Endurance + strength endurance on another
        - Recovery/skill work on third

        Best for hybrid athletes wanting concurrent development.
        """
        phases = []

        if total_weeks < 16:
            # Shorter cycles use simplified structure
            base_weeks = max(4, int(total_weeks * 0.3))
            build_weeks = int(total_weeks * 0.55)
            taper_weeks = total_weeks - base_weeks - build_weeks

            phases = [
                Phase(
                    name="General Physical Preparation (GPP)",
                    start_week=0,
                    end_week=base_weeks,
                    duration_weeks=base_weeks,
                    focus="Build general work capacity for hybrid training",
                    description="Balanced strength and endurance work. Develop movement quality.",
                    expected_outcomes=[
                        "General work capacity",
                        "Movement competency",
                        "Aerobic and strength base"
                    ]
                ),
                Phase(
                    name="Specific Physical Preparation (SPP)",
                    start_week=base_weeks,
                    end_week=base_weeks + build_weeks,
                    duration_weeks=build_weeks,
                    focus="Goal-specific hybrid development",
                    description="Concurrent training optimized to minimize interference. Strength + endurance progression.",
                    expected_outcomes=[
                        "Concurrent strength and endurance gains",
                        "Minimized interference effect",
                        "Goal-specific fitness"
                    ]
                ),
                Phase(
                    name="Competition Preparation",
                    start_week=base_weeks + build_weeks,
                    end_week=total_weeks,
                    duration_weeks=taper_weeks,
                    focus="Peak both strength and endurance",
                    description="Taper volume, maintain intensity in both domains.",
                    expected_outcomes=[
                        "Peak strength and endurance",
                        "Full recovery",
                        "Ready for competition or testing"
                    ]
                )
            ]
        else:
            # Longer cycles with multiple SPP blocks
            gpp_weeks = max(6, int(total_weeks * 0.25))
            spp_weeks = int(total_weeks * 0.6)
            comp_weeks = total_weeks - gpp_weeks - spp_weeks

            # Split SPP into 2 phases
            spp1_weeks = spp_weeks // 2
            spp2_weeks = spp_weeks - spp1_weeks

            phases = [
                Phase(
                    name="General Physical Preparation (GPP)",
                    start_week=0,
                    end_week=gpp_weeks,
                    duration_weeks=gpp_weeks,
                    focus="Build general work capacity",
                    description="Balanced strength and endurance. High volume, moderate intensity.",
                    expected_outcomes=[
                        "Work capacity development",
                        "Movement quality",
                        "Base fitness"
                    ]
                ),
                Phase(
                    name="Specific Physical Preparation 1",
                    start_week=gpp_weeks,
                    end_week=gpp_weeks + spp1_weeks,
                    duration_weeks=spp1_weeks,
                    focus="Initial strength emphasis with endurance maintenance",
                    description="Prioritize strength development while maintaining endurance.",
                    expected_outcomes=[
                        "Strength increase",
                        "Maintained aerobic fitness",
                        "Power development"
                    ]
                ),
                Phase(
                    name="Specific Physical Preparation 2",
                    start_week=gpp_weeks + spp1_weeks,
                    end_week=gpp_weeks + spp_weeks,
                    duration_weeks=spp2_weeks,
                    focus="Endurance emphasis with strength maintenance",
                    description="Shift focus to endurance while preserving strength gains.",
                    expected_outcomes=[
                        "Endurance peaking",
                        "Maintained strength",
                        "Concurrent fitness"
                    ]
                ),
                Phase(
                    name="Competition Preparation",
                    start_week=gpp_weeks + spp_weeks,
                    end_week=total_weeks,
                    duration_weeks=comp_weeks,
                    focus="Peak both domains",
                    description="Taper and prepare for goal event/test.",
                    expected_outcomes=[
                        "Peak performance",
                        "Full recovery",
                        "Balanced fitness"
                    ]
                )
            ]

        return phases

    def _build_undulating_periodization(
        self,
        goals: List[Goal],
        assessment: Assessment,
        total_weeks: int
    ) -> List[Phase]:
        """
        Build undulating periodization (DUP - Daily Undulating Periodization)

        Varies intensity and volume frequently (daily or weekly).
        Good for time-efficient training and avoiding monotony.
        """
        # For undulating, we still have macro phases but with more frequent variation
        return self._build_block_periodization(goals, assessment, total_weeks)

    def _build_short_cycle(
        self,
        goals: List[Goal],
        assessment: Assessment,
        total_weeks: int
    ) -> List[Phase]:
        """
        Build shortened cycle for timelines < 12 weeks

        Simplified structure due to time constraints
        """
        if total_weeks < 6:
            # Very short - just build and taper
            build_weeks = total_weeks - 1
            return [
                Phase(
                    name="Build",
                    start_week=0,
                    end_week=build_weeks,
                    duration_weeks=build_weeks,
                    focus="Rapid improvement",
                    description="Focused training to maximize gains in limited time.",
                    expected_outcomes=["Fitness improvement", "Skill development"]
                ),
                Phase(
                    name="Taper",
                    start_week=build_weeks,
                    end_week=total_weeks,
                    duration_weeks=1,
                    focus="Recovery",
                    description="Brief taper to arrive fresh.",
                    expected_outcomes=["Recovery", "Readiness"]
                )
            ]
        else:
            # 6-12 weeks - condensed base + build + taper
            base_weeks = 2
            build_weeks = total_weeks - 4
            taper_weeks = 2

            return [
                self._create_base_phase(0, base_weeks, goals),
                self._create_build_phase(base_weeks, base_weeks + build_weeks, goals, phase_num=1),
                self._create_taper_phase(base_weeks + build_weeks, total_weeks, goals)
            ]

    def _needs_base_building(self, assessment: Assessment, goals: List[Goal]) -> bool:
        """
        Determine if athlete needs extended base building phase

        Returns True if:
        - Recently detrained (>3 months off)
        - Beginner (<1 year training age)
        - Low current fitness
        - History of injuries
        """
        training_age = assessment.training_history.years_of_training
        detraining = assessment.training_history.detraining_period_months
        fitness = assessment.fitness_score or 50.0
        injuries = len(assessment.health.injuries)

        if detraining > 3:
            return True
        if training_age < 1:
            return True
        if fitness < 40:
            return True
        if injuries > 2:
            return True

        return False

    def _create_base_phase(self, start_week: int, end_week: int, goals: List[Goal]) -> Phase:
        """Create a base building phase"""
        duration = end_week - start_week

        # Customize based on goal type
        primary_goal = goals[0] if goals else None
        if primary_goal and primary_goal.type == GoalType.STRENGTH:
            focus_desc = "Build strength foundation and movement patterns"
            outcomes = [
                "Movement quality improvement",
                "Anatomical adaptation",
                "Work capacity development"
            ]
        else:
            focus_desc = "Build aerobic base and endurance foundation"
            outcomes = [
                "Aerobic capacity development",
                "Fat oxidation improvement",
                "Injury resilience"
            ]

        return Phase(
            name="Base Building",
            start_week=start_week,
            end_week=end_week,
            duration_weeks=duration,
            focus=focus_desc,
            description="Low to moderate intensity, higher volume. Build foundation for future intensity.",
            expected_outcomes=outcomes
        )

    def _create_build_phase(self, start_week: int, end_week: int, goals: List[Goal], phase_num: int = 1) -> Phase:
        """Create a build phase"""
        duration = end_week - start_week

        if phase_num == 1:
            name = "Build 1"
            focus = "Volume accumulation and threshold development"
            description = "Increase training volume. Introduce threshold and tempo work."
            outcomes = [
                "Increased training capacity",
                "Lactate threshold improvement",
                "Strength progression"
            ]
        elif phase_num == 2:
            name = "Build 2"
            focus = "Intensity development"
            description = "Maintain volume, increase intensity. More threshold and VO2max work."
            outcomes = [
                "VO2max improvement",
                "Higher sustainable pace/power",
                "Peak strength approaching"
            ]
        else:
            name = f"Build {phase_num}"
            focus = "Advanced preparation"
            description = "High intensity, race-specific work."
            outcomes = [
                "Race-specific fitness",
                "High performance capacity"
            ]

        return Phase(
            name=name,
            start_week=start_week,
            end_week=end_week,
            duration_weeks=duration,
            focus=focus,
            description=description,
            expected_outcomes=outcomes
        )

    def _create_peak_phase(self, start_week: int, end_week: int, goals: List[Goal]) -> Phase:
        """Create a peak/sharpening phase"""
        duration = end_week - start_week

        return Phase(
            name="Peak",
            start_week=start_week,
            end_week=end_week,
            duration_weeks=duration,
            focus="Race-specific preparation and final sharpening",
            description="High intensity, goal-specific workouts. Practice race pace/effort.",
            expected_outcomes=[
                "Peak fitness achieved",
                "Race-specific readiness",
                "Confidence building"
            ]
        )

    def _create_taper_phase(self, start_week: int, end_week: int, goals: List[Goal]) -> Phase:
        """Create a taper phase"""
        duration = end_week - start_week

        return Phase(
            name="Taper",
            start_week=start_week,
            end_week=end_week,
            duration_weeks=duration,
            focus="Recovery and freshness for goal event",
            description="Reduced volume (40-60% of peak), maintained intensity. Arrive fresh and ready.",
            expected_outcomes=[
                "Full recovery from training block",
                "Maintained or improved fitness",
                "Peak performance on goal day"
            ]
        )


def build_macrocycle(
    goals: List[Goal],
    assessment: Assessment,
    total_weeks: int,
    periodization_model: PeriodizationModel
) -> Macrocycle:
    """
    Convenience function to build macrocycle

    Args:
        goals: Training goals
        assessment: Current fitness assessment
        total_weeks: Total weeks in training cycle
        periodization_model: Type of periodization

    Returns:
        Macrocycle with phase structure
    """
    builder = MacrocycleBuilder()
    return builder.build(goals, assessment, total_weeks, periodization_model)
