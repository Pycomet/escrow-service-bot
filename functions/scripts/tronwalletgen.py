from tronpy.keys import PrivateKey
from mnemonic import Mnemonic

def generate_tron_wallet():
    mnemo = Mnemonic("english")
    mnemonic = mnemo.generate(strength=128)
    seed = mnemo.to_seed(mnemonic)
    private_key = PrivateKey(seed[:32])  
    address = private_key.public_key.to_base58check_address()
    
    return {
        'mnemonic': mnemonic,
        'private_key': private_key.hex(),
        'address': address
    }


if __name__ == "__main__":
    wallet = generate_tron_wallet()
    print("Mnemonic:", wallet['mnemonic'])
    print("Private Key:", wallet['private_key'])
    print("Address:", wallet['address'])
