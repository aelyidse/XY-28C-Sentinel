class AuthManager:
    def authenticate(self, credentials: Dict[str, Any], mfa_token: str = None) -> bool:
        """Authenticate user with optional MFA"""
        if not self._verify_credentials(credentials):
            return False
            
        if self._requires_mfa(credentials['role']):
            if not mfa_token or not self._verify_mfa_token(mfa_token):
                return False
                
        return True