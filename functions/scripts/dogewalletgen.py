from hdwallet import HDWallet
from hdwallet.cryptocurrencies import Dogecoin
from hdwallet.seeds import BIP39Seed
from mnemonic import Mnemonic
import binascii

def generate_doge_wallet():
    mnemo = Mnemonic("english")
    mnemonic_phrase = mnemo.generate(strength=128)
    
    # Generate seed bytes from mnemonic
    seed_bytes = mnemo.to_seed(mnemonic_phrase)
    seed_hex = binascii.hexlify(seed_bytes).decode()
    
    # Create BIP39 seed object from seed bytes
    seed = BIP39Seed(seed=seed_hex)
    
    # Create HDWallet instance
    hdwallet = HDWallet(cryptocurrency=Dogecoin)
    
    # Initialize from seed
    hdwallet.from_seed(seed=seed)
    
    # Get wallet data (using default derivation)
    private_key = hdwallet.private_key()
    address = hdwallet.address()
    
    return {
        "mnemonic": mnemonic_phrase,
        "private_key": private_key,
        "address": address
    }

# if __name__ == "__main__":
#     wallet = generate_doge_wallet()
#     print("Mnemonic:", wallet["mnemonic"])
#     print("Private Key:", wallet["private_key"])
#     print("Address:", wallet["address"])
