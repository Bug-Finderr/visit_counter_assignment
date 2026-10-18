from fastapi import APIRouter, Depends

from app.services.sharded_visit_counter import VisitCounterService
from app.core.sharded_redis_manager import RedisManager
from app.schemas.counter import VisitCount

router = APIRouter()

# one pool per shard for the whole process, not per request
redis_manager = RedisManager()


def get_visit_counter_service():
    return VisitCounterService(redis_manager)


@router.post("/visit/{page_id}")
async def record_visit(
    page_id: str,
    counter_service: VisitCounterService = Depends(get_visit_counter_service),
):
    """Record a visit for a website"""
    await counter_service.increment_visit(page_id)
    return {"status": "success", "message": f"Visit recorded for page {page_id}"}


@router.get("/visits/{page_id}", response_model=VisitCount)
async def get_visits(
    page_id: str,
    counter_service: VisitCounterService = Depends(get_visit_counter_service),
):
    """Get visit count for a website"""
    count = await counter_service.get_visit_count(page_id)
    return VisitCount(visits=count, served_via=counter_service.get_served_via())
