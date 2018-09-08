import hashlib
import json
from urllib.parse import urlparse
from time import time
import requests


class Blockchain():
    def __init__(self):
        self.chain = []
        self.current_transaction = []
        self.new_block(previous_hash=1, proof=100)
        self.nodes = set()

    def register_node(self, address):
        """
        add a new node to the list of nodes
        :param address: <str>
        :return: None
        """
        parse_url = urlparse(address)
        self.nodes.add(parse_url.netloc)

    def new_block(self, proof, previous_hash=None):
        """
        :param proof: <int>
        :param previous_hash: (Optional)<str>
        :return: <dict> new Block
        """
        block = {
            'index': len(self.chain),
            'timestamp': time(),
            'transaction': self.current_transaction,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1]),
        }
        # reset the current list of the transaction
        self.current_transaction = []
        self.chain.append(block)
        return block

    def new_transaction(self, sender, recipient, amount):
        """
        生成交易信息，信息将加入下一个待挖掘区块中
        :param sender: <str>
        :param recipient: <str>
        :param amount: <int>
        :return: <int> the index of the Block that will hold this transaction
        """
        self.current_transaction.append({
            'sender': sender,
            'recipient': recipient,
            'amount': amount,
        })
        return self.last_block['index']+1

    def proof_of_work(self, last_proof):
        """
        简单的工作量证明：
        -查找一个P，使得hash(PP')以四个零开头
        -P'是上一块的证明，P’是这一块的证明
        :param last_proof: <int>
        :return:  <int>
        """
        proof = 0
        while self.valid_proof(last_proof, proof) is False:
            proof += 1
        return proof

    def valid_chain(self,chain):
        """
        determine if a given blockchain is valid
        :param chain: <list> a blockchain
        :return: <bool> True if valid,
        """
        last_block = chain[0]
        current_index = 1
        while current_index < len(chain):
            block = chain[current_index]
            print(f'{last_block}')
            print(f'{block}')
            print("\n..........\n")
            if block['previous_hash'] != self.hash(last_block):
                return False
            if not self.valid_proof(last_block['proof'], block['proof']):
                return False
            last_block = block
            current_index += 1
        return True

    def resolve_conflicts(self):
        """
        共识算法解决冲突，使用网络中最长的链
        :return: <bool>
        """
        neighbours = self.nodes
        new_chain = None
        max_length = len(self.chain)
        for node in neighbours:
            response = requests.get(f'http://{node}/chain')
            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']
                if length > max_length and self.valid_chain(chain):
                    max_length = length
                    new_chain = chain
        if new_chain:
            self.chain = new_chain
            return True
        return False

    @staticmethod
    def hash(block):
        """
        生成块的SHA-256 hash值
        :param block: <dict> Block
        :return:  <str>
        """
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    @property
    def last_block(self):
        return self.chain[-1]

    @staticmethod
    def valid_proof(last_proof, proof):
        guess = f'{last_proof}{proof}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:4] == '0000'
