import asyncio
from typing import Dict, List
from ..config.system_config import SystemConfig, SystemMode
from ..events.event_manager import EventManager
from ..interfaces.system_component import SystemComponent
from ..utils.error_handler import ErrorHandler, SentinelError, ErrorCategory, ErrorSeverity

class SystemController:
    async def start(self) -> None:
        self._running = True
        self.error_handler = ErrorHandler(self.event_manager)
        
        # Register error handlers
        self._register_error_handlers()
        
        tasks = [
            self.event_manager.process_events(),
            self._update_components(),
            self.blockchain_network.start_network(),
            self._monitor_consensus()  # Add consensus monitoring
        ]
        await asyncio.gather(*tasks)

    def _register_error_handlers(self) -> None:
        """Register error handlers for different categories"""
        self.error_handler.register_handler(
            ErrorCategory.NETWORK, 
            self._handle_network_error
        )
        self.error_handler.register_handler(
            ErrorCategory.BLOCKCHAIN, 
            self._handle_blockchain_error
        )
        
        # Register recovery strategies
        self.error_handler.register_recovery_strategy(
            ConnectionError, 
            self._recover_connection
        )

    async def _handle_network_error(self, error: SentinelError) -> None:
        """Handle network-related errors"""
        if error.severity >= ErrorSeverity.ERROR:
            # Try to reconnect
            await self._attempt_reconnect()
            
    async def _handle_blockchain_error(self, error: SentinelError) -> None:
        """Handle blockchain-related errors"""
        if error.severity >= ErrorSeverity.ERROR:
            # Try to recover chain
            await self._recover_chain()
            
    async def _recover_connection(self, error: Exception) -> None:
        """Recovery strategy for connection errors"""
        # Implementation of connection recovery
        pass
        
    async def _attempt_reconnect(self) -> None:
        """Attempt to reconnect to network"""
        # Implementation of reconnection logic
        pass

    async def _monitor_consensus(self) -> None:
        """Monitor blockchain consensus status"""
        while self._running:
            # Check chain validity
            if not await self.blockchain.validate_consensus(self.blockchain.chain):
                await self.event_manager.publish(SystemEvent(
                    event_type=SystemEventType.CONSENSUS_FAILURE,
                    component_id="blockchain",
                    data={"chain_length": len(self.blockchain.chain)},
                    priority=1
                ))
                
            await asyncio.sleep(5.0)  # Check every 5 seconds

    async def _handle_consensus_failure(self, event: SystemEvent) -> None:
        """Handle blockchain consensus failure"""
        # Attempt chain recovery
        recovered = await self._recover_chain()
        
        if not recovered:
            # Initiate emergency protocols
            await self._initiate_emergency_protocols()
            
        await self.event_manager.publish(SystemEvent(
            event_type=SystemEventType.CONSENSUS_RECOVERY,
            component_id="blockchain",
            data={"success": recovered},
            priority=0
        ))
    
    async def _recover_chain(self) -> bool:
        """Attempt to recover valid chain state"""
        # Get proposed chains from all nodes
        proposed_chains = await self.blockchain_network.get_proposed_chains()
        
        # Select longest valid chain
        valid_chains = [
            chain for chain in proposed_chains
            if await self.blockchain.validate_consensus(chain)
        ]
        
        if valid_chains:
            # Update to longest valid chain
            self.blockchain.chain = max(valid_chains, key=len)
            return True
            
        return False

    def __init__(self, config: SystemConfig):
        self.config = config
        self.event_manager = EventManager()
        self.components: Dict[str, SystemComponent] = {}
        self._running = False
        self.blockchain_network = BlockchainNetworkInterface(
            blockchain=CommandBlockchain()
        )
        async def register_component(self, component: SystemComponent) -> None:
            self.components[component.component_id] = component
            await component.initialize()
            
        async def stop(self) -> None:
            self._running = False
            for component in self.components.values():
                await component.shutdown()
                
        async def _update_components(self) -> None:
            while self._running:
                update_tasks = []
                for component in self.components.values():
                    try:
                        update_tasks.append(component.update())
                    except Exception as e:
                        await self.error_handler.handle_error(e, component.component_id)
                
                try:
                    await asyncio.gather(*update_tasks)
                    await asyncio.sleep(1.0 / self.config.ai_processing_rate)
                except Exception as e:
                    await self.error_handler.handle_error(
                        e, 
                        "system_controller"
                    )
        self.audit_trail = AuditTrailManager(self.blockchain_network.blockchain)

    async def _handle_event(self, event: SystemEvent) -> None:
        """Process system events with audit logging"""
        # Log event to audit trail
        await self.audit_trail.log_event(event)
        
        # Process event normally
        await self._process_event(event)

    async def verify_system_integrity(self) -> bool:
        """Verify system integrity using audit trail"""
        return await self.audit_trail.verify_audit_trail()