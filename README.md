# How To Run Fossil
Let's understand how to use the fossil API using an example.
Our goal here is to deploy a contract that uses the fossil API to compute the TWAP of some native blockchain parameters.
We can then use this TWAP to do a lot of fun applications.
So let's get started!

## Setting Up The Environment
1. Let's create a directory for our project
```
mkdir playing-with-fossil
cd playing-with-fossil
```
2. Now clone the fossil repo into this directory
```
git clone https://github.com/OilerNetwork/fossil.git
cd fossil
```
3. Now we need to do some quick setup 
So first let's create a venv with python 3.7
```
python3.7 -m venv ~/fossil_venv
source ~/fossil_venv/bin/activate
```
Now we need to install [tox](https://tox.wiki/en/latest/#:~:text=tox%20is%20a%20generic%20virtualenv,your%20test%20tool%20of%20choice), On linux you can run something like - 
```
sudo apt update
sudo apt install tox
```
and then just run tox
```
tox
```
And once you have all of this ready, just run this command to compile all the existing contracts
```
./.tox/py37/bin/nile compile
```

## Computing the TWAP 
Fossil is just a set of smart contracts deployed on starknet. But you can use a combination of all these contracts to do some very powerful things.
Let's say you want to compute the TWAP of the basefee from block X to X-100. How do you do this?

To find the TWAP of any blockchain native parameter we have to use these smart contracts from the fossil infrastructure - 
1. L1MessagesSender.sol - Deployed on Ethereum
2. L1MessagesProxy 
3. L1HeadersStore 
4. TWAP 

#### L1 Messages Sender & L1MessagesProxy 

To get the TWAP of let's say the basefee, difficulty or the gas used, we will need the block headers of all the block headers between the starting and the ending block right?
So how do we get that?
Using Fossil you can achieve this in just one call to the ethereum smart contract - L1MessagesSender.sol
So L1MessagesSender will send a simple tuple consisting of the block number and the blockhash of the parent block to the L1MessagesProxy contract deployed on starknet.


So the process starts when the sendExactParentHashtoL2 function of the L1MessagesSender contract deployed on ethereum is called by some entity for block X + 1.
Now the L1MessagesProxy will receive the magic tuple, which is something like - (parentHash = blockhash(X),blockNum = X+1)
So far so good.

Now once we have these smart contracts deployed and we have the magic tuple for the block X on starknet, how do we recreate the block header for the block X, X-1,  X-2, or X- 100?

This is where the L1HeadersStore contract comes into the action.

#### L1HeadersStore.cairo
As soon as the L1MessagesProxy contract receives the tuple from ethereum, it calls the receive_from_l1 function of the L1HeadersStore contract.
Now let's talk about the L1HeadersStore, this is a very important smart contract in the fossil infrastructure.
It stores all of the parameters for the processed block headers on starknet, as mappings.
![](https://i.imgur.com/qgUyIKv.png)
A real advantage of this is that as the number of people using fossil increases, the cost of using fossil goes down.
This is because there is an increasing likelihood that a lot of the parameters that you need for your usecase might have already been stored in the L1HeadersStore by some older computations by other users.
This is one factor that makes the fossil API so powerful. You can read more about the API here ( @kacper please provide link)

Anyways, back to the TWAP.
Now once the L1HeadersStore receives the magic tuple - (parentHash = blockhash(X),blockNum = X+1), it sets the parent hash of block X+1 in state.

Now that we have the blockhash of block X (which is ofcourse the parenthash of block X+1) stored in L1HeadersStore this is what you can do -
* You can submit the RLP header of any block X to this contract using the process_block function, along with a number called the options_set.
 options_set indicates which element of the block header should be saved in state, it is a felt in range 0 to 2**15 - 1

> options_set: uncles_hash will be saved if **bit 1** of the arg is positive
 options_set: beneficiary will be saved if **bit 2** of the arg is positive
 options_set: state_root will be saved if **bit 3** of the arg is positive
 options_set: transactions_root will be saved if **bit 4** of the arg is positive
 options_set: receipts_root will be saved if **bit 5** of the arg is positive
 options_set: difficulty will be saved if **bit 7** of the arg is positive
 options_set: gas_used will be saved if **bit 10** of the arg is positive
 options_set: timestamp will be saved if **bit 11** of the arg is positive
 options_set: base_fee will be saved if **bit 15** of the arg is positive
> 
* The contract will validate that you have submitted the correct RLP by hashing it and comparing it to the blockhash that was sent to it from L1.
* If both the hashes match, then depending upon the options_set submitted, it will store the respective header parameters into state. If the RLP is invalid then the transaction fails.
* This contract also has a function called process_till_block, where instead of passing the RLP for just one block, you can pass it for multiple blocks and process multiple blocks at a time.

Now suppose only the L1HeadersStore contract existed, then you would have had to process all of the blocks between the start and end range of the TWAP.
Then you would have had to query L1HeadersStore for each of these blocks to calculate the final TWAP for the parameter you need.
#### TWAP.cairo
To save you the pain of doing these extra steps, we developed TWAP.cairo
Using TWAP.cairo, to find the TWAP you just have to follow these basic steps - 
1. Get the blockhash of your starting block (i.e latest block in twap computation) to starknet using the L1MessagesSender.sol
2. Create and Deploy a TWAPReceiver contract, that will receive the TWAP of your parameter once the computation is complete.
3. Register the computation depending upon your requirements by providing -
    a) Start Block Number
    b) End Block Number
    c) Parameter to Compute - difficulty, basefee, gasUsed
    d) Address of the contract that will receive the TWAP
4. Calculate the computation ID using of your request using the 4 parameters registered above. To calculate computationID you can do something like this -
```
const tmp1 = hash.pedersen([fromBlock, toBlock]);
const tmp2 = hash.pedersen([tmp1, callbackAddress]);
const computationID =  hash.pedersen([tmp2, twapParamToInt(parameter)]);
--------------------------------------------
Note that the key for parameter to Int is 
basefee --> 15
difficulty --> 7 
gas_used --> 10
--------------------------------------------
```
5. Prepare the calldata for this transaction by getting the RLPs of all the blocks that will be included in this TWAP computation. We will come back to this soon, and discuss how exactly this construction is done.
6. Once you have all of this ready, you just need to call the ``compute`` function of your TWAP smart contract, and voila you will receive your freshly computed TWAP in your TWAPReceiver contract!

Now that you have a good understanding of how the fossil infrastructure works, you can use it to do a lot of amazing things with it.
We'll publish a code walkthrough of the above mentioned steps very soon in an example project very soon, so stay tuned.
Till that time, you will find a lot of helpful code in the [tests](https://github.com/OilerNetwork/fossil/blob/master/tests/starknet_twap.py) directory of the fossil repo!
If you are building something cool using fossil, reach out to us here - [fossil@oiler.network](fossil@oiler.network)



