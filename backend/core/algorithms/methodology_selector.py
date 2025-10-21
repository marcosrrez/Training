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

Research basis:
- Polarized: Seiler & Kjerland 2006, Stoggl et al. 2014
- Norwegian: Tønnessen et al. 2014, Rønnestad et al. 2014
- MAF: Maffetone & Laursen 2017
- HIIT: Gibala et al. 2012, Buchheit & Laursen 2013
- Concurrent: Wilson et al. 2012, Coffey & Hawley 2009
"""
from typing import List, Dict, Tuple
from core.models.goal import Goal, GoalType
from core.models.assessment import Assessment
from core.models.constraint import Constraints
from core.models.training_plan import Methodology, IntensityDistribution, PeriodizationModel


class MethodologySelector:
    """
    Selects optimal training methodology based on user context
    """

    def __init__(self):
        # Define available methodologies with their characteristics
        self.methodologies = {
            "polarized_training": {
                "name": "Polarized Training (80/20)",
                "description": "80% easy volume, 20% high intensity. Minimizes moderate 'gray zone' work.",
                "intensity_distribution": IntensityDistribution(
                    zone_1_percentage=50.0,  # Easy aerobic
                    zone_2_percentage=30.0,  # Aerobic
                    zone_3_percentage=5.0,   # Moderate (minimal)
                    zone_4_percentage=10.0,  # Threshold
                    zone_5_percentage=5.0    # VO2max intervals
                ),
                "periodization": PeriodizationModel.BLOCK,
                "min_weekly_hours": 4.0,
                "min_training_age": 0.0,  # Suitable for all
                "best_for": ["endurance", "hybrid"],
                "research": ["seiler_2006_polarized_training", "stoggl_2014_polarized_vs_threshold"]
            },
            "norwegian_method": {
                "name": "Norwegian Method",
                "description": "High volume easy + frequent threshold sessions. Double-threshold days.",
                "intensity_distribution": IntensityDistribution(
                    zone_1_percentage=45.0,
                    zone_2_percentage=30.0,
                    zone_3_percentage=5.0,
                    zone_4_percentage=15.0,  # More threshold work
                    zone_5_percentage=5.0
                ),
                "periodization": PeriodizationModel.BLOCK,
                "min_weekly_hours": 6.0,  # Requires higher volume
                "min_training_age": 2.0,  # Intermediate+
                "best_for": ["endurance"],
                "research": ["tonnessen_2014_norwegian_method", "ronnestad_2014_threshold"]
            },
            "maf_method": {
                "name": "MAF Method (Maximum Aerobic Function)",
                "description": "Heart rate-capped aerobic training. Build aerobic base before intensity.",
                "intensity_distribution": IntensityDistribution(
                    zone_1_percentage=60.0,
                    zone_2_percentage=40.0,
                    zone_3_percentage=0.0,   # No moderate
                    zone_4_percentage=0.0,   # No threshold (initially)
                    zone_5_percentage=0.0    # No high intensity (initially)
                ),
                "periodization": PeriodizationModel.LINEAR,
                "min_weekly_hours": 3.0,
                "min_training_age": 0.0,
                "best_for": ["endurance", "base_building"],
                "research": ["maffetone_2017_aerobic_training"]
            },
            "time_efficient_hiit": {
                "name": "Time-Efficient HIIT",
                "description": "Short, intense intervals for maximum adaptation per minute.",
                "intensity_distribution": IntensityDistribution(
                    zone_1_percentage=30.0,
                    zone_2_percentage=20.0,
                    zone_3_percentage=10.0,
                    zone_4_percentage=20.0,
                    zone_5_percentage=20.0   # High proportion of intense work
                ),
                "periodization": PeriodizationModel.UNDULATING,
                "min_weekly_hours": 2.0,
                "min_training_age": 1.0,  # Need some base fitness
                "best_for": ["endurance", "general_fitness"],
                "research": ["gibala_2012_hiit", "buchheit_2013_hiit"]
            },
            "hybrid_concurrent": {
                "name": "Hybrid Concurrent Training",
                "description": "Optimized strength + endurance with minimal interference.",
                "intensity_distribution": IntensityDistribution(
                    zone_1_percentage=40.0,
                    zone_2_percentage=25.0,
                    zone_3_percentage=10.0,
                    zone_4_percentage=15.0,
                    zone_5_percentage=10.0
                ),
                "periodization": PeriodizationModel.CONJUGATE,
                "min_weekly_hours": 5.0,
                "min_training_age": 1.0,
                "best_for": ["hybrid", "strength"],
                "research": ["wilson_2012_concurrent_training_meta", "coffey_2009_molecular_interference"]
            },
            "pyramidal": {
                "name": "Pyramidal Training",
                "description": "Traditional approach: 70% easy, 20% moderate, 10% high.",
                "intensity_distribution": IntensityDistribution(
                    zone_1_percentage=40.0,
                    zone_2_percentage=30.0,
                    zone_3_percentage=20.0,  # More moderate work
                    zone_4_percentage=7.0,
                    zone_5_percentage=3.0
                ),
                "periodization": PeriodizationModel.LINEAR,
                "min_weekly_hours": 3.0,
                "min_training_age": 0.0,
                "best_for": ["endurance", "general_fitness"],
                "research": ["esteve_lanao_2007_intensity_distribution"]
            }
        }

    def select(
        self,
        goals: List[Goal],
        assessment: Assessment,
        constraints: Constraints,
        user_preference: str = "auto"
    ) -> Methodology:
        """
        Select best methodology for user context

        Args:
            goals: User's training goals
            assessment: Current fitness assessment
            constraints: Time and resource constraints
            user_preference: User's explicit methodology preference or "auto"

        Returns:
            Methodology object with selected approach
        """
        # If user has explicit preference (and it's valid), validate and use it
        if user_preference != "auto" and user_preference in self.methodologies:
            if self._validate_methodology(user_preference, assessment, constraints):
                return self._create_methodology_object(user_preference)
            else:
                # User preference not suitable, explain why and fall back to auto
                print(f"⚠️  User preference '{user_preference}' not suitable for current context. Auto-selecting.")

        # Score all methodologies
        scores = self._score_all_methodologies(goals, assessment, constraints)

        # Select highest scoring methodology
        best_methodology = max(scores, key=scores.get)

        return self._create_methodology_object(best_methodology)

    def _score_all_methodologies(
        self,
        goals: List[Goal],
        assessment: Assessment,
        constraints: Constraints
    ) -> Dict[str, float]:
        """
        Score each methodology based on user context

        Scoring factors (0-1 scale each):
        1. Goal alignment: How well does this method support the goal types?
        2. Time availability: Does user have enough time for this method?
        3. Training age: Is user experienced enough?
        4. Fitness level: Is this appropriate for their fitness?
        5. Injury history: Is this safe given injury history?

        Returns:
            Dictionary of {methodology_name: score}
        """
        scores = {}

        for method_name, method_info in self.methodologies.items():
            score = 0.0
            weight_total = 0.0

            # Factor 1: Goal alignment (weight: 0.35)
            goal_score = self._score_goal_alignment(goals, method_info)
            score += goal_score * 0.35
            weight_total += 0.35

            # Factor 2: Time availability (weight: 0.25)
            time_score = self._score_time_availability(constraints, method_info)
            score += time_score * 0.25
            weight_total += 0.25

            # Factor 3: Training age (weight: 0.20)
            experience_score = self._score_training_experience(assessment, method_info)
            score += experience_score * 0.20
            weight_total += 0.20

            # Factor 4: Fitness level (weight: 0.10)
            fitness_score = self._score_fitness_level(assessment, method_info)
            score += fitness_score * 0.10
            weight_total += 0.10

            # Factor 5: Injury safety (weight: 0.10)
            safety_score = self._score_injury_safety(assessment, method_info)
            score += safety_score * 0.10
            weight_total += 0.10

            # Normalize score
            final_score = score / weight_total if weight_total > 0 else 0.0
            scores[method_name] = final_score

        return scores

    def _score_goal_alignment(self, goals: List[Goal], method_info: Dict) -> float:
        """
        Score how well methodology aligns with user goals (0-1)
        """
        if not goals:
            return 0.5  # Neutral if no goals

        goal_types = [g.type.value for g in goals]
        best_for = method_info["best_for"]

        # Calculate overlap
        matches = sum(1 for gt in goal_types if gt in best_for)
        alignment = matches / len(goal_types)

        # Bonus for perfect match
        if alignment == 1.0:
            alignment = 1.0

        # Penalty for mismatch
        if alignment == 0.0:
            alignment = 0.3  # Not ideal but not impossible

        return alignment

    def _score_time_availability(self, constraints: Constraints, method_info: Dict) -> float:
        """
        Score based on time availability (0-1)
        """
        available_hours = constraints.time.total_weekly_hours or 4.0
        required_hours = method_info["min_weekly_hours"]

        if available_hours >= required_hours * 1.2:
            # Plenty of time
            return 1.0
        elif available_hours >= required_hours:
            # Just enough time
            return 0.8
        elif available_hours >= required_hours * 0.8:
            # Slightly less than ideal, but workable
            return 0.6
        else:
            # Not enough time for this methodology
            ratio = available_hours / required_hours
            return max(0.2, ratio)  # Minimum 0.2 (possible but not recommended)

    def _score_training_experience(self, assessment: Assessment, method_info: Dict) -> float:
        """
        Score based on training age / experience (0-1)
        """
        training_age = assessment.training_history.years_of_training
        required_age = method_info["min_training_age"]

        if training_age >= required_age * 1.5:
            # Well above requirements
            return 1.0
        elif training_age >= required_age:
            # Meets requirements
            return 0.9
        elif training_age >= required_age * 0.7:
            # Slightly below, but manageable
            return 0.7
        else:
            # Below requirements
            if required_age == 0:
                return 1.0  # No requirement
            ratio = training_age / required_age if required_age > 0 else 1.0
            return max(0.3, ratio)

    def _score_fitness_level(self, assessment: Assessment, method_info: Dict) -> float:
        """
        Score based on current fitness level (0-1)

        Higher fitness = better suited for advanced methods
        """
        fitness_score = assessment.fitness_score or 50.0  # Default to middle

        # Normalize fitness score (0-100 → 0-1)
        normalized_fitness = fitness_score / 100.0

        # Some methods work better at different fitness levels
        method_name = method_info["name"]

        if "HIIT" in method_name or "Norwegian" in method_name:
            # Advanced methods - prefer higher fitness
            if normalized_fitness > 0.6:
                return 1.0
            else:
                return normalized_fitness * 1.2  # Slight bonus for trying

        elif "MAF" in method_name:
            # MAF good for beginners and recovery
            if normalized_fitness < 0.4:
                return 1.0
            elif normalized_fitness < 0.6:
                return 0.9
            else:
                return 0.7  # Still works, but less optimal

        else:
            # Polarized, Pyramidal, Hybrid work across all levels
            return 0.8 + (normalized_fitness * 0.2)  # 0.8-1.0 range

    def _score_injury_safety(self, assessment: Assessment, method_info: Dict) -> float:
        """
        Score based on injury history and method safety (0-1)
        """
        injury_count = len(assessment.health.injuries)
        current_injuries = [i for i in assessment.health.injuries if i.status == "current"]

        # If current injuries, very conservative
        if current_injuries:
            # Only MAF or very conservative methods
            if "MAF" in method_info["name"]:
                return 1.0
            elif "Polarized" in method_info["name"]:
                return 0.7
            else:
                return 0.4

        # If injury history, prefer lower impact methods
        if injury_count > 2:
            if "MAF" in method_info["name"] or "Polarized" in method_info["name"]:
                return 0.9
            elif "HIIT" in method_info["name"]:
                return 0.5  # HIIT can be high injury risk
            else:
                return 0.7

        # No injury concerns
        return 1.0

    def _validate_methodology(
        self,
        methodology_name: str,
        assessment: Assessment,
        constraints: Constraints
    ) -> bool:
        """
        Validate if a methodology is suitable for user

        Returns True if suitable, False otherwise
        """
        if methodology_name not in self.methodologies:
            return False

        method_info = self.methodologies[methodology_name]

        # Check time availability
        available_hours = constraints.time.total_weekly_hours or 4.0
        required_hours = method_info["min_weekly_hours"]
        if available_hours < required_hours * 0.7:
            return False  # Not enough time

        # Check training age
        training_age = assessment.training_history.years_of_training
        required_age = method_info["min_training_age"]
        if training_age < required_age * 0.5:
            return False  # Not experienced enough

        # Check for current injuries with high-intensity methods
        current_injuries = [i for i in assessment.health.injuries if i.status == "current"]
        if current_injuries and "HIIT" in methodology_name:
            return False  # HIIT not safe with current injuries

        return True

    def _create_methodology_object(self, methodology_name: str) -> Methodology:
        """
        Create a Methodology object from methodology name
        """
        method_info = self.methodologies[methodology_name]

        return Methodology(
            name=methodology_name,
            description=method_info["description"],
            periodization_model=method_info["periodization"],
            intensity_distribution=method_info["intensity_distribution"]
        )

    def get_methodology_explanation(self, methodology: Methodology) -> str:
        """
        Get detailed explanation of why this methodology was selected

        Returns human-readable explanation
        """
        method_info = self.methodologies.get(methodology.name)
        if not method_info:
            return "Selected methodology based on your goals and constraints."

        explanation = f"""
**Selected Methodology: {method_info['name']}**

{method_info['description']}

**Intensity Distribution:**
- Zone 1-2 (Easy/Aerobic): {methodology.intensity_distribution.zone_1_percentage + methodology.intensity_distribution.zone_2_percentage:.0f}%
- Zone 3 (Moderate): {methodology.intensity_distribution.zone_3_percentage:.0f}%
- Zone 4 (Threshold): {methodology.intensity_distribution.zone_4_percentage:.0f}%
- Zone 5 (VO2max): {methodology.intensity_distribution.zone_5_percentage:.0f}%

**Why This Works for You:**
- Aligns with your training goals
- Fits within your time constraints
- Appropriate for your experience level
- Backed by research: {', '.join(method_info['research'])}

**Weekly Commitment:**
Minimum {method_info['min_weekly_hours']:.1f} hours per week
"""
        return explanation.strip()


def select_optimal_methodology(
    goals: List[Goal],
    assessment: Assessment,
    constraints: Constraints,
    user_preference: str = "auto"
) -> Methodology:
    """
    Convenience function to select methodology

    Args:
        goals: User's training goals
        assessment: Current fitness assessment
        constraints: Time and resource constraints
        user_preference: User's explicit preference or "auto"

    Returns:
        Selected Methodology object

    Example:
        >>> from core.models.goal import Goal, GoalType, EnduranceGoal
        >>> from core.models.assessment import Assessment
        >>> from core.models.constraint import Constraints, TimeConstraints, SessionRange
        >>>
        >>> goal = Goal(
        ...     goal_id="g1",
        ...     user_id="u1",
        ...     type=GoalType.ENDURANCE,
        ...     target_date=datetime.now() + timedelta(weeks=20),
        ...     endurance_goal=EnduranceGoal(event="half_marathon", target_time_seconds=5400)
        ... )
        >>>
        >>> assessment = Assessment(
        ...     user_id="u1",
        ...     assessment_id="a1",
        ...     body_composition=BodyComposition(weight=180),
        ...     training_history=TrainingHistory(years_of_training=2)
        ... )
        >>>
        >>> constraints = Constraints(
        ...     user_id="u1",
        ...     constraint_id="c1",
        ...     time=TimeConstraints(
        ...         sessions_per_week=SessionRange(min=4, max=6),
        ...         session_duration_minutes=SessionRange(min=30, max=60),
        ...         total_weekly_hours=5.0
        ...     )
        ... )
        >>>
        >>> methodology = select_optimal_methodology(goals=[goal], assessment=assessment, constraints=constraints)
        >>> print(methodology.name)
        'polarized_training'
    """
    selector = MethodologySelector()
    return selector.select(goals, assessment, constraints, user_preference)
