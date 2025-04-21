class MissionController:
    def __init__(self, blockchain: CommandBlockchain):
        self.blockchain = blockchain
        self.signer = MissionSigner(blockchain.node_keys['ground_station'])
        self.verifier = MissionVerifier(
            blockchain.node_keys['ground_station'].public_key()
        )
        self.cache = MissionCache()
        
    async def execute_mission(self, signed_params: SignedMissionParameters) -> bool:
        """Execute mission with caching and contextual adaptation"""
        # Check cache first
        cached = self.cache.retrieve(signed_params.parameters['mission_id'])
        if cached:
            # Adapt parameters to current context
            adapted = self.cache.adapt_parameters(
                cached,
                self.context_aware_planner.situational_context
            )
            signed_params.parameters = adapted
            
        # Verify and execute mission
        if not self.verifier.verify_parameters(signed_params):
            await self.event_manager.publish(SystemEvent(
                event_type=SystemEventType.INVALID_MISSION_PARAMETERS,
                component_id="mission_controller",
                data={"reason": "Invalid signature"},
                priority=2
            ))
            return False
            
        # Store in cache
        self.cache.store(
            signed_params.parameters['mission_id'],
            CachedMission(
                parameters=signed_params.parameters,
                timestamp=datetime.now(),
                context=self.context_aware_planner.situational_context,
                signature=signed_params.signature
            )
        )
        
        # Create blockchain transaction
        tx = self.blockchain.create_transaction({
            'type': 'mission_execution',
            'parameters': signed_params.parameters
        })
        
        # Add to blockchain
        self.blockchain.add_block(tx)
        
        # Execute mission
        return await self._execute_mission_parameters(signed_params.parameters)

    def create_mission(self, parameters: Dict[str, Any]) -> SignedMissionParameters:
        """Create signed mission parameters"""
        return self.signer.sign_parameters(parameters)