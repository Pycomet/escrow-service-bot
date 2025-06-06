import inspect
from globalState import GlobalState
def generateWallet(action_id: str, bot_state: GlobalState):
    caller_frame = inspect.stack()[1]
    tradeDetails = {}
    if action_id.startswith('TRADE'):
        tradeDetails = bot_state.get_var(action_id)
    elif action_id.startswith('TXID'):
        tradeDetails = bot_state.get_tx_var(action_id)
    else:
        print(f"Invalid action id supplied: {action_id}")
        return False
    if tradeDetails['currency'] == 'LTC':
        import imports.ltcwalletgen as m
        wallet = m.generate_litecoin_wallet();
        bot_state.save_wallet_info(action_id, wallet['mnemonic'], wallet['private_key'], wallet['bech32_address'], 'LTC',inspect.getmodule(caller_frame[0]).__name__.split('.')[1])
        return wallet['bech32_address']
    elif tradeDetails['currency'] == 'SOL (Solana)' or tradeDetails['currency'] == 'USDT (Solana)':
        from imports.solwalletgen import generate_solana_wallet
        wallet = generate_solana_wallet()
        bot_state.save_wallet_info(action_id, wallet['mnemonic'], wallet['private_key'], wallet['public_address'], 'SOL', inspect.getmodule(caller_frame[0]).__name__.split('.')[1])
        return wallet['public_address']
    elif tradeDetails['currency'] == 'BNB (BSC Bep-20)' or tradeDetails['currency'] == 'USDT (BSC Bep-20)':
        from imports.bscwalletgen import generate_bsc_wallet
        wallet = generate_bsc_wallet()
        bot_state.save_wallet_info(action_id, wallet['mnemonic'], wallet['private_key'], wallet['address'], 'BSC', inspect.getmodule(caller_frame[0]).__name__.split('.')[1])
        return wallet['address']
    elif tradeDetails['currency'] == 'DOGE':
        from imports.dogewalletgen import generate_doge_wallet
        wallet = generate_doge_wallet()
        bot_state.save_wallet_info(action_id, wallet['mnemonic'], wallet['private_key'], wallet['address'], 'DOGE', inspect.getmodule(caller_frame[0]).__name__.split('.')[1])
        return wallet['address']

def sendtrans(bot_state: GlobalState, action_id: str):
    tradeDetails = {}
    if action_id.startswith('TRADE'):
        tradeDetails = bot_state.get_var(action_id)
    elif action_id.startswith('TXID'):
        tradeDetails = bot_state.get_tx_var(action_id)
        tradeDetails['sellerAddress'] = bot_state.get_item_details(tradeDetails['item_id'])['sellerAddress']
        bot_state.set_tx_var(action_id, tradeDetails)
    else:
        print(f"Invalid action id supplied: {action_id}")
        return False
    if tradeDetails['currency'] =='LTC':
        import imports.ltctransactionsender as ms
        ms.send_transaction(bot_state, action_id)
    elif tradeDetails['currency'] == 'USDT (Solana)':
        from imports.usdt_sol_sender import send_usdt_sol_transaction
        send_usdt_sol_transaction(action_id=action_id, bot_state=bot_state)
    elif tradeDetails['currency'] == 'SOL (Solana)':
        from imports.simple_sol_to_sol_sender import simple_sol_to_sol_transaction
        simple_sol_to_sol_transaction(action_id=action_id, bot_state=bot_state)
    elif tradeDetails['currency'] == 'USDT (BSC Bep-20)':
        from imports.usdt_bnb_sender import usdt_bnb_transaction
        usdt_bnb_transaction(action_id, bot_state)
    elif tradeDetails['currency'] == 'BNB (BSC Bep-20)':
        from imports.simple_bnb_transaction import send_bnb_transaction
        send_bnb_transaction(action_id, bot_state)
    elif tradeDetails['currency'] == 'DOGE':
        from imports.doge_transaction_sender import send_transaction
        send_transaction(bot_state, action_id)
