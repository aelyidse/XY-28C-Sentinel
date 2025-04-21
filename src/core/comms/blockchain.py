from dataclasses import dataclass
from typing import List, Dict, Optional
import hashlib
import json
from datetime import datetime
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding

@dataclass
class CommandTransaction:
    command_id: str
    command_type: str
    parameters: Dict[str, Any]
    timestamp: float
    signature: Optional[bytes] = None
    previous_hash: Optional[str] = None

class CommandBlockchain:
    def __init__(self):
        self.chain: List[CommandTransaction] = []
        self.pending_transactions: List[CommandTransaction] = []
        self.node_keys = self._generate_node_keys()
        self.consensus_threshold = 0.67  # 2/3 majority for BFT
        self.node_weights = {
            'ground_station': 0.4,
            'uav': 0.3,
            'satellite': 0.3
        }

    def _generate_node_keys(self) -> Dict[str, rsa.RSAPrivateKey]:
        """Generate RSA key pairs for network nodes"""
        return {
            'ground_station': rsa.generate_private_key(public_exponent=65537, key_size=2048),
            'uav': rsa.generate_private_key(public_exponent=65537, key_size=2048),
            'satellite': rsa.generate_private_key(public_exponent=65537, key_size=2048)
        }

    def create_transaction(self, command: Dict[str, Any]) -> CommandTransaction:
        """Create a new command transaction"""
        tx = CommandTransaction(
            command_id=hashlib.sha256(json.dumps(command).encode()).hexdigest(),
            command_type=command['type'],
            parameters=command['parameters'],
            timestamp=datetime.now().timestamp(),
            previous_hash=self.get_last_block_hash()
        )
        return self._sign_transaction(tx)

    def _sign_transaction(self, tx: CommandTransaction) -> CommandTransaction:
        """Sign transaction with node private key"""
        private_key = self.node_keys['ground_station']
        tx_data = f"{tx.command_id}{tx.command_type}{json.dumps(tx.parameters)}{tx.timestamp}"
        tx.signature = private_key.sign(
            tx_data.encode(),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        return tx

    def validate_transaction(self, tx: CommandTransaction) -> bool:
        """Validate transaction signature and structure"""
        try:
            public_key = self.node_keys['ground_station'].public_key()
            tx_data = f"{tx.command_id}{tx.command_type}{json.dumps(tx.parameters)}{tx.timestamp}"
            public_key.verify(
                tx.signature,
                tx_data.encode(),
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            return True
        except Exception:
            return False

    def add_block(self, tx: CommandTransaction) -> None:
        """Add validated transaction to the chain"""
        if self.validate_transaction(tx):
            self.chain.append(tx)

    def get_last_block_hash(self) -> str:
        """Get hash of last block in chain"""
        if not self.chain:
            return "genesis"
        last_block = self.chain[-1]
        return hashlib.sha256(
            f"{last_block.command_id}{last_block.timestamp}".encode()
        ).hexdigest()

    async def validate_consensus(self, proposed_chain: List[CommandTransaction]) -> bool:
        """Validate chain using Byzantine Fault Tolerant consensus"""
        # Get validation votes from all nodes
        votes = await self._collect_validation_votes(proposed_chain)
        
        # Calculate weighted consensus
        total_weight = sum(
            self.node_weights[node] for node, vote in votes.items() if vote
        )
        
        return total_weight >= self.consensus_threshold

    async def _collect_validation_votes(self, chain: List[CommandTransaction]) -> Dict[str, bool]:
        """Collect validation votes from all nodes"""
        votes = {}
        
        # Validate locally first
        votes['local'] = self._validate_chain_integrity(chain)
        
        # Get remote node votes (simulated for now)
        for node in ['ground_station', 'uav', 'satellite']:
            votes[node] = await self._get_remote_vote(node, chain)
            
        return votes

    def _validate_chain_integrity(self, chain: List[CommandTransaction]) -> bool:
        """Validate chain structure and signatures"""
        if not chain:
            return False
            
        # Check all transactions are valid
        if not all(self.validate_transaction(tx) for tx in chain):
            return False
            
        # Check chain continuity
        for i in range(1, len(chain)):
            if chain[i].previous_hash != self._calculate_block_hash(chain[i-1]):
                return False
                
        return True

    async def _get_remote_vote(self, node: str, chain: List[CommandTransaction]) -> bool:
        """Get validation vote from remote node (simulated)"""
        # In real implementation would make network request
        return True  # Simulating successful validation