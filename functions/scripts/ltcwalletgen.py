# THIS IS NEW VERSION
from mnemonic import Mnemonic
from hdwallet import HDWallet
from hdwallet.symbols import LTC as SYMBOL
from binascii import hexlify


def generate_litecoin_wallet():
    mnemo = Mnemonic("english")
    mnemonic = mnemo.generate(strength=128)
    print(f"Mnemonic: {mnemonic}")
    seed = mnemo.to_seed(mnemonic)
    seed_hex = hexlify(seed).decode()
    hdwallet = HDWallet(symbol=SYMBOL, use_default_path=False)
    hdwallet.from_seed(seed=seed_hex)
    hdwallet.from_path("m/84'/2'/0'/0/0")
    ltc_address = hdwallet.p2wpkh_address()
    ltc_private_key = hdwallet.private_key()
    mnemonic = mnemonic
    private_key = ltc_private_key
    bech32_address = ltc_address
    return {
        'mnemonic': mnemonic,
        'private_key': private_key,
        'bech32_address': bech32_address
    }

