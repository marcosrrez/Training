"""
Goal management endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from db.postgres import get_session
from core.models.goal import Goal

router = APIRouter()


@router.post("/goals", response_model=Goal, status_code=status.HTTP_201_CREATED)
async def create_goal(
    goal: Goal,
    session: AsyncSession = Depends(get_session)
):
    """
    Create a new training goal

    This endpoint:
    - Validates the goal
    - Runs feasibility analysis
    - Provides realistic timeline recommendations
    - Stores the goal
    """
    # TODO: Implement goal creation with feasibility analysis
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Goal creation will be implemented in next phase"
    )


@router.get("/goals/{goal_id}", response_model=Goal)
async def get_goal(
    goal_id: str,
    session: AsyncSession = Depends(get_session)
):
    """Get a specific goal"""
    # TODO: Implement goal retrieval
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Goal retrieval will be implemented in next phase"
    )


@router.get("/goals", response_model=List[Goal])
async def list_goals(
    user_id: str,
    status: str = "active",
    session: AsyncSession = Depends(get_session)
):
    """List goals for a user"""
    # TODO: Implement goal listing
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Goal listing will be implemented in next phase"
    )


@router.put("/goals/{goal_id}", response_model=Goal)
async def update_goal(
    goal_id: str,
    goal: Goal,
    session: AsyncSession = Depends(get_session)
):
    """Update a goal"""
    # TODO: Implement goal update
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Goal update will be implemented in next phase"
    )
