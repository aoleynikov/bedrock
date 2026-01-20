from typing import Dict, Any
from src.services.base import BaseService
from src.database.connection import DatabaseConnection


class HealthService(BaseService):
    """Service for health check business logic."""
    
    def __init__(self):
        super().__init__()
    
    async def check_health(self) -> Dict[str, Any]:
        """
        Perform comprehensive health check.
        
        Returns status of all critical components.
        """
        health_status = {
            'status': 'healthy',
            'checks': {}
        }
        
        # Check database
        db_status = await self.check_database()
        health_status['checks']['database'] = db_status
        
        # Check RabbitMQ (if needed in future)
        # rabbitmq_status = await self.check_rabbitmq()
        # health_status['checks']['rabbitmq'] = rabbitmq_status
        
        # Overall status is unhealthy if any check fails
        if any(check.get('status') != 'healthy' for check in health_status['checks'].values()):
            health_status['status'] = 'unhealthy'
        
        return health_status
    
    async def check_database(self) -> Dict[str, Any]:
        """
        Check database connectivity.
        
        Business rules:
        - Database must be accessible
        - Ping must succeed
        """
        try:
            db = DatabaseConnection.get_db()
            await db.client.admin.command('ping')
            return {
                'status': 'healthy',
                'message': 'Database connection successful'
            }
        except Exception as e:
            self._log_error('Database health check failed', error=e)
            return {
                'status': 'unhealthy',
                'message': f'Database connection failed: {str(e)}'
            }
    
    async def check_rabbitmq(self) -> Dict[str, Any]:
        """
        Check RabbitMQ connectivity.
        
        This is a placeholder for future implementation.
        """
        # TODO: Implement RabbitMQ health check
        return {
            'status': 'healthy',
            'message': 'RabbitMQ check not implemented'
        }
