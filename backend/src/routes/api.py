from fastapi import APIRouter, Depends
from src.services.health_service import HealthService
from src.dependencies import get_health_service

router = APIRouter()


@router.get('/health')
async def health_check(
    health_service: HealthService = Depends(get_health_service)
):
    """
    Health check endpoint.
    
    Gateway: HTTP endpoint -> Service layer
    """
    return await health_service.check_health()


@router.get('/test')
async def test_endpoint(
    health_service: HealthService = Depends(get_health_service)
):
    """
    Test endpoint to verify backend connectivity.
    
    Gateway: HTTP endpoint -> Service layer
    """
    db_status = await health_service.check_database()
    return {
        'status': db_status.get('status'),
        'message': db_status.get('message', 'Backend is working')
    }
