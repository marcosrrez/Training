"""
Microcycle Creator

Generates individual weekly training plans (microcycles) within each mesocycle.

A microcycle is a single week of training that includes:
- Session allocation to specific days
- Hard/easy distribution
- Session type assignment (easy, moderate, hard, strength, rest)
- Optimal sequencing for concurrent training
- Recovery week modifications

Research basis:
- Hard/easy distribution: Seiler 2010, Billat 2001
- Concurrent training sequencing: Coffey & Hawley 2017, Wilson et al. 2012
- Recovery weeks: Aubry et al. 2014, Rønnestad et al. 2014
"""
from typing import List, Dict, Tuple
from datetime import date, timedelta
from enum import Enum

from core.models.training_plan import (
    Microcycle, Mesocycle, Session, SessionType, SessionCategory, Volume
)
from core.models.goal import Goal, GoalType
from core.models.constraint import Constraints, DayOfWeek
from core.models.assessment import Assessment


class MicrocycleCreator:
    """
    Creates weekly training plans (microcycles)
    """

    def __init__(self):
        # Day of week ordering for scheduling
        self.DAYS_OF_WEEK = [
            DayOfWeek.MONDAY,
            DayOfWeek.TUESDAY,
            DayOfWeek.WEDNESDAY,
            DayOfWeek.THURSDAY,
            DayOfWeek.FRIDAY,
            DayOfWeek.SATURDAY,
            DayOfWeek.SUNDAY
        ]

    def create(
        self,
        mesocycle: Mesocycle,
        goals: List[Goal],
        constraints: Constraints,
        assessment: Assessment,
        start_date: date
    ) -> List[Microcycle]:
        """
        Create all microcycles for a mesocycle

        Args:
            mesocycle: The mesocycle to break into weeks
            goals: Training goals
            constraints: Time and resource constraints
            assessment: User fitness assessment
            start_date: Start date of the training plan

        Returns:
            List of Microcycle objects (one per week)
        """
        microcycles = []

        # Calculate start date for this mesocycle
        mesocycle_start = start_date + timedelta(weeks=mesocycle.start_week)

        for week_offset in range(mesocycle.duration_weeks):
            week_number = mesocycle.start_week + week_offset
            week_start = mesocycle_start + timedelta(weeks=week_offset)

            # Determine if this is a recovery week
            is_recovery_week = self._is_recovery_week(
                week_offset=week_offset,
                recovery_frequency=mesocycle.recovery_frequency
            )

            # Create the microcycle
            microcycle = self._create_single_microcycle(
                week_number=week_number,
                week_start=week_start,
                mesocycle=mesocycle,
                goals=goals,
                constraints=constraints,
                assessment=assessment,
                is_recovery_week=is_recovery_week
            )

            microcycles.append(microcycle)

        return microcycles

    def _is_recovery_week(self, week_offset: int, recovery_frequency: int) -> bool:
        """
        Determine if this week is a recovery week

        Recovery weeks occur every N weeks (e.g., every 4th week)
        Week offset 0, 1, 2 = normal weeks
        Week offset 3 = recovery week (if frequency is 4)
        """
        if recovery_frequency <= 0:
            return False

        # Last week of each recovery cycle is a recovery week
        return (week_offset + 1) % recovery_frequency == 0

    def _create_single_microcycle(
        self,
        week_number: int,
        week_start: date,
        mesocycle: Mesocycle,
        goals: List[Goal],
        constraints: Constraints,
        assessment: Assessment,
        is_recovery_week: bool
    ) -> Microcycle:
        """
        Create a single week of training
        """
        # Determine session count for this week
        sessions_per_week = self._determine_session_count(
            constraints=constraints,
            is_recovery_week=is_recovery_week
        )

        # Allocate session types based on intensity distribution
        session_types = self._allocate_session_types(
            sessions_per_week=sessions_per_week,
            intensity_distribution=mesocycle.intensity_distribution,
            goals=goals,
            is_recovery_week=is_recovery_week
        )

        # Sequence sessions optimally across the week
        session_schedule = self._sequence_sessions(
            session_types=session_types,
            constraints=constraints,
            goals=goals
        )

        # Create Session objects
        sessions = []
        for day_offset, (session_type, session_category) in enumerate(session_schedule):
            if session_type == SessionType.REST:
                continue  # Don't create session objects for rest days

            session_date = week_start + timedelta(days=day_offset)

            session = Session(
                session_id=f"week{week_number}_day{day_offset}",
                date=session_date,
                type=session_type,
                category=session_category,
                workout_id=None,  # Will be populated by workout builder
                estimated_duration_minutes=self._estimate_session_duration(
                    session_type=session_type,
                    session_category=session_category,
                    constraints=constraints
                ),
                estimated_tss=self._estimate_tss(session_category),
                coaching_notes=self._generate_coaching_notes(
                    session_type=session_type,
                    session_category=session_category,
                    is_recovery_week=is_recovery_week,
                    week_number=week_number
                )
            )

            sessions.append(session)

        # Calculate weekly volume
        total_volume = self._calculate_weekly_volume(
            sessions=sessions,
            mesocycle_base_volume=mesocycle.base_weekly_volume,
            is_recovery_week=is_recovery_week
        )

        # Create microcycle
        microcycle = Microcycle(
            week_number=week_number,
            start_date=week_start,
            sessions=sessions,
            total_volume=total_volume,
            intensity_score=self._calculate_intensity_score(sessions),
            recovery_days=self._count_recovery_days(session_schedule),
            is_recovery_week=is_recovery_week
        )

        return microcycle

    def _determine_session_count(
        self,
        constraints: Constraints,
        is_recovery_week: bool
    ) -> int:
        """
        Determine how many sessions this week

        Recovery weeks typically have 1-2 fewer sessions
        """
        target_sessions = constraints.time.sessions_per_week.target or 5

        if is_recovery_week:
            # Reduce session count for recovery
            return max(3, target_sessions - 2)
        else:
            return target_sessions

    def _allocate_session_types(
        self,
        sessions_per_week: int,
        intensity_distribution,
        goals: List[Goal],
        is_recovery_week: bool
    ) -> List[Tuple[SessionType, SessionCategory]]:
        """
        Allocate session types and categories based on intensity distribution

        Returns list of (SessionType, SessionCategory) tuples
        """
        session_types = []

        # Determine primary goal type
        primary_goal = goals[0] if goals else None
        is_endurance_focus = primary_goal and primary_goal.type in [GoalType.ENDURANCE]
        is_strength_focus = primary_goal and primary_goal.type in [GoalType.STRENGTH]
        is_hybrid = primary_goal and primary_goal.type == GoalType.HYBRID

        if is_recovery_week:
            # Recovery week - mostly easy sessions
            for i in range(sessions_per_week):
                if is_hybrid and i < 2:
                    # Keep some strength in recovery weeks
                    session_types.append((SessionType.STRENGTH, SessionCategory.EASY))
                else:
                    session_types.append((SessionType.RUN, SessionCategory.EASY))
            return session_types

        # Normal week - distribute based on intensity distribution
        dist = intensity_distribution

        # Calculate how many easy vs moderate vs hard sessions
        easy_percentage = dist.zone_1_percentage + dist.zone_2_percentage
        moderate_percentage = dist.zone_3_percentage
        hard_percentage = dist.zone_4_percentage + dist.zone_5_percentage

        # Convert percentages to session counts
        easy_count = round(sessions_per_week * (easy_percentage / 100))
        moderate_count = round(sessions_per_week * (moderate_percentage / 100))
        hard_count = round(sessions_per_week * (hard_percentage / 100))

        # Ensure we have the right total
        total = easy_count + moderate_count + hard_count
        if total < sessions_per_week:
            easy_count += (sessions_per_week - total)
        elif total > sessions_per_week:
            easy_count -= (total - sessions_per_week)

        # For hybrid athletes, allocate some sessions to strength
        if is_hybrid:
            strength_sessions = min(2, sessions_per_week // 3)  # ~1/3 strength
            easy_count = max(1, easy_count - strength_sessions)

            for _ in range(strength_sessions):
                session_types.append((SessionType.STRENGTH, SessionCategory.MODERATE))

        # Add endurance sessions
        for _ in range(hard_count):
            session_types.append((SessionType.RUN, SessionCategory.HARD))

        for _ in range(moderate_count):
            session_types.append((SessionType.RUN, SessionCategory.MODERATE))

        for _ in range(easy_count):
            session_types.append((SessionType.RUN, SessionCategory.EASY))

        return session_types

    def _sequence_sessions(
        self,
        session_types: List[Tuple[SessionType, SessionCategory]],
        constraints: Constraints,
        goals: List[Goal]
    ) -> List[Tuple[SessionType, SessionCategory]]:
        """
        Sequence sessions optimally across the week

        Key principles:
        - Hard days should not be consecutive
        - Key workouts on preferred days (e.g., Sat for long run)
        - Strength and hard endurance separated by 6+ hours ideally
        - Rest days strategically placed

        Returns: List of 7 tuples (one per day), with REST for rest days
        """
        week_schedule = [(SessionType.REST, SessionCategory.RECOVERY)] * 7

        # Separate sessions by category
        hard_sessions = [s for s in session_types if s[1] == SessionCategory.HARD]
        moderate_sessions = [s for s in session_types if s[1] == SessionCategory.MODERATE]
        easy_sessions = [s for s in session_types if s[1] == SessionCategory.EASY]

        # Get preferred training days (if specified)
        preferred_days = constraints.time.preferred_days
        if not preferred_days:
            preferred_days = self.DAYS_OF_WEEK  # All days available

        # Convert preferred days to indices
        day_indices = []
        for pref_day in preferred_days:
            if pref_day == DayOfWeek.MONDAY:
                day_indices.append(0)
            elif pref_day == DayOfWeek.TUESDAY:
                day_indices.append(1)
            elif pref_day == DayOfWeek.WEDNESDAY:
                day_indices.append(2)
            elif pref_day == DayOfWeek.THURSDAY:
                day_indices.append(3)
            elif pref_day == DayOfWeek.FRIDAY:
                day_indices.append(4)
            elif pref_day == DayOfWeek.SATURDAY:
                day_indices.append(5)
            elif pref_day == DayOfWeek.SUNDAY:
                day_indices.append(6)

        if not day_indices:
            day_indices = list(range(7))  # All days

        # Strategy: Place hard sessions first with gaps between them
        # Typical pattern: Hard on Tue, Thu or Sat (if endurance)
        # Or: Strength Mon/Thu, Hard endurance Wed/Sat (if hybrid)

        is_hybrid = goals and goals[0].type == GoalType.HYBRID

        if is_hybrid:
            # Hybrid pattern: alternate strength and endurance
            # Mon: Strength, Tue: Easy, Wed: Hard Run, Thu: Strength, Fri: Easy, Sat: Long Run, Sun: Rest

            available_indices = [i for i in day_indices]

            # Place strength sessions (Monday, Thursday ideally)
            strength_sessions = [s for s in session_types if s[0] == SessionType.STRENGTH]
            for i, strength in enumerate(strength_sessions):
                if i == 0 and 0 in available_indices:  # Monday
                    week_schedule[0] = strength
                    available_indices.remove(0)
                elif i == 1 and 3 in available_indices:  # Thursday
                    week_schedule[3] = strength
                    available_indices.remove(3)
                elif available_indices:
                    # Place on first available day
                    day = available_indices.pop(0)
                    week_schedule[day] = strength

            # Place hard endurance sessions (Wed, Sat ideally)
            endurance_hard = [s for s in hard_sessions if s[0] != SessionType.STRENGTH]
            for i, hard in enumerate(endurance_hard):
                if i == 0 and 2 in available_indices:  # Wednesday
                    week_schedule[2] = hard
                    available_indices.remove(2)
                elif i == 1 and 5 in available_indices:  # Saturday (long run)
                    week_schedule[5] = hard
                    available_indices.remove(5)
                elif available_indices:
                    # Find day with gap from hard days
                    for day in available_indices:
                        if self._has_hard_neighbor(week_schedule, day):
                            continue
                        week_schedule[day] = hard
                        available_indices.remove(day)
                        break

            # Fill remaining with easy/moderate
            for session in moderate_sessions + easy_sessions:
                if available_indices:
                    day = available_indices.pop(0)
                    week_schedule[day] = session

        else:
            # Endurance-focused pattern
            # Tue: Hard, Thu: Moderate/Hard, Sat: Long Run, other days easy

            available_indices = [i for i in day_indices]

            # Place key long run on Saturday if available
            if hard_sessions and 5 in available_indices:
                week_schedule[5] = hard_sessions.pop(0)  # Saturday long run
                available_indices.remove(5)

            # Place remaining hard sessions with gaps
            hard_days_preference = [1, 3]  # Tuesday, Thursday
            for hard in hard_sessions:
                placed = False
                for pref_day in hard_days_preference:
                    if pref_day in available_indices:
                        week_schedule[pref_day] = hard
                        available_indices.remove(pref_day)
                        placed = True
                        break

                if not placed and available_indices:
                    # Find day without adjacent hard sessions
                    for day in available_indices:
                        if not self._has_hard_neighbor(week_schedule, day):
                            week_schedule[day] = hard
                            available_indices.remove(day)
                            break

            # Place moderate sessions
            for moderate in moderate_sessions:
                if available_indices:
                    day = available_indices.pop(0)
                    week_schedule[day] = moderate

            # Fill remaining with easy
            for easy in easy_sessions:
                if available_indices:
                    day = available_indices.pop(0)
                    week_schedule[day] = easy

        return week_schedule

    def _has_hard_neighbor(self, schedule: List, day_index: int) -> bool:
        """
        Check if a day has a hard session adjacent to it
        """
        for neighbor in [day_index - 1, day_index + 1]:
            if 0 <= neighbor < 7:
                session_type, category = schedule[neighbor]
                if category == SessionCategory.HARD:
                    return True
        return False

    def _estimate_session_duration(
        self,
        session_type: SessionType,
        session_category: SessionCategory,
        constraints: Constraints
    ) -> int:
        """
        Estimate session duration in minutes
        """
        typical_duration = constraints.time.session_duration_minutes.target or 45

        # Adjust based on category
        if session_category == SessionCategory.EASY:
            return int(typical_duration * 0.8)  # Shorter easy sessions
        elif session_category == SessionCategory.HARD:
            # Hard sessions can be longer (especially long runs)
            if session_type == SessionType.RUN:
                return int(typical_duration * 1.3)  # Long run
            else:
                return typical_duration
        else:
            return typical_duration

    def _estimate_tss(self, session_category: SessionCategory) -> float:
        """
        Estimate Training Stress Score

        Simple estimation:
        - Easy: 30-50 TSS
        - Moderate: 50-80 TSS
        - Hard: 80-120 TSS
        """
        if session_category == SessionCategory.EASY:
            return 40.0
        elif session_category == SessionCategory.MODERATE:
            return 65.0
        elif session_category == SessionCategory.HARD:
            return 100.0
        else:
            return 20.0  # Recovery

    def _generate_coaching_notes(
        self,
        session_type: SessionType,
        session_category: SessionCategory,
        is_recovery_week: bool,
        week_number: int
    ) -> str:
        """
        Generate coaching notes for the session
        """
        if is_recovery_week:
            return "Recovery week - keep intensity low, focus on feeling good and recovering."

        if session_category == SessionCategory.EASY:
            return "Easy effort - should be able to hold a conversation. Focus on form and enjoyment."
        elif session_category == SessionCategory.MODERATE:
            if session_type == SessionType.STRENGTH:
                return "Moderate strength session - focus on quality movement and progressive overload."
            else:
                return "Moderate effort - steady, controlled pace. Building aerobic endurance."
        elif session_category == SessionCategory.HARD:
            if session_type == SessionType.RUN:
                return "Key workout - give this one full focus and effort. Warm up well before intervals."
            elif session_type == SessionType.STRENGTH:
                return "Hard strength session - push for progressive overload while maintaining form."
            else:
                return "Hard effort - this is a key session for adaptation."
        else:
            return "Listen to your body and adjust as needed."

    def _calculate_weekly_volume(
        self,
        sessions: List[Session],
        mesocycle_base_volume: float,
        is_recovery_week: bool
    ) -> Volume:
        """
        Calculate total weekly training volume
        """
        # Sum estimated durations
        total_minutes = sum(s.estimated_duration_minutes for s in sessions)
        total_hours = total_minutes / 60.0

        # For recovery week, reduce by 40-60%
        if is_recovery_week:
            total_hours *= 0.6

        return Volume(
            total_duration_minutes=total_hours * 60,
            total_distance_miles=None,  # Will be calculated when workouts are populated
            running_volume=None,
            cycling_volume=None,
            strength_volume=None
        )

    def _calculate_intensity_score(self, sessions: List[Session]) -> float:
        """
        Calculate weekly intensity score (average TSS)
        """
        if not sessions:
            return 0.0

        total_tss = sum(s.estimated_tss or 0 for s in sessions)
        return total_tss / len(sessions) if sessions else 0.0

    def _count_recovery_days(
        self,
        session_schedule: List[Tuple[SessionType, SessionCategory]]
    ) -> int:
        """
        Count rest and easy days
        """
        count = 0
        for session_type, category in session_schedule:
            if session_type == SessionType.REST or category == SessionCategory.RECOVERY:
                count += 1
        return count


def create_microcycles(
    mesocycle: Mesocycle,
    goals: List[Goal],
    constraints: Constraints,
    assessment: Assessment,
    start_date: date
) -> List[Microcycle]:
    """
    Convenience function to create microcycles

    Args:
        mesocycle: Mesocycle to break into weeks
        goals: Training goals
        constraints: User constraints
        assessment: Fitness assessment
        start_date: Training plan start date

    Returns:
        List of Microcycle objects (weekly plans)
    """
    creator = MicrocycleCreator()
    return creator.create(mesocycle, goals, constraints, assessment, start_date)
