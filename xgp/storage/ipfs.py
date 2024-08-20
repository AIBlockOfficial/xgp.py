from typing import List, Optional
import logging
from io import BytesIO
from pathlib import Path

from file_handler import to_uint8_array, uint8_array_to_stream
from wallet import KeyWallet
from utils import construct_address
from pinata_sdk import PinataSDK  # Assuming you have a PinataSDK Python wrapper or equivalent

logger = logging.getLogger(__name__)

class IPFSStorage:
    def __init__(self, config: dict, key_wallet: KeyWallet):
        self.key_wallet = key_wallet

        if not config.get('pinataSDKKeys') or not config['pinataSDKKeys'].get('jwt') or not config['pinataSDKKeys'].get('gateway'):
            raise ValueError('Pinata API keys are required for IPFS storage')

        self.pinata_sdk_client = PinataSDK(
            pinata_jwt=config['pinataSDKKeys']['jwt'],
            pinata_gateway=config['pinataSDKKeys']['gateway']
        )

    async def push(self, data: bytes, file_id: str, byte_map: List[int], public_key: bytes):
        logger.info("Pushing data to IPFS")
        if not await self.is_connected_to_pinata():
            raise ConnectionError('Not connected to Pinata')

        array_data = to_uint8_array(data)
        transformed_data = bytes([byte_map[byte] for byte in array_data])

        # Convert the bytes to a stream (in place of Blob and File in JS)
        file_stream = BytesIO(transformed_data)
        file_name = construct_address(public_key, None) or "default_file"

        try:
            resp = await self.pinata_sdk_client.upload_file(file_stream, file_name, "text/plain")
            logger.info("IPFS response: %s", resp)

            if resp:
                await self.mint_pinata_map(resp, byte_map, public_key)
        except Exception as e:
            logger.error("Error pushing data to IPFS: %s", e)

    async def pull(self, ipfs_hash: str, public_key: bytes):
        logger.info("Pulling data from IPFS")
        if not await self.is_connected_to_pinata():
            raise ConnectionError('Not connected to Pinata')

        try:
            resp = await self.pinata_sdk_client.get_file(ipfs_hash)
            logger.info("Response: %s", resp)

            byte_map = await self.get_byte_map_from_public_key(ipfs_hash, public_key)
            blob_data = await resp.read()
            array_data = bytearray(blob_data)
            data = bytes([byte_map[byte] for byte in array_data])

            return {
                'data': data,
                'byte_map': byte_map
            }
        except Exception as e:
            logger.error("Error pulling data from IPFS: %s", e)

    async def get_byte_map_from_public_key(self, ipfs_hash: str, public_key: bytes) -> List[int]:
        address = construct_address(public_key, None) or ''
        balance_resp = await self.key_wallet.fetch_balance([address])
        balance = balance_resp.get('content', {}).get('fetchBalanceResponse')

        if balance:
            entry = next((entry for entry in balance.get(address, []) if entry['ipfsHash'] == ipfs_hash), None)
            if entry:
                return entry.get('byteMap', [])

        return []

    async def mint_pinata_map(self, pinata_resp: dict, byte_map: List[int], public_key: bytes):
        pinata_map = {
            'ipfsHash': pinata_resp['IpfsHash'],
            'timestamp': pinata_resp['Timestamp'],
            'schema': 'XGP_V1_IPFS_PINATA',  # Replace with actual schema enum/constant if necessary
            'byteMap': byte_map,
            'address': construct_address(public_key, None) or "default"
        }

        await self.key_wallet.mint_to_chain(pinata_map, public_key, 1)

    async def is_connected_to_pinata(self) -> bool:
        try:
            resp = await self.pinata_sdk_client.test_authentication()
            return resp == "Congratulations! You are communicating with the Pinata API!"
        except Exception:
            return False
