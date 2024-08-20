import boto3
from typing import List, Optional
import logging
from io import BytesIO
from botocore.exceptions import NoCredentialsError, ClientError

from file_handler import to_uint8_array, uint8_array_to_stream
from wallet import KeyWallet
from utils import construct_address

logger = logging.getLogger(__name__)

class S3Storage:
    def __init__(self, config: dict, key_wallet: KeyWallet):
        self.key_wallet = key_wallet

        if not config.get('aws_access_key_id') or not config.get('aws_secret_access_key') or not config.get('bucket_name'):
            raise ValueError('AWS credentials and bucket name are required for S3 storage')

        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=config['aws_access_key_id'],
            aws_secret_access_key=config['aws_secret_access_key'],
            region_name=config.get('region', 'us-west-2')  # Default to us-west-2 if region not specified
        )
        self.bucket_name = config['bucket_name']

    async def push(self, data: bytes, file_id: str, byte_map: List[int], public_key: bytes):
        logger.info("Pushing data to S3")
        
        array_data = to_uint8_array(data)
        transformed_data = bytes([byte_map[byte] for byte in array_data])

        # Convert data to BytesIO stream for upload
        file_stream = BytesIO(transformed_data)
        file_name = construct_address(public_key, None) or "default_file"

        try:
            self.s3_client.upload_fileobj(file_stream, self.bucket_name, file_name)
            logger.info("Data successfully uploaded to S3 as %s", file_name)

            await self.mint_s3_map(file_name, byte_map, public_key)
        except (NoCredentialsError, ClientError) as e:
            logger.error("Error pushing data to S3: %s", e)

    async def pull(self, file_name: str, public_key: bytes):
        logger.info("Pulling data from S3")
        
        try:
            file_stream = BytesIO()
            self.s3_client.download_fileobj(self.bucket_name, file_name, file_stream)
            file_stream.seek(0)  # Reset stream position after downloading

            byte_map = await self.get_byte_map_from_public_key(file_name, public_key)
            array_data = bytearray(file_stream.read())
            data = bytes([byte_map[byte] for byte in array_data])

            return {
                'data': data,
                'byte_map': byte_map
            }
        except (NoCredentialsError, ClientError) as e:
            logger.error("Error pulling data from S3: %s", e)

    async def get_byte_map_from_public_key(self, file_name: str, public_key: bytes) -> List[int]:
        address = construct_address(public_key, None) or ''
        balance_resp = await self.key_wallet.fetch_balance([address])
        balance = balance_resp.get('content', {}).get('fetchBalanceResponse')

        if balance:
            entry = next((entry for entry in balance.get(address, []) if entry['fileName'] == file_name), None)
            if entry:
                return entry.get('byteMap', [])

        return []

    async def mint_s3_map(self, file_name: str, byte_map: List[int], public_key: bytes):
        s3_map = {
            'fileName': file_name,
            'schema': 'XGP_V1_S3_STORAGE',  # Replace with actual schema enum/constant if necessary
            'byteMap': byte_map,
            'address': construct_address(public_key, None) or "default"
        }

        await self.key_wallet.mint_to_chain(s3_map, public_key, 1)

    def is_connected_to_s3(self) -> bool:
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            return True
        except (NoCredentialsError, ClientError):
            return False
