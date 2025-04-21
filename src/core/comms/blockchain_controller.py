from typing import Dict, List, Optional, Any
from datetime import datetime
import hashlib
import json
from dataclasses import dataclass
from ..system.system_controller import SystemController
from ..system.events import SystemEvent, SystemEventType

@dataclass
class Block:
    timestamp: float
    data: Dict[str, Any]
    previous_hash: str
    nonce: int = 0
    
    @property
    def hash(self) -> str:
        """Calculate block hash"""
        block_string = json.dumps(self.__dict__, sort_keys=True)
        return hashlib.sha256(block_string.encode()).hexdigest()

class BlockchainController:
    def __init__(self, system_controller: SystemController):
        self.chain: List[Block] = []
        self.pending_transactions: List[Dict] = []
        self.system_controller = system_controller
        self.difficulty = 4  # Number of leading zeros required for proof of work
        self.consensus_threshold = 0.66  # 66% nodes must agree
        self.max_pending_transactions = 100
        
    async def initialize_chain(self):
        """Initialize blockchain with genesis block"""
        genesis_block = Block(
            timestamp=datetime.now().timestamp(),
            data={"message": "Genesis Block"},
            previous_hash="0" * 64
        )
        self.chain.append(genesis_block)
        
    async def add_command(self, command: Dict[str, Any]) -> bool:
        """Add new command to pending transactions"""
        if len(self.pending_transactions) >= self.max_pending_transactions:
            return False
            
        self.pending_transactions.append({
            "timestamp": datetime.now().timestamp(),
            "command": command,
            "signature": await self._sign_command(command)
        })
        
        if len(self.pending_transactions) >= 10:  # Batch size threshold
            await self._create_block()
        return True
        
    async def _create_block(self) -> Optional[Block]:
        """Create new block from pending transactions"""
        if not self.pending_transactions:
            return None
            
        new_block = Block(
            timestamp=datetime.now().timestamp(),
            data={"transactions": self.pending_transactions},
            previous_hash=self.chain[-1].hash
        )
        
        # Perform proof of work
        while not new_block.hash.startswith("0" * self.difficulty):
            new_block.nonce += 1
            
        # Validate block
        if await self._validate_block(new_block):
            self.chain.append(new_block)
            self.pending_transactions = []
            await self._notify_block_creation(new_block)
            return new_block
        return None
        
    async def _validate_block(self, block: Block) -> bool:
        """Validate block integrity and transactions"""
        # Verify block hash
        if not block.hash.startswith("0" * self.difficulty):
            return False
            
        # Verify previous hash
        if block.previous_hash != self.chain[-1].hash:
            return False
            
        # Verify transactions
        for transaction in block.data["transactions"]:
            if not await self._verify_signature(transaction):
                return False
                
        return True
        
    async def _sign_command(self, command: Dict) -> str:
        """Sign command with node's private key"""
        command_string = json.dumps(command, sort_keys=True)
        return hashlib.sha256(command_string.encode()).hexdigest()
        
    async def _verify_signature(self, transaction: Dict) -> bool:
        """Verify transaction signature"""
        command = transaction["command"]
        signature = transaction["signature"]
        expected_signature = await self._sign_command(command)
        return signature == expected_signature
        
    async def _notify_block_creation(self, block: Block):
        """Notify system of new block creation"""
        await self.system_controller.event_manager.publish(
            SystemEvent(
                event_type=SystemEventType.BLOCKCHAIN_BLOCK_CREATED,
                component_id="blockchain_controller",
                data={
                    "block_hash": block.hash,
                    "transaction_count": len(block.data["transactions"]),
                    "timestamp": block.timestamp
                },
                priority=1
            )
        )
        
    async def get_command_history(self) -> List[Dict]:
        """Retrieve command history from blockchain"""
        history = []
        for block in self.chain[1:]:  # Skip genesis block
            for transaction in block.data["transactions"]:
                history.append({
                    "timestamp": transaction["timestamp"],
                    "command": transaction["command"],
                    "block_hash": block.hash
                })
        return history