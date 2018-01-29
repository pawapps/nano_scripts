import json
import os
import requests
import datetime
import atexit

LOG='log_wallet.txt'
PASSWORD = 'password'
SCRIPT_LOC='/home/ubuntu/'
ALIVE_MINS=60

##########
# System
##

def timestamp(when=None):
    """ Returns now as string timestamp """
    if not when:
        when = datetime.datetime.now()
    return '{:%Y-%m-%d %H:%M:%S.%f}'.format(when)

def append_file(fn, value):
    """ Appends value to fn """
    with open(fn, 'a') as f:
        f.write('{}\n'.format(value))

def log(msg, stdout=True):
    """Logs
    """
    entry = '{}: {}'.format(timestamp(), msg)
    append_file(SCRIPT_LOC + LOG, entry)
    if stdout:
        print(entry)

@atexit.register
def last_log():
    """Log when exiting
    """
    log('EXITING')

##########
# RPC
##

def get_connection():
    protocol = os.getenv('RAI_PROTOCOL', default='http')
    host = os.getenv('RAI_HOST', default='[::1]')
    port = os.getenv('RAI_PORT', default='7076')

    return "{protocol}://{host}:{port}".format(
        protocol=protocol,
        host=host,
        port=port
    )


def make_rpc(payload):
    rsp = requests.post(
        url=get_connection(),
        json=payload
    )
    return json.loads(
        rsp.content.decode('utf-8')
    )

##########
# Validators
##

def valid_block_id(block_id):
    """Returns True if block_id is valid
    Returns False if block_id is not valid
    """
    valid = True

    # Valid length
    valid = valid and len(block_id) == 64
    
    # Valid characters
    valid_chars = 'ABCDEF1234567890'
    tmp_block_id = str(block_id.upper())
    for valid_char in valid_chars:
        tmp_block_id = tmp_block_id.replace(valid_char, '')
    valid = valid and len(tmp_block_id) == 0

    return valid

def valid_account_id(account_id):
    """Returns True if account_id is valid
    Returns False if account_id is not valid
    """
    valid = True

    # Valid length
    valid = valid and len(account_id) == 64

    # Valid characters
    valid_chars = '_ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890'
    tmp_account_id = str(account_id.upper())
    for valid_char in valid_chars:
        tmp_account_id = tmp_account_id.replace(valid_char, '')
    valid = valid and len(tmp_account_id) == 0

    return valid

def valid_transfer_value(transfer_value):
    """Returns True if transfer_value is valid
    Returns False if transfer_value is not valid
    """
    try:
        int(transfer_value)
    except:
        return False
    return True

##########
# Password
##

def wallet_check(wallet):
    """Checks whether wallet is locked
    Response:
    {
      "locked": 0
    }
    """
    data = {
        'action': 'wallet_locked',
        'wallet': wallet,
    }
    rsp = make_rpc(data)
    return rsp

def wallet_unlock(wallet, password):
    """Enters the password in to wallet
    Response:
    {
      "valid": "1"
    }
    """
    data = {
        'action': 'password_enter',
        'wallet': wallet,
        'password': password,
    }

    rsp = make_rpc(data)
    return rsp

##########
# Account
##

def account_history(account, count=1):

    rsp = make_rpc({
        'action': 'account_history',
        'account': account,
        'count': count
    })
    return rsp

def account_pending(account, count=1, threshold=0):
    """Returns a list of block hashes which have not yet been 
    received by this account.
    ** LAST IN FIRST OUT (most recent pending is shown if count is 1) **
    Response:
    {  
      "blocks" : {    
            "000D1BAEC8EC208142C99059B393051BAC8380F9B5A2E6B2489A277D81789F3F": {   
                 "amount": "6000000000000000000000000000000",       
                 "source": "xrb_3dcfozsmekr1tr9skf1oa5wbgmxt81qepfdnt7zicq5x3hk65fg4fqj58mbr"  
            }   
        }  
    }    
    """
    data = {
        'action': 'pending',
        'account': account,
        'count': count,
        'source': 'true',
    }
    if threshold > 0:
        data['threshold'] = threshold

    rsp = make_rpc(data)
    return rsp

def account_receive(wallet, account, block):
    """enable_control required
    Receive pending block for account in wallet
    Response:
    {  
      "block": "EE5286AB32F580AB65FD84A69E107C69FBEB571DEC4D99297E19E3FA5529547B"  
    }
    """
    data = {
        'action': 'receive',
        'wallet': wallet,
        'account': account,
        'block': block,
    }

    rsp = make_rpc(data)
    return rsp

def account_send(wallet, source, destination, amount):
    """enable_control required
    Send amount from source in wallet to destination
    Response:
    {  
      "block": "000D1BAEC8EC208142C99059B393051BAC8380F9B5A2E6B2489A277D81789F3F"  
    }
    """
    data = {
        'action': 'send',
        'wallet': wallet,
        'source': source,
        'destination': destination,
        'amount': amount,
    }

    rsp = make_rpc(data)
    return rsp

def account_balance(account):
    """Returns how many RAW is owned and how many have not yet been received by account
    Response:
    {  
      "balance": "10000",  
      "pending": "10000"  
    }
    """
    data = {
        'action': 'account_balance',
        'account': account,
    }

    rsp = make_rpc(data)
    return rsp

##########
# Macros
def macro_unlock_wallet(wallet):
    """Unlocks given wallet
    Returns True if success, False otherwise
    """
    rsp = wallet_check(wallet)
    if 'error' in  rsp.keys():
        return False

    if rsp['locked'] == '1':
        rsp = wallet_unlock(wallet, PASSWORD)
        if rsp['valid'] != '1':
            raise Exception('Invalid Password when unlocking Wallet {}'.format(wallet))
        rsp = wallet_check(wallet)
    success = rsp['locked'] == '0'
    log('Wallet unlock attempted.  Success: {}'.format(success))
    return success

def macro_lock_wallet(wallet):
    """Locks given wallet
    Returns True if success, False otherwise
    """
    rsp = wallet_unlock(wallet, '')
    if 'error' in rsp.keys():
        return False

    rsp = wallet_check(wallet)
    success = rsp['locked'] == '1'
    log('Wallet lock attempted.  Success: {}'.format(success))
    return success

def macro_receive_pending(wallet, account, threshold=0):
    """Receives inbound block if one exists
    If exists, returns dictionary of values
    If none exists, returns None
    """
    ret = {
        'message': 'receive',
        'wallet': wallet,
        'destination': account,
        'threshold': threshold,
        'send_block_id': None,
        'source': None,
        'amount': None,
        'receive_block_id': None,
        'pending_success': False,
        'receive_success': False
    }

    pending_rsp = account_pending(account, count=1, threshold=threshold)
    try:
        # Validate return
        send_block_id = list(pending_rsp['blocks'].keys())[0]
        assert(valid_block_id(send_block_id))
        ret['send_block_id'] = send_block_id

        account_id = pending_rsp['blocks'][send_block_id]['source']
        assert(valid_account_id(account_id))
        ret['source'] = account_id

        transfer_value = pending_rsp['blocks'][send_block_id]['amount']
        assert(valid_transfer_value(transfer_value))
        ret['amount'] = int(transfer_value)

    except AssertionError as e:
        log('Invalid pending block {} {}'.format(e, pending_rsp))
        return ret
    except:
        return ret

    ret['pending_success'] = True
    log('Pending send block found: Hash: {} Source: {} Amount: {}'.format(
        send_block_id,
        account_id,
        transfer_value
    ))

    #if macro_unlock_wallet(wallet) == False:
    #    return ret

    receive_rsp = account_receive(wallet, account, send_block_id)

   # macro_lock_wallet(wallet)

    try:
        # Validate return
        receive_block_id = receive_rsp['block']
        assert(valid_block_id(receive_block_id))
        ret['receive_block_id'] = receive_block_id

    except AssertionError as e:
        log('Invalid receive block {} {}'.format(e, receive_rsp))
        return ret
    except Exception as e:
        log('Error receiving block {} {}'.format(e, receive_rsp))
        return ret

    ret['receive_success'] = True
    log('Receive block processed: Hash: {}'.format(receive_block_id))

    return ret

def macro_send(wallet, source, destination, amount):
    """Sends block of given value to destination account
    """
    ret = {
        'message': 'send',
        'wallet': wallet,
        'destination': destination,
        'send_block_id': None,
        'source': source,
        'amount': str(amount),
        'send_success': False
    }
    log('Creating send block: Wallet: {} Source: {} Destination: {} Amount: {}'.format(
        wallet,
        source,
        destination,
        amount
    ))

    #if macro_unlock_wallet(wallet) == False:
    #    return ret
    send_rsp = account_send(wallet, source, destination, amount)
    #macro_lock_wallet(wallet)

    try:
        # Validate return
        send_block_id = send_rsp['block']
        assert(valid_block_id(send_block_id))
        ret['send_block_id'] = send_block_id

    except AssertionError as e:
        log('Invalid send block {} {}'.format(e, send_rsp))
        return ret
    except Exception as e:
        log('Error sending block {} {}'.format(e, send_rsp))
        return ret

    ret['send_success'] = True
    log('Send block processed: Hash: {}'.format(send_block_id))

    return ret


def macro_balance(account):
    """Gets balance of account
    Returns tuple (balance, pending)
    Returns None if error
    """
    balance_rsp = account_balance(account)
    try:
        # Validate return
        balance_actual = int(balance_rsp['balance'])
        balance_pending = int(balance_rsp['pending'])
    except Exception as e:
        log('Error retrieving balance {} {}'.format(e, balance_rsp))
        return None, None

    log('Account {} balance: {} pending: {}'.format(
        account, 
        balance_actual,
        balance_pending
    ))

    return balance_actual, balance_pending


##########
# Test
##

def mirror(account, wallet):

    while True:

        # Check for stop message
        if os.path.exists('{}/stop'.format(SCRIPT_LOC)):
            os.remove('{}/stop'.format(SCRIPT_LOC))
            return

        # Time for alive log?
        try:
            now = datetime.datetime.now()
            assert(now-alive_last < datetime.timedelta(minutes=ALIVE_MINS))
        except:
            log('ALIVE')
            alive_last = now

        # Check for pending messages
        receive_dict = macro_receive_pending(wallet, account)
        
        if receive_dict['receive_success'] == True:
            balance_actual, balance_pending = macro_balance(account)
            send_dict = macro_send(wallet, account, receive_dict['source'], receive_dict['amount'])
        
            if send_dict['send_success'] == True:
                balance_actual, balance_pending = macro_balance(account)
                return
    


if __name__ == '__main__':
    account_1 = 'xrb_abcdef1234...'
    wallet = 'ABCD1234...'
    account_2 = 'xrb_1234abcd...'
    macro_balance(account_1)
    macro_balance(account_2)
    #exit(0)
    macro_unlock_wallet(wallet)
    #while True:
    #    receive_dict = macro_receive_pending(wallet, account_1)
    macro_send(wallet, account_2, account_1, 1000000000000000000000000)
    #mirror(account_1, wallet)
    while True:
        log('#')
        log('# Monitoring Account 1')
        log('#')
        mirror(account_1, wallet)
        log('#')
        log('# Monitoring Account 2')
        log('#')
        mirror(account_2, wallet)
        
    macro_lock_wallet(wallet)
