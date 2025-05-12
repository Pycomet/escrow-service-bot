from hdwallet import HDWallet
from hdwallet.symbols import DOGE
from mnemonic import Mnemonic
import binascii

def generate_doge_wallet():
    mnemo = Mnemonic("english")
    mnemonic_phrase = mnemo.generate(strength=128)
    seed = mnemo.to_seed(mnemonic_phrase, passphrase="")
    seed_hex = binascii.hexlify(seed).decode('utf-8')
    hdwallet = HDWallet(symbol=DOGE)
    hdwallet.from_seed(seed_hex)
    hdwallet.from_path("m/44'/3'/0'/0/0")
    private_key = hdwallet.private_key()
    address = hdwallet.p2pkh_address()
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
