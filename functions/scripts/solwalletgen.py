from mnemonic import Mnemonic
from solders.keypair import Keypair
import hashlib
from solders.pubkey import Pubkey
from nacl.signing import SigningKey
import hashlib

def generate_solana_wallet():
    mnemo = Mnemonic("english")
    mnemonic_phrase = mnemo.generate(strength=128)
    seed = mnemo.to_seed(mnemonic_phrase)
    seed_bytes = hashlib.sha256(seed).digest()[:32]
    signing_key = SigningKey(seed_bytes)
    private_key = signing_key.encode()
    public_key = signing_key.verify_key.encode()
    full_key = private_key + public_key
    solana_keypair = Keypair.from_bytes(full_key)
    public_address = str(solana_keypair.pubkey())
    return {
        'mnemonic': mnemonic_phrase,
        'private_key': private_key.hex(),
        'public_address': public_address
    }

# Example usage
# wallet = generate_solana_wallet()
# print("Mnemonic:", wallet['mnemonic'])
# print("Private Key:", wallet['private_key'])
# print("Public Address:", wallet['public_address'])
