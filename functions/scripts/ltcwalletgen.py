# Simplified version for compatibility
from mnemonic import Mnemonic
from hdwallet import HDWallet
from hdwallet.cryptocurrencies import Litecoin
from hdwallet.seeds import BIP39Seed
import binascii


def generate_litecoin_wallet():
    mnemo = Mnemonic("english")
    mnemonic = mnemo.generate(strength=128)
    print(f"Mnemonic: {mnemonic}")
    
    # Generate seed bytes from mnemonic
    seed_bytes = mnemo.to_seed(mnemonic)
    seed_hex = binascii.hexlify(seed_bytes).decode()
    
    # Create BIP39 seed object from seed bytes
    seed = BIP39Seed(seed=seed_hex)
    
    # Create HDWallet instance
    hdwallet = HDWallet(cryptocurrency=Litecoin)
    
    # Initialize from seed
    hdwallet.from_seed(seed=seed)
    
    # Get wallet data (using default derivation)
    ltc_address = hdwallet.address()
    ltc_private_key = hdwallet.private_key()
    
    return {
        'mnemonic': mnemonic,
        'private_key': ltc_private_key,
        'bech32_address': ltc_address
    }

