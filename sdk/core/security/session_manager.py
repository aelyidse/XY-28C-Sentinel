class SessionManager:
    def create_session(self, user_id: str, role: str) -> str:
        """Create new session with expiration"""
        session_token = self._generate_secure_token()
        expiration = datetime.now() + timedelta(hours=8)
        
        self._sessions[session_token] = {
            'user_id': user_id,
            'role': role,
            'expiration': expiration
        }
        
        return session_token