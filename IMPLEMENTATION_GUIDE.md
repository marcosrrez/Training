# Hybrid Athlete Platform - Implementation Guide

## Current Status

This repository contains the **foundational architecture** for the Hybrid Athlete Platform, based on the comprehensive product specification document. The groundwork has been laid for a scalable, research-backed training platform.

### What Has Been Built ✅

#### 1. Project Structure & Configuration
- Complete backend directory structure (Python/FastAPI)
- Frontend placeholder structure (React)
- Docker Compose configuration for local development
- Environment configuration templates
- Comprehensive `.gitignore` and dependency management

#### 2. Core Data Models
**Location: `backend/core/models/`**

All Pydantic models implementing the specification from Section 5.2:

- **User Models** (`user.py`): User profiles, preferences, subscription management
- **Assessment Models** (`assessment.py`): Fitness assessments, body composition, training history, health data
- **Goal Models** (`goal.py`): Endurance, strength, composition, and hybrid goals with feasibility tracking
- **Constraint Models** (`constraint.py`): Time, resource, and personal constraints
- **Training Plan Models** (`training_plan.py`): Macrocycles, mesocycles, microcycles, periodization
- **Workout Models** (`workout.py`): Workout structures, intervals, exercises, intensity prescriptions
- **Workout Log Models** (`workout_log.py`): Performance tracking, wellness data, subjective feedback

#### 3. Database Configuration
**Location: `backend/db/`**

- PostgreSQL configuration with async SQLAlchemy
- MongoDB configuration with Motor (async)
- Redis placeholder for caching
- Database connection management

#### 4. API Endpoints (Scaffolded)
**Location: `backend/api/routes/`**

RESTful API structure with placeholder implementations:

- **Health** (`health.py`): Health checks and database status
- **Users** (`users.py`): User registration, authentication, profile management
- **Assessments** (`assessments.py`): Fitness assessment CRUD
- **Goals** (`goals.py`): Goal creation, feasibility analysis, tracking
- **Plans** (`plans.py`): Training plan generation and adaptation
- **Workouts** (`workouts.py`): Workout retrieval and logging

#### 5. Core Algorithms (Partially Implemented)
**Location: `backend/core/algorithms/`**

- **Feasibility Analyzer** (`feasibility.py`): ✅ **FULLY IMPLEMENTED**
  - Analyzes goal feasibility based on current fitness and timeline
  - Calculates required VO2max for endurance goals
  - Estimates realistic timelines using research-backed adaptation rates
  - Identifies required physiological adaptations
  - Assesses risks and provides recommendations
  - Supports endurance goals (5K, 10K, half marathon, marathon, ultra)
  - Placeholders for strength, composition, and hybrid goals

- **Methodology Selector** (`methodology_selector.py`): 🟡 **PLACEHOLDER**
- **Plan Generator** (`plan_generator.py`): 🟡 **PLACEHOLDER**
- **Adaptive Engine** (`adaptation.py`): 🟡 **PLACEHOLDER**

#### 6. Research Database Structure
**Location: `research_database/`**

- Complete directory structure for organizing research
- Research article template (YAML format)
- Sample research entries:
  - Seiler 2006: Polarized Training study
  - Wilson 2012: Concurrent Training interference meta-analysis

#### 7. Documentation
- Comprehensive README.md
- Research database README
- This implementation guide

---

## What Needs to Be Built 🚧

### Phase 1: Core Algorithm Completion (Highest Priority)

#### 1.1 Complete Feasibility Analysis
**File: `backend/core/algorithms/feasibility.py`**

Currently implemented for endurance goals. Need to add:

- [ ] Strength goal feasibility analysis
  - Calculate strength gain rates by training age
  - Account for genetic potential limits
  - Adjust for concurrent endurance training (interference)

- [ ] Body composition goal analysis
  - Safe fat loss rates (research-backed)
  - Muscle gain potential calculations
  - Recomposition feasibility

- [ ] Hybrid goal analysis with interference assessment
  - Quantify concurrent training interference
  - Recommend modality choices (cycling vs running)
  - Optimize session timing and separation

#### 1.2 Implement Methodology Selector
**File: `backend/core/algorithms/methodology_selector.py`**

Implement algorithm to choose optimal methodology:

- [ ] Score each methodology based on user context
- [ ] Polarized training selection criteria
- [ ] Norwegian method prerequisites (high training age, volume)
- [ ] MAF method for injury-prone or conservative users
- [ ] Time-efficient HIIT for severe time constraints
- [ ] Hybrid concurrent protocols for multi-goal athletes

#### 1.3 Build Plan Generation Engine
**File: `backend/core/algorithms/plan_generator.py`**

This is the **most complex component**. Implement pseudocode from spec Section 5.3:

- [ ] **Macrocycle Builder**: Create phase structure (base, build, peak, recovery)
- [ ] **Mesocycle Generator**: Build 3-6 week training blocks with volume progression
- [ ] **Microcycle Creator**: Generate weekly plans with proper session sequencing
- [ ] **Workout Populator**: Create individual workout structures
- [ ] **Volume Dosing**: Calculate appropriate training load
- [ ] **Intensity Distribution**: Apply methodology-specific zone distribution
- [ ] **Concurrent Training Optimizer**: Sequence strength and endurance optimally
- [ ] **Exercise Selection**: Choose exercises based on goals and equipment

#### 1.4 Implement Adaptive Learning Engine
**File: `backend/core/algorithms/adaptation.py`**

Real-time plan adjustment based on feedback:

- [ ] **Performance Trend Analysis**: Detect improvement, plateau, decline
- [ ] **Fatigue Monitoring**: Calculate cumulative fatigue from wellness data
- [ ] **Injury Risk Assessment**: Flag injury risk patterns
- [ ] **Compliance Tracking**: Measure adherence and adjust plan complexity
- [ ] **Timeline Recalibration**: Adjust goals based on actual progress
- [ ] **Stimulus Variation**: Change training when plateaued
- [ ] **Recovery Insertion**: Auto-insert recovery weeks when needed

---

### Phase 2: Backend Implementation

#### 2.1 Database Models (SQLAlchemy ORM)
**Location: `backend/db/models/`**

Convert Pydantic models to SQLAlchemy ORM models:

- [ ] User table schema
- [ ] Assessment table schema
- [ ] Goal table schema
- [ ] Constraint table schema
- [ ] Relationships and foreign keys
- [ ] Indexes for performance

#### 2.2 Database Migrations
**Tool: Alembic**

- [ ] Initialize Alembic
- [ ] Create initial migration
- [ ] Add migration for each model

#### 2.3 Service Layer
**Location: `backend/core/services/`**

Business logic layer between API and database:

- [ ] UserService (CRUD, authentication)
- [ ] AssessmentService (create, retrieve, calculate fitness scores)
- [ ] GoalService (create, validate, track progress)
- [ ] PlanService (generate, retrieve, update)
- [ ] WorkoutService (retrieve, log, analyze)

#### 2.4 API Implementation
**Location: `backend/api/routes/`**

Replace placeholders with real implementations:

- [ ] User registration with password hashing
- [ ] JWT authentication
- [ ] Assessment creation and retrieval
- [ ] Goal creation with feasibility analysis
- [ ] Training plan generation endpoint
- [ ] Workout logging with validation
- [ ] Progress tracking endpoints

#### 2.5 Research Database Integration
**Location: `backend/research/`**

- [ ] YAML parser for research articles
- [ ] Research query engine
- [ ] Cache research lookups (Redis)
- [ ] API to retrieve research citations
- [ ] Populate database with comprehensive research (50-100+ studies)

---

### Phase 3: Frontend Implementation

#### 3.1 Project Setup
**Location: `frontend/`**

- [ ] Initialize React + TypeScript project (Vite or Create React App)
- [ ] Set up Tailwind CSS
- [ ] Configure React Router
- [ ] Set up state management (Zustand or Redux)
- [ ] Configure React Query for API calls

#### 3.2 Core UI Components
**Location: `frontend/src/components/`**

- [ ] Button, Input, Card, Modal (base components)
- [ ] Forms with validation (React Hook Form)
- [ ] Charts and visualizations (Recharts)
- [ ] Loading states and error handling

#### 3.3 Onboarding Flow
**Location: `frontend/src/pages/onboarding/`**

Implement multi-step onboarding from spec Section 4:

- [ ] Stage 1: Welcome & Philosophy
- [ ] Stage 2: Goal Definition
- [ ] Stage 3: Current Fitness Assessment
- [ ] Stage 4: Constraints & Context
- [ ] Stage 5: Training Preferences
- [ ] Stage 6: Plan Preview & Commitment
- [ ] Stage 7: Initial Setup (zone calibration)

#### 3.4 Dashboard & Core Views
**Location: `frontend/src/pages/`**

- [ ] Home Dashboard (today's workout, weekly view, progress)
- [ ] Workout Detail View (structured workout display)
- [ ] Workout Logging Form (performance and wellness tracking)
- [ ] Progress Dashboard (charts, analytics, goal tracking)
- [ ] Training Plan View (calendar, weekly breakdown)
- [ ] Research Library (browse studies, view citations)

#### 3.5 Settings & Profile
- [ ] User profile editing
- [ ] Notification preferences
- [ ] Display preferences (units, theme)
- [ ] Account management

---

### Phase 4: Testing

#### 4.1 Backend Tests
**Location: `backend/tests/`**

- [ ] Unit tests for all algorithm components
- [ ] Integration tests for API endpoints
- [ ] Database tests
- [ ] Test fixtures and factories
- [ ] Achieve >80% code coverage

#### 4.2 Frontend Tests
**Location: `frontend/src/__tests__/`**

- [ ] Component unit tests (Jest + React Testing Library)
- [ ] Integration tests for key flows
- [ ] E2E tests (Playwright or Cypress)

---

### Phase 5: Deployment & DevOps

#### 5.1 Containerization
- [ ] Create production Dockerfile for backend
- [ ] Create production Dockerfile for frontend
- [ ] Optimize image sizes
- [ ] Multi-stage builds

#### 5.2 CI/CD Pipeline
**Tool: GitHub Actions**

- [ ] Automated testing on PR
- [ ] Linting and code quality checks
- [ ] Automated deployment to staging
- [ ] Production deployment workflow

#### 5.3 Infrastructure
- [ ] PostgreSQL hosting (e.g., AWS RDS, Supabase)
- [ ] MongoDB hosting (e.g., MongoDB Atlas)
- [ ] Redis hosting (e.g., Redis Cloud)
- [ ] Backend hosting (e.g., AWS ECS, Render, Fly.io)
- [ ] Frontend hosting (e.g., Vercel, Netlify)
- [ ] Domain and SSL configuration

#### 5.4 Monitoring & Logging
- [ ] Application logging (structured logs)
- [ ] Error tracking (e.g., Sentry)
- [ ] Performance monitoring
- [ ] Uptime monitoring

---

## Development Workflow

### Local Setup

1. **Clone and setup:**
```bash
git clone <repo-url>
cd Training
cp .env.example .env
# Edit .env with your local database credentials
```

2. **Backend setup:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. **Database setup (using Docker):**
```bash
docker-compose up -d postgres mongodb redis
```

4. **Run database migrations:**
```bash
cd backend
alembic upgrade head
```

5. **Start backend:**
```bash
cd backend
uvicorn main:app --reload
```

6. **Frontend setup:**
```bash
cd frontend
npm install
npm run dev
```

7. **Access the application:**
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Frontend: http://localhost:3000

---

## Testing the Feasibility Analyzer

The feasibility analyzer is **fully functional** and can be tested:

```python
# Example usage
from core.algorithms.feasibility import analyze_goal_feasibility
from core.models.goal import Goal, EnduranceGoal, GoalType
from core.models.assessment import Assessment, EnduranceMetrics, BodyComposition, TrainingHistory, Health, Lifestyle
from core.models.constraint import Constraints, TimeConstraints, SessionRange
from datetime import datetime, timedelta

# Create sample assessment
assessment = Assessment(
    user_id="user123",
    assessment_id="assess123",
    body_composition=BodyComposition(weight=180, height=72),
    endurance_metrics=EnduranceMetrics(vo2max=42),
    training_history=TrainingHistory(
        years_of_training=2,
        detraining_period_months=0
    ),
    health=Health(),
    lifestyle=Lifestyle(sleep_hours=7, stress_level=3)
)

# Create sample goal
goal = Goal(
    goal_id="goal123",
    user_id="user123",
    type=GoalType.ENDURANCE,
    target_date=datetime.now() + timedelta(weeks=20),
    endurance_goal=EnduranceGoal(
        event="half_marathon",
        target_time_seconds=5400  # 1:30:00
    )
)

# Create sample constraints
constraints = Constraints(
    user_id="user123",
    constraint_id="const123",
    time=TimeConstraints(
        sessions_per_week=SessionRange(min=4, max=6, target=5),
        session_duration_minutes=SessionRange(min=30, max=60, target=45),
        total_weekly_hours=4.5
    )
)

# Analyze feasibility
feasibility = analyze_goal_feasibility(goal, assessment, constraints)

print(f"Probability of success: {feasibility.probability}")
print(f"Is realistic: {feasibility.is_realistic}")
print(f"Estimated timeline: {feasibility.estimated_timeline_weeks} weeks")
print(f"Recommendation: {feasibility.recommendation}")
```

---

## Priority Roadmap

### Week 1-2: Core Algorithms
- ✅ Feasibility analyzer (DONE)
- 🔄 Complete methodology selector
- 🔄 Start plan generation engine (macrocycle, mesocycle)

### Week 3-4: Plan Generation
- 🔄 Complete plan generation (microcycles, workouts)
- 🔄 Workout generation logic
- 🔄 Exercise selection and prescription

### Week 5-6: Backend Services
- 🔄 Database models and migrations
- 🔄 Service layer implementation
- 🔄 API endpoint implementation

### Week 7-8: Frontend Foundation
- 🔄 Project setup and core components
- 🔄 Start onboarding flow
- 🔄 Dashboard scaffolding

### Week 9-12: Feature Complete MVP
- 🔄 Complete onboarding flow
- 🔄 Workout logging and tracking
- 🔄 Progress visualization
- 🔄 Testing and bug fixes

### Week 13-16: Polish & Deploy
- 🔄 Adaptive learning engine
- 🔄 Research database population
- 🔄 Comprehensive testing
- 🔄 Beta deployment

---

## Key Design Decisions

### 1. Why FastAPI?
- Modern, fast Python framework
- Automatic OpenAPI documentation
- Async support for scalability
- Type validation with Pydantic
- Easy to learn and maintain

### 2. Why PostgreSQL + MongoDB?
- **PostgreSQL**: Structured user data, relational integrity
- **MongoDB**: Flexible workout structures, research database, rapid iteration

### 3. Why Pydantic Models First?
- Type safety and validation
- Easy serialization for API
- Can be converted to SQLAlchemy models
- Self-documenting code

### 4. Algorithm-First Approach
- Core value is in the intelligence
- Get the science right before the UI
- Easier to test logic independently
- Multiple frontends possible (web, mobile, API)

---

## Research Database Population

The research database is **critical** for credibility. Priority research areas:

### High Priority (MVP)
- ✅ Polarized training (Seiler et al.)
- ✅ Concurrent training interference (Wilson et al.)
- 🔄 Norwegian method (Seiler, Tønnessen)
- 🔄 MAF method (Maffetone)
- 🔄 VO2max development protocols
- 🔄 Lactate threshold training
- 🔄 Strength training for endurance athletes
- 🔄 Detraining and return to training

### Medium Priority
- 🔄 Body composition (fat loss, muscle gain)
- 🔄 Nutrition for hybrid athletes
- 🔄 Recovery and sleep optimization
- 🔄 Injury prevention
- 🔄 Age and gender-specific training

### Lower Priority (Post-MVP)
- 🔄 Advanced topics (altitude, heat, cold)
- 🔄 Supplementation evidence
- 🔄 Wearable technology validation
- 🔄 Psychological factors

---

## Questions to Resolve

1. **Monetization**: When to implement subscription/payment?
2. **Authentication**: Use Auth0, Firebase, or custom JWT?
3. **Target Audience**: Which persona to focus on for MVP?
4. **Research Source**: Partner with university/lab or DIY?
5. **Deployment**: Cloud provider preference?

---

## Next Immediate Steps

1. ✅ Review this implementation guide
2. 🔄 Complete the methodology selector
3. 🔄 Start implementing the plan generation engine
4. 🔄 Set up database models and migrations
5. 🔄 Test the full pipeline: goal → feasibility → plan generation

---

## Getting Help

- **Product Spec**: See the original specification document for detailed requirements
- **Research**: See `research_database/` for scientific backing
- **API Docs**: Run backend and visit http://localhost:8000/docs
- **Code Comments**: All algorithm files have TODO comments for guidance

---

**Remember**: The goal is to build an **evidence-based, personalized training platform**. Every algorithm decision should be backed by research. Every UX decision should serve the user's success.

Let's build something that genuinely helps people achieve their athletic goals! 🏃‍♂️💪
