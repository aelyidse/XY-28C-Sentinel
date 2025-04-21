from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes
from dataclasses import dataclass
from typing import Dict, Any
import json

@dataclass
class SignedMissionParameters:
    parameters: Dict[str, Any]
    signature: bytes
    timestamp: float

class MissionSigner:
    def __init__(self, private_key):
        self.private_key = private_key

    def sign_parameters(self, parameters: Dict[str, Any]) -> SignedMissionParameters:
        """Sign mission parameters with private key"""
        # Serialize parameters deterministically
        serialized = json.dumps(parameters, sort_keys=True)
        
        # Create signature
        signature = self.private_key.sign(
            serialized.encode(),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        
        return SignedMissionParameters(
            parameters=parameters,
            signature=signature,
            timestamp=datetime.now().timestamp()
        )

class MissionVerifier:
    def __init__(self, public_key):
        self.public_key = public_key

    def verify_parameters(self, signed_params: SignedMissionParameters) -> bool:
        """Verify signed mission parameters"""
        try:
            # Serialize parameters deterministically
            serialized = json.dumps(signed_params.parameters, sort_keys=True)
            
            # Verify signature
            self.public_key.verify(
                signed_params.signature,
                serialized.encode(),
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            return True
        except Exception:
            return False