class MissionController:
    def __init__(self, sdk: SentinelSDK):
        self.sdk = sdk
    
    async def execute_mission(self, mission_params: Dict[str, Any], role: str) -> bool:
        """Execute a mission with role-based access control"""
        try:
            if not self.sdk.check_permission(role, "mission", "execute"):
                await self.sdk.audit_logger.log_operation(
                    operation="mission_execution",
                    user_id=mission_params.get("user_id", "unknown"),
                    role=role,
                    resource="mission",
                    action="execute",
                    status="denied",
                    details={
                        "reason": "insufficient_permissions",
                        "mission_id": mission_params.get("mission_id")
                    },
                    severity=AuditSeverity.WARNING,
                    component_id="mission_controller"
                )
                raise PermissionError("Insufficient permissions to execute mission")
            
            # Log successful permission check
            await self.sdk.audit_logger.log_operation(
                operation="mission_execution",
                user_id=mission_params.get("user_id", "unknown"),
                role=role,
                resource="mission",
                action="execute",
                status="authorized",
                details={
                    "mission_id": mission_params.get("mission_id"),
                    "mission_type": mission_params.get("type")
                },
                severity=AuditSeverity.INFO,
                component_id="mission_controller"
            )
            
            # Proceed with mission execution
            result = await self._execute_mission_impl(mission_params)
            
            # Log mission completion
            await self.sdk.audit_logger.log_operation(
                operation="mission_execution",
                user_id=mission_params.get("user_id", "unknown"),
                role=role,
                resource="mission",
                action="execute",
                status="completed" if result else "failed",
                details={
                    "mission_id": mission_params.get("mission_id"),
                    "success": result
                },
                severity=AuditSeverity.INFO if result else AuditSeverity.WARNING,
                component_id="mission_controller"
            )
            
            return result
            
        except Exception as e:
            # Log any unexpected errors
            await self.sdk.audit_logger.log_operation(
                operation="mission_execution",
                user_id=mission_params.get("user_id", "unknown"),
                role=role,
                resource="mission",
                action="execute",
                status="error",
                details={
                    "mission_id": mission_params.get("mission_id"),
                    "error": str(e)
                },
                severity=AuditSeverity.CRITICAL,
                component_id="mission_controller"
            )
            raise