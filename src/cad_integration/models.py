class CADModel:
    """
    Base class for CAD models.
    """
    def __init__(self, model_id):
        self.id = model_id
        self.data = None
        
    def update(self, new_data):
        """Update model data"""
        self.data = new_data