
from dotenv import load_dotenv

from web3 import Web3
from web3.middleware import geth_poa_middleware

eth_provider_url = "http://94.237.54.114:8550/"
provider = Web3.HTTPProvider(eth_provider_url)
web3 = Web3(provider)
web3.middleware_onion.inject(geth_poa_middleware, layer=0)

print(web3.eth.get_block(6867387))