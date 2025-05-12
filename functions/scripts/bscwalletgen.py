from eth_account import Account
from mnemonic import Mnemonic
from eth_utils import to_checksum_address

def generate_bsc_wallet():
    mnemo = Mnemonic("english")
    mnemonic = mnemo.generate(strength=128)
    seed = mnemo.to_seed(mnemonic)
    #Dont't even know what enable_unaudited_hdwallet_features even does
    Account.enable_unaudited_hdwallet_features()
    account = Account.from_mnemonic(mnemonic)
    private_key = account.key.hex()
    address = to_checksum_address(account.address)
    return {
        'mnemonic': mnemonic,
        'private_key': private_key,
        'address': address
    }

# Example usage
if __name__ == "__main__":
    wallet = generate_bsc_wallet()
    print("Mnemonic:", wallet['mnemonic'])
    print("Private Key:", wallet['private_key'])
    print("Address:", wallet['address'])
