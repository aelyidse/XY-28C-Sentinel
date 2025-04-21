from dataclasses import dataclass
from typing import Dict, List, Optional
import random
import asyncio
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes
from .low_latency_crypto import LowLatencyCrypto

@dataclass
class ChannelConfig:
    frequency: float  # MHz
    bandwidth: float  # MHz
    protocol: str
    encryption_key: Optional[bytes] = None

class JammingResistantProtocol:
    def __init__(self, secure_comm: SecureCommunication):
        self.secure_comm = secure_comm
        self.spread_spectrum_enabled = True
        self.frequency_hopping_rate = 1000  # hops per second
        self.power_threshold = -80  # dBm
        self.jamming_detection_window = 0.1  # seconds
        self.interference_threshold = 0.3  # 30% interference tolerance
        
    async def encode_data(self, data: bytes) -> bytes:
        """Apply spread spectrum encoding to data"""
        # Direct Sequence Spread Spectrum (DSSS) implementation
        spreading_code = self._generate_spreading_code(len(data))
        return bytes(d ^ s for d, s in zip(data, spreading_code))
        
    async def decode_data(self, encoded: bytes) -> bytes:
        """Decode spread spectrum data"""
        spreading_code = self._generate_spreading_code(len(encoded))
        return bytes(e ^ s for e, s in zip(encoded, spreading_code))
        
    def _generate_spreading_code(self, length: int) -> bytes:
        """Generate pseudo-random spreading code"""
        return os.urandom(length)
        
    async def detect_jamming(self) -> bool:
        """Detect potential jamming attempts"""
        signal_strength = self.secure_comm.current_signal_strength
        error_rate = self.secure_comm.current_error_rate
        
        # Check for abnormal signal characteristics
        if signal_strength > self.power_threshold and error_rate > self.interference_threshold:
            return True
            
        return False
        
    async def mitigate_jamming(self) -> None:
        """Implement jamming countermeasures"""
        if await self.detect_jamming():
            # Increase frequency hopping rate
            self.frequency_hopping_rate *= 2
            
            # Adjust power levels
            await self.secure_comm.adjust_power(1.5)
            
            # Switch to backup channels if needed
            if self.secure_comm.current_error_rate > 0.5:
                await self.secure_comm.attempt_recovery()

class SecureCommunication:
    def __init__(self, blockchain: CommandBlockchain):
        self.blockchain = blockchain
        self.active_channels: List[ChannelConfig] = []
        self.current_channel_index = 0
        self.hop_interval = 0.1  # seconds
        self._initialize_channels()
        self.crypto = LowLatencyCrypto()
        self.jamming_resistant = JammingResistantProtocol(self)
        self.current_signal_strength = -60  # dBm
        self.current_error_rate = 0.0     # 0-1 scale
        self.current_latency = 0.0         # seconds
        
    def _initialize_channels(self) -> None:
        """Initialize available communication channels"""
        self.available_channels = [
            ChannelConfig(frequency=2400 + i*100, bandwidth=20, protocol='OFDM')
            for i in range(10)
        ]
        self.active_channels = random.sample(self.available_channels, 3)
        
    async def start_frequency_hopping(self) -> None:
        """Start frequency hopping pattern"""
        while True:
            await self._hop_to_next_channel()
            await asyncio.sleep(self.hop_interval)
            
    async def _hop_to_next_channel(self) -> None:
        """Switch to next channel in sequence"""
        self.current_channel_index = (self.current_channel_index + 1) % len(self.active_channels)
        current_channel = self.active_channels[self.current_channel_index]
        await self._update_channel_config(current_channel)
        
    async def _update_channel_config(self, channel: ChannelConfig) -> None:
        """Update communication parameters for new channel"""
        # Generate new encryption key for channel
        channel.encryption_key = self._generate_channel_key()
        
        # Broadcast new channel configuration
        await self._broadcast_channel_update(channel)
        
    def _generate_channel_key(self) -> bytes:
        """Generate encryption key for current channel"""
        private_key = self.blockchain.node_keys['uav']
        return private_key.sign(
            str(self.current_channel_index).encode(),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        
    async def _broadcast_channel_update(self, channel: ChannelConfig) -> None:
        """Broadcast channel update to network"""
        tx = self.blockchain.create_transaction({
            'type': 'channel_update',
            'frequency': channel.frequency,
            'bandwidth': channel.bandwidth,
            'protocol': channel.protocol
        })
        await self.blockchain_network.broadcast_transaction(tx)
        
    async def send_message(self, message: str) -> bool:
        """Send message using jamming-resistant protocol"""
        # Encode message with spread spectrum
        encoded = await self.jamming_resistant.encode_data(message.encode())
        
        # Encrypt encoded message
        current_channel = self.active_channels[self.current_channel_index]
        encrypted = self._encrypt_message(encoded, current_channel.encryption_key)
        
        # Check for jamming before transmission
        if await self.jamming_resistant.detect_jamming():
            await self.jamming_resistant.mitigate_jamming()
            
        # Transmit message
        return await self._transmit_message(encrypted)
        
    async def receive_message(self, encrypted: bytes) -> str:
        """Receive and decode jamming-resistant message"""
        # Decrypt message
        current_channel = self.active_channels[self.current_channel_index]
        encoded = self._decrypt_message(encrypted, current_channel.encryption_key)
        
        # Decode spread spectrum
        decoded = await self.jamming_resistant.decode_data(encoded)
        
        return decoded.decode()
        
    async def adjust_power(self, factor: float) -> None:
        """Adjust transmission power"""
        # Would implement actual power adjustment in production
        pass
        
    def _encrypt_message(self, message: str, key: bytes) -> bytes:
        """Encrypt message using low-latency crypto"""
        # Use first 32 bytes of key for AES
        self.crypto.key = key[:32]
        nonce, ciphertext, tag = self.crypto.encrypt(message.encode())
        return nonce + ciphertext + tag
        
    def _decrypt_message(self, encrypted: bytes, key: bytes) -> str:
        """Decrypt message using low-latency crypto"""
        # Use first 32 bytes of key for AES
        self.crypto.key = key[:32]
        nonce = encrypted[:12]
        ciphertext = encrypted[12:-16]
        tag = encrypted[-16:]
        return self.crypto.decrypt(nonce, ciphertext, tag).decode()
        
    async def _transmit_message(self, encrypted: bytes) -> bool:
        """Transmit encrypted message and update metrics"""
        success = await self._actual_transmit(encrypted)
        
        # Update metrics (simplified example)
        self.current_signal_strength = self._calculate_signal_strength()
        self.current_error_rate = self._calculate_error_rate()
        self.current_latency = self._calculate_latency()
        
        return success
        """Transmit encrypted message (simulated)"""
        # Would implement actual transmission in production
        return True
        
    async def attempt_recovery(self) -> bool:
        """Attempt communication recovery"""
        # Try different channels and protocols
        for channel in self.available_channels:
            if await self._try_channel(channel):
                return True
        return False
        
    async def _try_channel(self, channel: ChannelConfig) -> bool:
        """Attempt to establish communication on a specific channel"""
        # Would implement actual channel testing in production
        return True