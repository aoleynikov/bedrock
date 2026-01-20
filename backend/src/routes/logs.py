from fastapi import APIRouter, HTTPException, status

router = APIRouter()


@router.get('/logs/correlation/{correlation_id}')
async def get_logs_by_correlation(correlation_id: str):
    """
    Note: With Docker-level log rotation, logs are managed by Docker.
    Use Docker commands or a log aggregation system to query logs:
    
    docker logs bedrock_backend | grep {correlation_id}
    docker logs bedrock_worker | grep {correlation_id}
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail='Log querying requires Docker logs or a log aggregation system. Use: docker logs <container> | grep <correlation_id>'
    )
