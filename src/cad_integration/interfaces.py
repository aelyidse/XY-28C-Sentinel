class CADInterface:
    """
    Base interface for CAD integration.
    """
    def __init__(self, config):
        self.config = config
        
    async def connect(self):
        """Connect to CAD system"""
        raise NotImplementedError
        
    async def disconnect(self):
        """Disconnect from CAD system"""
        raise NotImplementedError
        
    async def send_model(self, model_data):
        """Send 3D model data to CAD system"""
        raise NotImplementedError
        
    async def receive_model(self):
        """Receive updated model data from CAD system"""
        raise NotImplementedError