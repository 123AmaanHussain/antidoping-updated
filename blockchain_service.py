from web3 import Web3
import json
import os
from datetime import datetime
from eth_account import Account
from typing import Optional
import time

class BlockchainService:
    def __init__(self):
        # Connect to local blockchain (Ganache)
        self.w3 = Web3(Web3.HTTPProvider('http://127.0.0.1:7545'))
        if not self.w3.is_connected():
            raise Exception("Failed to connect to Ethereum network")
        
        # Load contract ABI and address
        contract_path = os.path.join('blockchain', 'build', 'contracts', 'AntidopingCertificate.json')
        with open(contract_path) as f:
            contract_json = json.load(f)
            self.contract_abi = contract_json['abi']
            networks = contract_json.get('networks', {})
            if not networks:
                raise ValueError("No deployed networks found in contract JSON")
            network_id = list(networks.keys())[-1]
            self.contract_address = networks[network_id]['address']
        
        print(f"Contract address from deployment: {self.contract_address}")
        
        # Initialize contract
        self.contract = self.w3.eth.contract(
            address=self.w3.to_checksum_address(self.contract_address),
            abi=self.contract_abi
        )
        
        # Set up account with private key
        private_key = '0x54cd5a0f68b87c1c828e2a872dc1f0e199ae902cf93f30948bda55bf5e5dd24c'
        self.account = Account.from_key(private_key)
        self.w3.eth.default_account = self.account.address
        print(f"Initialized with account: {self.account.address}")

    def mint_certificate(self, recipient_address: str, quiz_title: str, score: int, ipfs_hash: Optional[str] = None) -> str:
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                print(f"\n=== Minting Certificate (Attempt {attempt + 1}) ===")
                print(f"Recipient: {recipient_address}")
                date = datetime.now().strftime('%Y-%m-%d')
                ipfs_hash = ipfs_hash or ''
                
                # Convert address to checksum format
                recipient_address = self.w3.to_checksum_address(recipient_address)
                
                # Get optimized gas price (10% higher than base for faster confirmation)
                gas_price = int(self.w3.eth.gas_price * 1.1)
                
                # Estimate gas with the actual parameters
                estimated_gas = self.contract.functions.mintCertificate(
                    recipient_address,
                    quiz_title,
                    score,
                    date,
                    ipfs_hash
                ).estimate_gas({'from': self.account.address})
                
                # Add 20% buffer to estimated gas
                gas_limit = int(estimated_gas * 1.2)
                
                # Build transaction with optimized parameters
                tx = self.contract.functions.mintCertificate(
                    recipient_address,
                    quiz_title,
                    score,
                    date,
                    ipfs_hash
                ).build_transaction({
                    'from': self.account.address,
                    'nonce': self.w3.eth.get_transaction_count(self.account.address),
                    'gas': gas_limit,
                    'gasPrice': gas_price,
                })
                
                print(f"Transaction built with gas limit: {gas_limit}")
                
                # Sign and send transaction
                signed_tx = self.w3.eth.account.sign_transaction(tx, private_key=self.account.key)
                tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
                print(f"Transaction sent with hash: {self.w3.to_hex(tx_hash)}")
                
                # Wait for transaction receipt with timeout
                receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
                print(f"Transaction confirmed in block {receipt['blockNumber']}")
                
                if receipt['status'] == 1:
                    # Get the token ID from the event logs
                    transfer_event = self.contract.events.Transfer().process_receipt(receipt)
                    if transfer_event:
                        token_id = transfer_event[0]['args']['tokenId']
                        print(f"Certificate minted with token ID: {token_id}")
                        return str(token_id)
                    return self.w3.to_hex(tx_hash)
                else:
                    raise Exception("Transaction failed")
                
            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"\nAttempt {attempt + 1} failed: {str(e)}")
                    print("Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    continue
                print(f"\nAll attempts failed. Last error: {str(e)}")
                raise Exception(f"Failed to mint certificate after {max_retries} attempts: {str(e)}")

    def verify_certificate(self, token_id: int, expected_recipient: Optional[str] = None) -> dict:
        try:
            # Get certificate data
            certificate = self.get_certificate(token_id)
            if not certificate['success']:
                return {
                    'success': False,
                    'error': 'Certificate not found'
                }
            
            # Verify owner
            owner = self.contract.functions.ownerOf(token_id).call()
            
            # Get token URI if available
            token_uri = None
            try:
                token_uri = self.contract.functions.tokenURI(token_id).call()
            except:
                pass
            
            # Get transfer history
            transfer_events = self.contract.events.Transfer.get_logs(
                fromBlock=0,
                toBlock='latest',
                argument_filters={'tokenId': token_id}
            )
            
            # Get block timestamps for each transfer
            transfers_with_time = []
            for event in transfer_events:
                block = self.w3.eth.get_block(event['blockNumber'])
                transfers_with_time.append({
                    'from': event['args']['from'],
                    'to': event['args']['to'],
                    'block_number': event['blockNumber'],
                    'timestamp': datetime.fromtimestamp(block['timestamp']).isoformat(),
                    'transaction_hash': event['transactionHash'].hex()
                })
            
            return {
                'success': True,
                'is_valid': True,
                'owner': owner,
                'matches_recipient': not expected_recipient or owner.lower() == expected_recipient.lower(),
                'data': certificate['data'],
                'token_uri': token_uri,
                'history': transfers_with_time
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def get_certificate(self, token_id: int) -> dict:
        try:
            certificate = self.contract.functions.getCertificate(token_id).call()
            return {
                'success': True,
                'data': {
                    'quiz_title': certificate[0],
                    'score': certificate[1],
                    'date': certificate[2],
                    'recipient': certificate[3],
                    'ipfs_hash': certificate[4]
                }
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def get_user_certificates(self, user_address: str) -> dict:
        try:
            # Convert address to checksum format
            user_address = self.w3.to_checksum_address(user_address)
            
            token_ids = self.contract.functions.getCertificatesByOwner(user_address).call()
            certificates = []
            
            for token_id in token_ids:
                cert_data = self.get_certificate(token_id)
                if cert_data['success']:
                    # Get verification details
                    verification = self.verify_certificate(token_id)
                    certificates.append({
                        'token_id': token_id,
                        'verification': verification,
                        **cert_data['data']
                    })
            
            return {
                'success': True,
                'certificates': certificates
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
