
import os
import asyncio
import json
from dotenv import load_dotenv

from web3 import Web3
from web3.middleware import geth_poa_middleware

from services.external_api.base_client import RetryConfig
from starkware.starknet.services.api.gateway.gateway_client import GatewayClient
from starkware.starknet.services.api.gateway.transaction import Deploy, InvokeFunction
from starkware.starknet.compiler.compile import compile_starknet_files, get_selector_from_name
from starkware.cairo.lang.vm.crypto import pedersen_hash
from utils.types import Data
from utils.block_header import build_block_header
from utils.Signer import Signer
from utils.create_account import create_account


eth_provider_url = "http://94.237.54.114:8550/"
provider = Web3.HTTPProvider(eth_provider_url)
web3 = Web3(provider)
web3.middleware_onion.inject(geth_poa_middleware, layer=0)
load_dotenv()

def get_gateway_client(gateway_url: str) -> GatewayClient:
    # Limit the number of retries.
    retry_config = RetryConfig(n_retries=1)
    return GatewayClient(url=gateway_url, retry_config=retry_config)


gateway_url = "https://alpha4.starknet.io/"

starknet_core_addr = '0xde29d060D45901Fb19ED6C6e959EB22d8626708e'
gateway_client = get_gateway_client(gateway_url)


async def register_computation_twap(client, twap_contract_address, start_block, end_block,parameter,  callback_address):
    twap_register_computation_tx = InvokeFunction(
            contract_address=int(twap_contract_address, 16),
            entry_point_selector=get_selector_from_name('register_computation'),
            calldata=[start_block, end_block, parameter, int(callback_address, 16)],
            signature=[],
            max_fee=0,
            version=0)
    tx_receipt = await client.add_transaction(twap_register_computation_tx)
    
    print(tx_receipt)

async def compute_twap(client, twap_contract_address, _calldata):
    twap_compute_tx = InvokeFunction(
            contract_address=int(twap_contract_address, 16),
            entry_point_selector=get_selector_from_name('compute'),
            calldata=_calldata,
            signature=[],
            max_fee=0,
            version=0)
    tx_receipt = await client.add_transaction(twap_compute_tx)

    print(tx_receipt)


## Remember end_block < start_block, so we are working in backward direction from beginning start block
start_block_number = 6876069 # The block you send to L1 Messaging Contract, should be --> start_block + 1
end_block_number = 6876065
parameter_num = 15 # basefee --> 15, difficulty --> 7, gas_used --> 10


twap_contract_address = os.getenv("STARKNET_TWAP_ADDR")
twap_callback_address = os.getenv("STARKNET_TWAP_CALLBACK_ADDR")

# Register Computation Starts Here
# loop = asyncio.get_event_loop()
# loop.run_until_complete(register_computation_twap(gateway_client, twap_contract_address, start_block_number, end_block_number,parameter_num,  twap_callback_address))
# loop.close()
# Register Computation Ends Here

# Calculate Pedersen Hash
tmp_1 = pedersen_hash(start_block_number, end_block_number)
tmp_2 = pedersen_hash(tmp_1, int(twap_callback_address,16))
computation_id = pedersen_hash(tmp_2, parameter_num)
print("Computation ID: ", computation_id)
# Pedersen Hash Ends Here

# Preparing calldata starts here
headers_lengths_bytes = []
headers_lengths_words = []
concat_headers = []
for block_num in range(start_block_number, end_block_number - 1, -1):
    block = dict(web3.eth.get_block(block_num))
    block_header = build_block_header(block)
    print(block_header)
    block_rlp = Data.from_bytes(block_header.raw_rlp()).to_ints()
    print("Block Number: ", block_num , " ,blockhash: ", block_header.hash().hex())
    headers_lengths_bytes.append(block_rlp.length)
    headers_lengths_words.append(len(block_rlp.values))
    concat_headers.extend(block_rlp.values)

calldata = [
    computation_id,
    len(headers_lengths_bytes),
    *headers_lengths_bytes,
    len(headers_lengths_words),
    *headers_lengths_words,
    len(concat_headers),
    *concat_headers
]
print(calldata)
# Preparing calldata ends here
loop = asyncio.new_event_loop()
loop.run_until_complete(compute_twap(gateway_client, twap_contract_address, calldata))
loop.close()