"""
Simple FastAPI Application - Hybrid Athlete Platform
Self-contained version with in-memory storage for immediate testing

Run with: python app_simple.py
Or: uvicorn app_simple:app --reload

API will be available at: http://localhost:8000
Interactive docs at: http://localhost:8000/docs
"""

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime, timedelta, date
import jwt
import uuid

from core.models.user import User, UserProfile
from core.models.assessment import Assessment
from core.models.goal import Goal
from core.models.constraint import Constraints
from core.models.training_plan import TrainingPlan
from core.models.workout_log import WorkoutLog

from core.algorithms.plan_generator import generate_training_plan
from core.algorithms.adaptation_engine import analyze_and_adapt, AdaptationEngine

# ============================================================================
# In-Memory Storage
# ============================================================================

users_db: Dict[str, User] = {}
assessments_db: Dict[str, Assessment] = {}
goals_db: Dict[str, Goal] = {}
constraints_db: Dict[str, Constraints] = {}
plans_db: Dict[str, TrainingPlan] = {}
workout_logs_db: Dict[str, WorkoutLog] = {}

# ============================================================================
# Configuration
# ============================================================================

SECRET_KEY = "dev-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 24 hours for testing

# ============================================================================
# FastAPI Application
# ============================================================================

app = FastAPI(
    title="Hybrid Athlete Platform API",
    description="Intelligent training platform with adaptive intelligence - Simple Version",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer(auto_error=False)

# ============================================================================
# Request/Response Models
# ============================================================================

class RegisterRequest(BaseModel):
    email: str
    password: str
    name: str

class LoginRequest(BaseModel):
    email: str
    password: str

class GeneratePlanRequest(BaseModel):
    goal_ids: List[str]
    assessment_id: str
    constraint_id: str

# ============================================================================
# Authentication Functions
# ============================================================================

def create_access_token(data: dict):
    """Create JWT access token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> str:
    """Verify JWT token and return user_id"""
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
        return user_id
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")


# ============================================================================
# Root & Health Endpoints
# ============================================================================

@app.get("/", tags=["Health"])
async def root():
    """API root endpoint"""
    return {
        "message": "Hybrid Athlete Platform API - Simple Version",
        "version": "1.0.0",
        "status": "operational",
        "docs": "/docs",
        "endpoints": {
            "register": "POST /api/auth/register",
            "login": "POST /api/auth/login",
            "generate_plan": "POST /api/plans/generate",
            "log_workout": "POST /api/workouts/log",
            "adapt_plan": "POST /api/plans/{plan_id}/adapt"
        }
    }


@app.get("/api/health", tags=["Health"])
async def health_check():
    """Health check with database stats"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "storage": {
            "users": len(users_db),
            "assessments": len(assessments_db),
            "goals": len(goals_db),
            "constraints": len(constraints_db),
            "plans": len(plans_db),
            "workout_logs": len(workout_logs_db)
        }
    }


# ============================================================================
# Authentication Endpoints
# ============================================================================

@app.post("/api/auth/register", tags=["Authentication"])
async def register(request: RegisterRequest):
    """Register a new user"""
    # Check if user exists
    if any(u.email == request.email for u in users_db.values()):
        raise HTTPException(status_code=400, detail="Email already registered")

    # Create user
    user_id = str(uuid.uuid4())
    user = User(
        id=user_id,
        email=request.email,
        profile=UserProfile(
            name=request.name,
            date_of_birth=None,
            gender=None
        )
    )
    users_db[user_id] = user

    # Create access token
    access_token = create_access_token(data={"sub": user_id})

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user_id,
        "message": f"User {request.name} registered successfully"
    }


@app.post("/api/auth/login", tags=["Authentication"])
async def login(request: LoginRequest):
    """Login existing user"""
    # Find user
    user = next((u for u in users_db.values() if u.email == request.email), None)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Create access token
    access_token = create_access_token(data={"sub": user.id})

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user.id,
        "message": f"Welcome back, {user.profile.name}!"
    }


# ============================================================================
# User Endpoints
# ============================================================================

@app.get("/api/users/me", tags=["Users"])
async def get_current_user(user_id: str = Depends(verify_token)):
    """Get current user profile"""
    user = users_db.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


# ============================================================================
# Assessment Endpoints
# ============================================================================

@app.post("/api/assessments", tags=["Assessments"], response_model=dict)
async def create_assessment(assessment: Assessment, user_id: str = Depends(verify_token)):
    """Create a new fitness assessment"""
    assessment.user_id = user_id
    assessment.assessment_id = str(uuid.uuid4())
    assessment.completed_at = datetime.utcnow()

    assessments_db[assessment.assessment_id] = assessment

    return {
        "assessment_id": assessment.assessment_id,
        "message": "Assessment created successfully"
    }


@app.get("/api/assessments/{assessment_id}", tags=["Assessments"])
async def get_assessment(assessment_id: str, user_id: str = Depends(verify_token)):
    """Get assessment by ID"""
    assessment = assessments_db.get(assessment_id)
    if not assessment or assessment.user_id != user_id:
        raise HTTPException(status_code=404, detail="Assessment not found")
    return assessment


@app.get("/api/assessments", tags=["Assessments"])
async def list_assessments(user_id: str = Depends(verify_token)):
    """List all assessments for user"""
    user_assessments = [a for a in assessments_db.values() if a.user_id == user_id]
    return {"assessments": user_assessments, "count": len(user_assessments)}


# ============================================================================
# Goal Endpoints
# ============================================================================

@app.post("/api/goals", tags=["Goals"])
async def create_goal(goal: Goal, user_id: str = Depends(verify_token)):
    """Create a new training goal"""
    goal.user_id = user_id
    goal.goal_id = str(uuid.uuid4())

    goals_db[goal.goal_id] = goal

    return {
        "goal_id": goal.goal_id,
        "message": "Goal created successfully"
    }


@app.get("/api/goals/{goal_id}", tags=["Goals"])
async def get_goal(goal_id: str, user_id: str = Depends(verify_token)):
    """Get goal by ID"""
    goal = goals_db.get(goal_id)
    if not goal or goal.user_id != user_id:
        raise HTTPException(status_code=404, detail="Goal not found")
    return goal


@app.get("/api/goals", tags=["Goals"])
async def list_goals(user_id: str = Depends(verify_token)):
    """List all goals for user"""
    user_goals = [g for g in goals_db.values() if g.user_id == user_id]
    return {"goals": user_goals, "count": len(user_goals)}


# ============================================================================
# Constraint Endpoints
# ============================================================================

@app.post("/api/constraints", tags=["Constraints"])
async def create_constraints(constraints: Constraints, user_id: str = Depends(verify_token)):
    """Create user constraints"""
    constraints.user_id = user_id
    constraints.constraint_id = str(uuid.uuid4())
    constraints.updated_at = datetime.utcnow()

    constraints_db[constraints.constraint_id] = constraints

    return {
        "constraint_id": constraints.constraint_id,
        "message": "Constraints created successfully"
    }


@app.get("/api/constraints/{constraint_id}", tags=["Constraints"])
async def get_constraints(constraint_id: str, user_id: str = Depends(verify_token)):
    """Get constraints by ID"""
    constraints = constraints_db.get(constraint_id)
    if not constraints or constraints.user_id != user_id:
        raise HTTPException(status_code=404, detail="Constraints not found")
    return constraints


@app.get("/api/constraints", tags=["Constraints"])
async def list_constraints(user_id: str = Depends(verify_token)):
    """List all constraints for user"""
    user_constraints = [c for c in constraints_db.values() if c.user_id == user_id]
    return {"constraints": user_constraints, "count": len(user_constraints)}


# ============================================================================
# Training Plan Endpoints
# ============================================================================

@app.post("/api/plans/generate", tags=["Training Plans"])
async def generate_plan(request: GeneratePlanRequest, user_id: str = Depends(verify_token)):
    """Generate a new training plan"""
    # Get goals
    goals = []
    for goal_id in request.goal_ids:
        goal = goals_db.get(goal_id)
        if not goal or goal.user_id != user_id:
            raise HTTPException(status_code=404, detail=f"Goal {goal_id} not found")
        goals.append(goal)

    if not goals:
        raise HTTPException(status_code=400, detail="At least one goal is required")

    # Get assessment
    assessment = assessments_db.get(request.assessment_id)
    if not assessment or assessment.user_id != user_id:
        raise HTTPException(status_code=404, detail="Assessment not found")

    # Get constraints
    constraints = constraints_db.get(request.constraint_id)
    if not constraints or constraints.user_id != user_id:
        raise HTTPException(status_code=404, detail="Constraints not found")

    # Generate plan
    try:
        plan = generate_training_plan(user_id, goals, assessment, constraints)
        plans_db[plan.plan_id] = plan

        return {
            "plan_id": plan.plan_id,
            "message": "Training plan generated successfully!",
            "summary": {
                "duration_weeks": plan.total_duration_weeks,
                "methodology": plan.methodology.name,
                "periodization": plan.methodology.periodization_model.value,
                "phases": len(plan.macrocycle.phases),
                "total_sessions": sum(len(m.sessions) for m in plan.microcycles),
                "start_date": plan.start_date.isoformat(),
                "end_date": plan.end_date.isoformat()
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Plan generation failed: {str(e)}")


@app.get("/api/plans/{plan_id}", tags=["Training Plans"])
async def get_plan(plan_id: str, user_id: str = Depends(verify_token)):
    """Get complete training plan"""
    plan = plans_db.get(plan_id)
    if not plan or plan.user_id != user_id:
        raise HTTPException(status_code=404, detail="Plan not found")
    return plan


@app.get("/api/plans", tags=["Training Plans"])
async def list_plans(user_id: str = Depends(verify_token)):
    """List all plans for user"""
    user_plans = [p for p in plans_db.values() if p.user_id == user_id]
    return {"plans": user_plans, "count": len(user_plans)}


@app.get("/api/plans/{plan_id}/summary", tags=["Training Plans"])
async def get_plan_summary(plan_id: str, user_id: str = Depends(verify_token)):
    """Get plan summary"""
    plan = plans_db.get(plan_id)
    if not plan or plan.user_id != user_id:
        raise HTTPException(status_code=404, detail="Plan not found")

    return {
        "plan_id": plan.plan_id,
        "duration_weeks": plan.total_duration_weeks,
        "methodology": plan.methodology.name,
        "periodization": plan.methodology.periodization_model.value,
        "start_date": plan.start_date.isoformat(),
        "end_date": plan.end_date.isoformat(),
        "phases": [
            {
                "name": p.name,
                "weeks": f"{p.start_week}-{p.end_week}",
                "duration": p.duration_weeks,
                "focus": p.focus
            }
            for p in plan.macrocycle.phases
        ],
        "total_sessions": sum(len(m.sessions) for m in plan.microcycles),
        "current_week": plan.current_week
    }


@app.get("/api/plans/{plan_id}/week/{week_number}", tags=["Training Plans"])
async def get_week(plan_id: str, week_number: int, user_id: str = Depends(verify_token)):
    """Get specific week from plan"""
    plan = plans_db.get(plan_id)
    if not plan or plan.user_id != user_id:
        raise HTTPException(status_code=404, detail="Plan not found")

    # Find microcycle for this week
    microcycle = next((m for m in plan.microcycles if m.week_number == week_number), None)
    if not microcycle:
        raise HTTPException(status_code=404, detail="Week not found")

    return microcycle


# ============================================================================
# Workout Logging Endpoints
# ============================================================================

@app.post("/api/workouts/log", tags=["Workouts"])
async def log_workout(workout_log: WorkoutLog, user_id: str = Depends(verify_token)):
    """Log a completed workout"""
    workout_log.user_id = user_id
    workout_log.log_id = str(uuid.uuid4())
    workout_log.completed_at = datetime.utcnow()

    workout_logs_db[workout_log.log_id] = workout_log

    # Mark session as completed in plan
    for plan in plans_db.values():
        if plan.user_id == user_id:
            for microcycle in plan.microcycles:
                for session in microcycle.sessions:
                    if session.session_id == workout_log.session_id:
                        session.completed = True
                        session.completed_at = workout_log.completed_at
                        session.workout_log_id = workout_log.log_id

    return {
        "log_id": workout_log.log_id,
        "message": "Workout logged successfully!"
    }


@app.get("/api/workouts/logs", tags=["Workouts"])
async def list_workout_logs(
    plan_id: Optional[str] = None,
    user_id: str = Depends(verify_token)
):
    """List workout logs"""
    logs = [log for log in workout_logs_db.values() if log.user_id == user_id]

    # Filter by plan if specified
    if plan_id:
        plan = plans_db.get(plan_id)
        if plan:
            session_ids = [s.session_id for m in plan.microcycles for s in m.sessions]
            logs = [log for log in logs if log.session_id in session_ids]

    return {"logs": logs, "count": len(logs)}


# ============================================================================
# Adaptation Endpoints
# ============================================================================

@app.post("/api/plans/{plan_id}/adapt", tags=["Adaptation"])
async def adapt_plan(plan_id: str, user_id: str = Depends(verify_token)):
    """Analyze performance and adapt training plan"""
    # Get plan
    plan = plans_db.get(plan_id)
    if not plan or plan.user_id != user_id:
        raise HTTPException(status_code=404, detail="Plan not found")

    # Get workout logs for this plan
    session_ids = [s.session_id for m in plan.microcycles for s in m.sessions]
    logs = [log for log in workout_logs_db.values()
            if log.user_id == user_id and log.session_id in session_ids]

    if not logs:
        raise HTTPException(
            status_code=400,
            detail="No workout logs found. Complete and log some workouts first."
        )

    # Get assessment and constraints
    assessment = next((a for a in assessments_db.values() if a.user_id == user_id), None)
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")

    constraints = next((c for c in constraints_db.values() if c.user_id == user_id), None)
    if not constraints:
        raise HTTPException(status_code=404, detail="Constraints not found")

    # Run adaptation analysis
    try:
        adapted_plan, recommendations = analyze_and_adapt(
            plan=plan,
            workout_logs=logs,
            assessment=assessment,
            constraints=constraints,
            current_date=date.today()
        )

        # Update plan in database
        plans_db[plan_id] = adapted_plan

        return {
            "message": "Plan adapted successfully!",
            "logs_analyzed": len(logs),
            "recommendations_count": len(recommendations),
            "recommendations": [
                {
                    "trigger": rec.trigger.value,
                    "type": rec.adaptation_type.value,
                    "severity": round(rec.severity * 100, 1),
                    "description": rec.description,
                    "reasoning": rec.reasoning,
                    "suggested_changes": rec.suggested_changes
                }
                for rec in recommendations
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Adaptation failed: {str(e)}")


@app.get("/api/plans/{plan_id}/performance", tags=["Adaptation"])
async def get_performance_analysis(plan_id: str, user_id: str = Depends(verify_token)):
    """Get performance analysis for a plan"""
    # Get plan
    plan = plans_db.get(plan_id)
    if not plan or plan.user_id != user_id:
        raise HTTPException(status_code=404, detail="Plan not found")

    # Get workout logs
    session_ids = [s.session_id for m in plan.microcycles for s in m.sessions]
    logs = [log for log in workout_logs_db.values()
            if log.user_id == user_id and log.session_id in session_ids]

    if not logs:
        return {
            "message": "No workout logs found for analysis",
            "logs_count": 0
        }

    # Analyze performance
    engine = AdaptationEngine()
    performance = engine.analyze_performance(plan, logs, date.today())

    return {
        "completion_rate": round(performance.completion_rate * 100, 1),
        "average_difficulty_delta": round(performance.average_difficulty_delta, 2),
        "volume_compliance": round(performance.volume_compliance * 100, 1),
        "intensity_compliance": round(performance.intensity_compliance * 100, 1),
        "recovery_quality": round(performance.recovery_quality * 100, 1),
        "acute_chronic_workload_ratio": round(performance.acute_chronic_workload_ratio, 2),
        "training_monotony": round(performance.training_monotony, 2),
        "training_strain": round(performance.training_strain, 2),
        "trend": performance.trend,
        "logs_analyzed": len(logs),
        "analysis_period_days": 14
    }


# ============================================================================
# Run Application
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    print("\n" + "=" * 80)
    print("🚀 Hybrid Athlete Platform API - Starting...")
    print("=" * 80)
    print("\nAPI will be available at:")
    print("  • Main API: http://localhost:8000")
    print("  • Interactive Docs: http://localhost:8000/docs")
    print("  • ReDoc: http://localhost:8000/redoc")
    print("\n" + "=" * 80 + "\n")

    uvicorn.run(app, host="0.0.0.0", port=8000)
