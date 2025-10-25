"""
API Test Script - Hybrid Athlete Platform

Tests the complete API workflow:
1. Register user
2. Create assessment
3. Create goal
4. Create constraints
5. Generate training plan
6. Log workouts
7. Adapt plan based on performance

Run the API first: python backend/app_simple.py
Then run this script: python test_api.py
"""

import requests
import json
from datetime import datetime, timedelta
from pprint import pprint

# API base URL
BASE_URL = "http://localhost:8000"

# Store IDs for cross-request use
user_token = None
assessment_id = None
goal_id = None
constraint_id = None
plan_id = None


def print_section(title):
    """Print section header"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def test_health():
    """Test health check"""
    print_section("1. Health Check")
    response = requests.get(f"{BASE_URL}/api/health")
    print(f"Status: {response.status_code}")
    pprint(response.json())
    return response.status_code == 200


def test_register():
    """Test user registration"""
    global user_token

    print_section("2. Register User")
    data = {
        "email": "test@example.com",
        "password": "testpass123",
        "name": "Test User"
    }

    response = requests.post(f"{BASE_URL}/api/auth/register", json=data)
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        result = response.json()
        user_token = result["access_token"]
        print(f"✓ User registered successfully!")
        print(f"  User ID: {result['user_id']}")
        print(f"  Token: {user_token[:20]}...")
        return True
    else:
        print(f"✗ Registration failed: {response.text}")
        return False


def test_create_assessment():
    """Test creating fitness assessment"""
    global assessment_id

    print_section("3. Create Fitness Assessment")

    headers = {"Authorization": f"Bearer {user_token}"}
    data = {
        "user_id": "will-be-set-by-server",
        "assessment_id": "will-be-set-by-server",
        "body_composition": {
            "weight": 70.0,
            "height": 175.0,
            "body_fat_percentage": 15.0
        },
        "endurance_metrics": {
            "vo2max": 50.0,
            "lactate_threshold": 0.85,
            "max_heart_rate": 190,
            "resting_heart_rate": 55
        },
        "strength_metrics": {
            "one_rep_maxes": {},
            "estimated": True
        },
        "training_history": {
            "years_of_training": 3.0,
            "recent_weekly_volume": 5.0,
            "detraining_period_months": 0.0
        },
        "health": {
            "injuries": [],
            "medical_conditions": [],
            "medications": [],
            "healthcare_clearance": True
        },
        "lifestyle": {
            "sleep_hours": 7.5,
            "sleep_quality": 4,
            "stress_level": 2,
            "work_type": "sedentary"
        }
    }

    response = requests.post(f"{BASE_URL}/api/assessments", headers=headers, json=data)
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        result = response.json()
        assessment_id = result["assessment_id"]
        print(f"✓ Assessment created!")
        print(f"  Assessment ID: {assessment_id}")
        return True
    else:
        print(f"✗ Assessment creation failed: {response.text}")
        return False


def test_create_goal():
    """Test creating training goal"""
    global goal_id

    print_section("4. Create Training Goal")

    headers = {"Authorization": f"Bearer {user_token}"}

    # Create a marathon goal (Sub-4:00 marathon in 16 weeks)
    target_date = datetime.now() + timedelta(weeks=16)

    data = {
        "goal_id": "will-be-set-by-server",
        "user_id": "will-be-set-by-server",
        "type": "endurance",
        "target_date": target_date.isoformat(),
        "priority": "primary",
        "endurance_goal": {
            "event": "marathon",
            "target_time_seconds": 14400.0,  # 4:00:00
            "required_pace_min_per_km": 5.687
        }
    }

    response = requests.post(f"{BASE_URL}/api/goals", headers=headers, json=data)
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        result = response.json()
        goal_id = result["goal_id"]
        print(f"✓ Goal created!")
        print(f"  Goal ID: {goal_id}")
        print(f"  Target: Sub-4:00 marathon in 16 weeks")
        return True
    else:
        print(f"✗ Goal creation failed: {response.text}")
        return False


def test_create_constraints():
    """Test creating training constraints"""
    global constraint_id

    print_section("5. Create Training Constraints")

    headers = {"Authorization": f"Bearer {user_token}"}

    data = {
        "user_id": "will-be-set-by-server",
        "constraint_id": "will-be-set-by-server",
        "time": {
            "sessions_per_week": {"min": 4, "max": 5, "target": 5},
            "session_duration_minutes": {"min": 45, "max": 90, "target": 60},
            "preferred_days": ["monday", "tuesday", "thursday", "saturday", "sunday"],
            "preferred_times": ["morning"],
            "schedule_consistency": "stable",
            "total_weekly_hours": 7.0
        },
        "resources": {
            "training_locations": ["outdoor", "home_gym"],
            "equipment": {
                "outdoor_running": True,
                "dumbbells": True,
                "dumbbell_max_weight": 50.0,
                "resistance_bands": True
            }
        },
        "personal": {
            "injury_risk_tolerance": "moderate",
            "progression_preference": "moderate",
            "complexity_preference": "moderate"
        }
    }

    response = requests.post(f"{BASE_URL}/api/constraints", headers=headers, json=data)
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        result = response.json()
        constraint_id = result["constraint_id"]
        print(f"✓ Constraints created!")
        print(f"  Constraint ID: {constraint_id}")
        print(f"  Available: 7 hours/week, 4-5 sessions")
        return True
    else:
        print(f"✗ Constraints creation failed: {response.text}")
        return False


def test_generate_plan():
    """Test generating training plan"""
    global plan_id

    print_section("6. Generate Training Plan")

    headers = {"Authorization": f"Bearer {user_token}"}

    data = {
        "goal_ids": [goal_id],
        "assessment_id": assessment_id,
        "constraint_id": constraint_id
    }

    print("Generating plan... (this may take a few seconds)")
    response = requests.post(f"{BASE_URL}/api/plans/generate", headers=headers, json=data)
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        result = response.json()
        plan_id = result["plan_id"]
        summary = result["summary"]

        print(f"\n✓ Plan generated successfully!")
        print(f"  Plan ID: {plan_id}")
        print(f"\n  Summary:")
        print(f"    Duration: {summary['duration_weeks']} weeks")
        print(f"    Methodology: {summary['methodology']}")
        print(f"    Periodization: {summary['periodization']}")
        print(f"    Phases: {summary['phases']}")
        print(f"    Total Sessions: {summary['total_sessions']}")
        print(f"    Start: {summary['start_date']}")
        print(f"    End: {summary['end_date']}")
        return True
    else:
        print(f"✗ Plan generation failed: {response.text}")
        return False


def test_get_plan_summary():
    """Test getting plan summary"""
    print_section("7. Get Plan Summary")

    headers = {"Authorization": f"Bearer {user_token}"}

    response = requests.get(f"{BASE_URL}/api/plans/{plan_id}/summary", headers=headers)
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        result = response.json()
        print(f"\n✓ Plan summary retrieved!")
        print(f"\n  Phases:")
        for phase in result["phases"]:
            print(f"    • {phase['name']}: Weeks {phase['weeks']} ({phase['duration']} weeks)")
            print(f"      Focus: {phase['focus']}")
        return True
    else:
        print(f"✗ Failed to get plan summary: {response.text}")
        return False


def test_get_week():
    """Test getting a specific week"""
    print_section("8. Get Week 1 Details")

    headers = {"Authorization": f"Bearer {user_token}"}

    response = requests.get(f"{BASE_URL}/api/plans/{plan_id}/week/0", headers=headers)
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        week = response.json()
        print(f"\n✓ Week 0 retrieved!")
        print(f"  Sessions: {len(week['sessions'])}")
        print(f"  Recovery Week: {week['is_recovery_week']}")
        print(f"\n  Session Schedule:")
        for i, session in enumerate(week['sessions'][:3], 1):  # Show first 3
            print(f"    {i}. {session['date']}: {session['type']} - {session['category']}")
            print(f"       Duration: {session['estimated_duration_minutes']} min")
        if len(week['sessions']) > 3:
            print(f"    ... and {len(week['sessions']) - 3} more sessions")
        return True
    else:
        print(f"✗ Failed to get week: {response.text}")
        return False


def test_log_workout():
    """Test logging a workout"""
    print_section("9. Log Completed Workout")

    headers = {"Authorization": f"Bearer {user_token}"}

    # Get first session from week 0
    response = requests.get(f"{BASE_URL}/api/plans/{plan_id}/week/0", headers=headers)
    if response.status_code != 200:
        print("✗ Couldn't get week data")
        return False

    week = response.json()
    session = week['sessions'][0]

    # Log the workout
    data = {
        "log_id": "will-be-set-by-server",
        "user_id": "will-be-set-by-server",
        "session_id": session['session_id'],
        "workout_id": session.get('workout_id', 'workout_001'),
        "duration_minutes": float(session['estimated_duration_minutes']),
        "perceived_exertion": 6,
        "perceived_difficulty": "as_expected",
        "completion_quality": "full",
        "training_load": session.get('estimated_tss', 50.0),
        "wellness": {
            "fatigue": 2,
            "soreness": 2,
            "mood": 4,
            "sleep_quality": 4,
            "stress": 2,
            "motivation": 4
        }
    }

    response = requests.post(f"{BASE_URL}/api/workouts/log", headers=headers, json=data)
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        result = response.json()
        print(f"\n✓ Workout logged successfully!")
        print(f"  Log ID: {result['log_id']}")
        print(f"  Session: {session['type']} - {session['category']}")
        return True
    else:
        print(f"✗ Workout logging failed: {response.text}")
        return False


def test_performance_analysis():
    """Test performance analysis"""
    print_section("10. Get Performance Analysis")

    headers = {"Authorization": f"Bearer {user_token}"}

    response = requests.get(f"{BASE_URL}/api/plans/{plan_id}/performance", headers=headers)
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        result = response.json()
        print(f"\n✓ Performance analysis retrieved!")
        print(f"\n  Metrics:")
        print(f"    Completion Rate: {result['completion_rate']}%")
        print(f"    Difficulty Delta: {result['average_difficulty_delta']}")
        print(f"    Volume Compliance: {result['volume_compliance']}%")
        print(f"    Recovery Quality: {result['recovery_quality']}%")
        print(f"    ACWR: {result['acute_chronic_workload_ratio']}")
        print(f"    Trend: {result['trend']}")
        print(f"    Logs Analyzed: {result['logs_analyzed']}")
        return True
    else:
        print(f"✗ Performance analysis failed: {response.text}")
        return False


def test_adapt_plan():
    """Test plan adaptation"""
    print_section("11. Adapt Plan Based on Performance")

    headers = {"Authorization": f"Bearer {user_token}"}

    response = requests.post(f"{BASE_URL}/api/plans/{plan_id}/adapt", headers=headers)
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        result = response.json()
        print(f"\n✓ Plan adapted successfully!")
        print(f"  Logs Analyzed: {result['logs_analyzed']}")
        print(f"  Recommendations: {result['recommendations_count']}")

        if result['recommendations']:
            print(f"\n  Adaptation Recommendations:")
            for i, rec in enumerate(result['recommendations'], 1):
                print(f"\n    {i}. {rec['trigger'].upper()}")
                print(f"       Type: {rec['type']}")
                print(f"       Severity: {rec['severity']}%")
                print(f"       Description: {rec['description']}")
                print(f"       Changes: {rec['suggested_changes']}")
        else:
            print(f"\n  No adaptations needed - plan is on track!")

        return True
    else:
        print(f"✗ Plan adaptation failed: {response.text}")
        return False


def run_all_tests():
    """Run all API tests"""
    print("\n" + "=" * 80)
    print("  HYBRID ATHLETE PLATFORM - API TEST SUITE")
    print("=" * 80)

    tests = [
        ("Health Check", test_health),
        ("User Registration", test_register),
        ("Create Assessment", test_create_assessment),
        ("Create Goal", test_create_goal),
        ("Create Constraints", test_create_constraints),
        ("Generate Plan", test_generate_plan),
        ("Get Plan Summary", test_get_plan_summary),
        ("Get Week Details", test_get_week),
        ("Log Workout", test_log_workout),
        ("Performance Analysis", test_performance_analysis),
        ("Adapt Plan", test_adapt_plan),
    ]

    results = []
    for name, test_func in tests:
        try:
            success = test_func()
            results.append((name, success))
        except Exception as e:
            print(f"\n✗ Test failed with exception: {e}")
            results.append((name, False))

    # Print summary
    print_section("TEST SUMMARY")
    passed = sum(1 for _, success in results if success)
    total = len(results)

    for name, success in results:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"  {status}: {name}")

    print(f"\n  Total: {passed}/{total} tests passed")

    if passed == total:
        print("\n  🎉 ALL TESTS PASSED!")
    else:
        print(f"\n  ⚠️  {total - passed} test(s) failed")

    print("=" * 80 + "\n")


if __name__ == "__main__":
    print("\nMake sure the API is running at http://localhost:8000")
    print("Start it with: python backend/app_simple.py\n")

    input("Press Enter to start testing...")

    run_all_tests()
