from fastapi import APIRouter, HTTPException, Depends

# from app.services.in_memory_couter import VisitCounterService
# from app.services.simple_redis_counter import VisitCounterService
from app.services.application_layer_cached_visit_counter import VisitCounterService
from app.schemas.counter import VisitCount

router = APIRouter()


# Dependency to get VisitCounterService instance
def get_visit_counter_service():
    return VisitCounterService()


@router.post("/visit/{page_id}")
async def record_visit(
    page_id: str,
    counter_service: VisitCounterService = Depends(get_visit_counter_service),
):
    """Record a visit for a website"""
    try:
        await counter_service.increment_visit(page_id)
        return {"status": "success", "message": f"Visit recorded for page {page_id}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/visits/{page_id}", response_model=VisitCount)
async def get_visits(
    page_id: str,
    counter_service: VisitCounterService = Depends(get_visit_counter_service),
):
    """Get visit count for a website"""
    try:
        count = await counter_service.get_visit_count(page_id)
        # return VisitCount(visits=count, served_via="in_memory")
        # return VisitCount(visits=count, served_via="redis")
        return VisitCount(visits=count, served_via=counter_service.get_served_via())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
