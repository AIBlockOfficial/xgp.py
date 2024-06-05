import hashlib
import os
from typing import List, Union
from xgp.key_wallet import KeyWallet

class Gateway:
    def __init__(self):
        self.key_wallet = KeyWallet()

    async def init(self, seed_phrase: str):
        await self.key_wallet.init(seed_phrase)

    def get_keypair(self):
        return self.key_wallet.provide_keypair()

    def create_byte_map_from_public_key(self, public_key: bytes) -> List[int]:
        hash_obj = hashlib.sha256(public_key)
        hash_array = list(hash_obj.digest())

        byte_map = list(range(256))
        for i in range(len(byte_map) - 1, 0, -1):
            j = hash_array[i % len(hash_array)] % (i + 1)
            byte_map[i], byte_map[j] = byte_map[j], byte_map[i]

        return byte_map

    def create_inverse_byte_map(self, byte_map: List[int]) -> List[int]:
        inverse_byte_map = [0] * len(byte_map)
        for index, value in enumerate(byte_map):
            inverse_byte_map[value] = index

        return inverse_byte_map

    async def mint(self, byte_map: List[int], public_key: bytes, amount: int):
        await self.key_wallet.mintByteMapToChain(byte_map, public_key, amount)

    async def push(self, folder_path: str, public_key: Union[bytes, None] = None):
        if not self.is_node():
            raise RuntimeError('This method is only available in Node.js environments')

        used_public_key = public_key or self.get_keypair().get('publicKey')
        byte_map = self.create_byte_map_from_public_key(used_public_key)
        shards_to_push = []
        prev_hash = None

        try:
            for root, _, files in os.walk(folder_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    if os.path.isfile(file_path):
                        shards = self.shard_file(file_path, byte_map)
                        shards_to_push.extend(shards)

            if used_public_key:
                for i, shard in enumerate(shards_to_push):
                    try:
                        resp = await self.key_wallet.mintShardToChain(shard, prev_hash, i, used_public_key, 1)
                        if resp:
                            prev_hash = resp.get('tx_hash')
                    except Exception as err:
                        print("Error minting shard", err)
            else:
                print("No public key found. Unable to push to chain")
                raise RuntimeError('No public key found. Unable to push to chain')
        except Exception as err:
            print(f"Error processing folder {folder_path}:", err)

    def is_node(self) -> bool:
        try:
            return os.environ.get('NODE_ENV') is not None
        except AttributeError:
            return False

    def shard_file(self, file_path: str, byte_map: List[int]) -> List[bytes]:
        # Placeholder method for sharding file, needs implementation
        pass
