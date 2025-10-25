# Hybrid Athlete Platform API - Usage Guide

## Quick Start

### 1. Install Dependencies

```bash
cd Training
pip install -r backend/requirements.txt
```

### 2. Start the API Server

```bash
python backend/app_simple.py
```

The API will start at: `http://localhost:8000`

### 3. View API Documentation

Open in your browser:
- **Interactive Docs (Swagger)**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### 4. Run Automated Tests

```bash
# In a new terminal (while API is running)
python test_api.py
```

This will test the complete workflow:
1. Register user
2. Create fitness assessment
3. Create training goal (sub-4:00 marathon)
4. Set constraints (7 hours/week, 4-5 sessions)
5. Generate training plan
6. View plan details
7. Log a workout
8. Get performance analysis
9. Adapt plan based on performance

---

## API Endpoints

### Authentication

**Register User**
```http
POST /api/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password123",
  "name": "John Doe"
}
```

**Login**
```http
POST /api/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password123"
}
```

Returns:
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "user_id": "uuid-here"
}
```

Use the token in subsequent requests:
```http
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

---

### Create Fitness Assessment

```http
POST /api/assessments
Authorization: Bearer <token>
Content-Type: application/json

{
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
  "training_history": {
    "years_of_training": 3.0,
    "recent_weekly_volume": 5.0
  },
  "health": {
    "injuries": [],
    "healthcare_clearance": true
  },
  "lifestyle": {
    "sleep_hours": 7.5,
    "sleep_quality": 4,
    "stress_level": 2
  }
}
```

---

### Create Training Goal

```http
POST /api/goals
Authorization: Bearer <token>
Content-Type: application/json

{
  "type": "endurance",
  "target_date": "2026-06-01T00:00:00",
  "priority": "primary",
  "endurance_goal": {
    "event": "marathon",
    "target_time_seconds": 14400.0,
    "required_pace_min_per_km": 5.687
  }
}
```

---

### Create Constraints

```http
POST /api/constraints
Authorization: Bearer <token>
Content-Type: application/json

{
  "time": {
    "sessions_per_week": {"min": 4, "max": 5},
    "total_weekly_hours": 7.0,
    "preferred_days": ["monday", "tuesday", "thursday", "saturday"]
  },
  "resources": {
    "training_locations": ["outdoor", "home_gym"],
    "equipment": {
      "outdoor_running": true,
      "dumbbells": true
    }
  }
}
```

---

### Generate Training Plan

```http
POST /api/plans/generate
Authorization: Bearer <token>
Content-Type: application/json

{
  "goal_ids": ["goal-uuid"],
  "assessment_id": "assessment-uuid",
  "constraint_id": "constraint-uuid"
}
```

Returns:
```json
{
  "plan_id": "plan-uuid",
  "message": "Training plan generated successfully!",
  "summary": {
    "duration_weeks": 16,
    "methodology": "polarized_training",
    "periodization": "block",
    "phases": 4,
    "total_sessions": 80,
    "start_date": "2025-10-25",
    "end_date": "2026-02-14"
  }
}
```

---

### Get Plan Summary

```http
GET /api/plans/{plan_id}/summary
Authorization: Bearer <token>
```

---

### Get Week Details

```http
GET /api/plans/{plan_id}/week/{week_number}
Authorization: Bearer <token>
```

Returns the microcycle with all sessions for that week.

---

### Log Workout

```http
POST /api/workouts/log
Authorization: Bearer <token>
Content-Type: application/json

{
  "session_id": "session-uuid",
  "workout_id": "workout-uuid",
  "duration_minutes": 45.0,
  "perceived_exertion": 6,
  "perceived_difficulty": "as_expected",
  "completion_quality": "full",
  "training_load": 50.0,
  "wellness": {
    "fatigue": 2,
    "soreness": 2,
    "mood": 4,
    "sleep_quality": 4,
    "stress": 2,
    "motivation": 4
  }
}
```

---

### Get Performance Analysis

```http
GET /api/plans/{plan_id}/performance
Authorization: Bearer <token>
```

Returns:
```json
{
  "completion_rate": 95.0,
  "average_difficulty_delta": 0.2,
  "volume_compliance": 98.0,
  "intensity_compliance": 102.0,
  "recovery_quality": 75.0,
  "acute_chronic_workload_ratio": 1.15,
  "training_monotony": 1.8,
  "trend": "improving",
  "logs_analyzed": 10
}
```

---

### Adapt Plan

```http
POST /api/plans/{plan_id}/adapt
Authorization: Bearer <token>
```

Returns:
```json
{
  "message": "Plan adapted successfully!",
  "logs_analyzed": 10,
  "recommendations_count": 2,
  "recommendations": [
    {
      "trigger": "injury_risk",
      "type": "meso",
      "severity": 85.0,
      "description": "High injury risk detected",
      "reasoning": "ACWR is 1.65, above safe threshold",
      "suggested_changes": {
        "volume_multiplier": 0.85,
        "extra_recovery_day": true
      }
    }
  ]
}
```

---

## Example Workflow (curl)

```bash
# 1. Register
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123","name":"Test User"}'

# Save the token
TOKEN="your-token-here"

# 2. Create assessment
curl -X POST http://localhost:8000/api/assessments \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"body_composition":{"weight":70,"height":175},...}'

# 3. Generate plan
curl -X POST http://localhost:8000/api/plans/generate \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"goal_ids":["..."],"assessment_id":"...","constraint_id":"..."}'

# 4. View plan
curl http://localhost:8000/api/plans/{plan_id}/summary \
  -H "Authorization: Bearer $TOKEN"
```

---

## Features

### ✅ Complete Training Intelligence

- **Plan Generation**: Generate personalized training plans based on goals, fitness, and constraints
- **Adaptive Intelligence**: Plans adapt based on real-world performance
- **Load Monitoring**: Tracks ACWR (Acute:Chronic Workload Ratio) for injury prevention
- **Performance Analysis**: Analyzes completion rate, difficulty, recovery quality
- **Smart Recommendations**: Provides actionable adaptation suggestions

### ✅ Research-Backed

- Gabbett (2016): ACWR for injury prevention
- Foster (1998): Training load monitoring
- Banister (1975): Fitness-fatigue model
- Multiple periodization models (Block, Linear, Conjugate, Undulating)

### ✅ Production Features

- JWT authentication
- In-memory storage (easily replaceable with PostgreSQL/MongoDB)
- Automatic API documentation (Swagger/ReDoc)
- CORS support
- Error handling

---

## Storage

Currently uses **in-memory storage** for easy testing. Data is lost when the server restarts.

For production, replace with:
- PostgreSQL for structured data (users, assessments, goals, constraints)
- MongoDB for flexible data (training plans, workouts)
- Redis for caching

---

## Next Steps

1. **Test the API**: Run `python test_api.py`
2. **Explore the docs**: Visit http://localhost:8000/docs
3. **Build a frontend**: Use the API to build a web/mobile app
4. **Add persistence**: Replace in-memory storage with real databases
5. **Deploy**: Deploy to cloud platform (AWS, GCP, Azure)

---

## Support

For issues or questions, check the `/docs` endpoint for full API documentation.
