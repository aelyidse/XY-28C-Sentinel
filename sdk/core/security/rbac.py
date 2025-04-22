from enum import Enum
from typing import List, Dict, Set, Optional
from dataclasses import dataclass

class Role(Enum):
    ADMIN = "admin"
    OPERATOR = "operator"
    OBSERVER = "observer"
    MAINTENANCE = "maintenance"

@dataclass
class Permission:
    resource: str
    actions: Set[str]

class RBACManager:
    def __init__(self):
        self._role_permissions: Dict[Role, List[Permission]] = {
            Role.ADMIN: [],
            Role.OPERATOR: [],
            Role.OBSERVER: [],
            Role.MAINTENANCE: []
        }
        self._setup_default_permissions()
    
    def _setup_default_permissions(self):
        # Admin has full access
        self._role_permissions[Role.ADMIN] = [
            Permission("*", {"*"}),
        ]
        
        # Operator can control missions and sensors
        self._role_permissions[Role.OPERATOR] = [
            Permission("mission", {"create", "execute", "abort"}),
            Permission("sensors", {"configure", "read"}),
            Permission("navigation", {"control"}),
        ]
        
        # Observer can only read data
        self._role_permissions[Role.OBSERVER] = [
            Permission("mission", {"read"}),
            Permission("sensors", {"read"}),
            Permission("telemetry", {"read"}),
        ]
        
        # Maintenance can configure and diagnose
        self._role_permissions[Role.MAINTENANCE] = [
            Permission("sensors", {"configure", "calibrate", "diagnose"}),
            Permission("system", {"diagnose", "update"}),
        ]
    
    def check_permission(self, role: Role, resource: str, action: str) -> bool:
        if role == Role.ADMIN:
            return True
            
        permissions = self._role_permissions.get(role, [])
        for permission in permissions:
            if (permission.resource == "*" or permission.resource == resource) and \
               ("*" in permission.actions or action in permission.actions):
                return True
        return False