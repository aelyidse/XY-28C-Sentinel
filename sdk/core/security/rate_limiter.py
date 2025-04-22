class RateLimiter:
    def check_rate_limit(self, user_id: str, action: str) -> bool:
        """Check if action exceeds rate limit"""
        current_time = time.time()
        window_start = current_time - 3600  # 1 hour window
        
        # Clean old entries
        self._clean_old_entries(window_start)
        
        # Check limit
        action_count = self._get_action_count(user_id, action, window_start)
        return action_count < self.MAX_ACTIONS_PER_HOUR