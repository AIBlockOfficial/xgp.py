from typing import Union, List

class KeyWallet:
    # Placeholder class for KeyWallet, should implement methods used in Gateway
    async def init(self, seed_phrase: str):
        pass

    def provide_keypair(self):
        pass

    async def mintByteMapToChain(self, byte_map: List[int], public_key: bytes, amount: int):
        pass

    async def mintShardToChain(self, shard: bytes, prev_hash: Union[str, None], index: int, public_key: bytes, amount: int):
        pass