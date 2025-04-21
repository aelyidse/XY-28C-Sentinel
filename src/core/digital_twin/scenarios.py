BASIC_SCENARIOS = [
    {
        'name': 'propulsion_failure',
        'failure': {
            'component': 'engine_1',
            'severity': 0.3
        },
        'duration': 60  # seconds
    },
    {
        'name': 'high_wind_conditions',
        'environment': {
            'wind_speed': 25,
            'wind_direction': 45
        },
        'duration': 120
    }
]