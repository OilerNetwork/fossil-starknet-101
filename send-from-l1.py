import os
from dotenv import load_dotenv
from web3 import Web3
from web3.middleware import geth_poa_middleware

eth_provider_url = "http://94.237.54.114:8550/"
provider = Web3.HTTPProvider(eth_provider_url)
web3 = Web3(provider)
web3.middleware_onion.inject(geth_poa_middleware, layer=0)
load_dotenv()

l1_sender_address = os.getenv("ETHEREUM_SYNC_CONTRACT_ADDR")
abi = [
    {
      "inputs": [
        {
          "internalType": "contract IStarknetCore",
          "name": "starknetCore_",
          "type": "address"
        },
        {
          "internalType": "uint256",
          "name": "l2RecipientAddr_",
          "type": "uint256"
        }
      ],
      "stateMutability": "nonpayable",
      "type": "constructor"
    },
    {
      "inputs": [],
      "name": "l2RecipientAddr",
      "outputs": [
        {
          "internalType": "uint256",
          "name": "",
          "type": "uint256"
        }
      ],
      "stateMutability": "view",
      "type": "function"
    },
    {
      "inputs": [
        {
          "internalType": "uint256",
          "name": "blockNumber_",
          "type": "uint256"
        }
      ],
      "name": "sendExactParentHashToL2",
      "outputs": [],
      "stateMutability": "nonpayable",
      "type": "function"
    },
    {
      "inputs": [],
      "name": "sendLatestParentHashToL2",
      "outputs": [],
      "stateMutability": "nonpayable",
      "type": "function"
    },
    {
      "inputs": [],
      "name": "starknetCore",
      "outputs": [
        {
          "internalType": "contract IStarknetCore",
          "name": "",
          "type": "address"
        }
      ],
      "stateMutability": "view",
      "type": "function"
    }
  ]

start_block_child = 6876070
contract_instance = web3.eth.contract(address=l1_sender_address, abi=abi)
nonce = web3.eth.getTransactionCount(os.getenv("ETHEREUM_PUBKEY"), 'latest')
public_key = os.getenv("ETHEREUM_PUBKEY")
transaction = contract_instance.functions.sendExactParentHashToL2(start_block_child).buildTransaction({
    'gas': 100000,
    'gasPrice': web3.toWei('1', 'gwei'),
    'from': public_key,
    'nonce': nonce
    }) 
private_key = os.getenv("ETHEREUM_PRIVKEY") 
signed_txn = web3.eth.account.signTransaction(transaction, private_key=private_key)
web3.eth.sendRawTransaction(signed_txn.rawTransaction)

