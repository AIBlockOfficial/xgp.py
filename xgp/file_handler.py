import os
from io import BytesIO
from typing import List, Optional, Union

def split_into_shards(data: bytes, shard_size: int, byte_map: Optional[List[int]] = None) -> List[bytes]:
    """
    Splits a byte array into shards of a given size. If a byte_map is provided, the data will be transformed
    
    :param data: The data to be split into shards
    :param shard_size: The size of each shard
    :param byte_map: A list of integers that will be used to transform the data
    """
    shards = []
    for i in range(0, len(data), shard_size):
        shard = data[i:i + shard_size]

        if byte_map:
            converted_shard = to_uint8_array(shard)
            transformed_data = transform_data(converted_shard, byte_map)
            shards.append(transformed_data['transformed_message'])
        else:
            shards.append(to_uint8_array(shard))

    return shards

def contract_from_shards(shards: List[bytes], byte_map: List[int]) -> bytes:
    """
    Concatenates a list of shards into a single byte array. If a byte_map is provided, the data will be transformed
    
    :param shards: A list of byte arrays
    :param byte_map: A list of integers that will be used to transform the data
    """
    return b''.join([reverse_transform_data(shard, byte_map) for shard in shards])

def bytes_to_hex(byte_array: bytes) -> str:
    """
    Converts a byte array to a hex string
    
    :param byte_array: The byte array to be converted
    """
    return ''.join([f'{byte:02x}' for byte in byte_array])

def uint8_array_to_stream(uint8_array: bytes):
    """
    Converts a byte array to a BytesIO stream
    
    :param uint8_array: The byte array to be converted
    """
    return BytesIO(uint8_array)

def transform_data(message: bytes, byte_map: List[int]) -> dict:
    """
    Transforms a byte array using a byte map
    
    :param message: The byte array to be transformed
    :param byte_map: A list of integers that will be used to transform the data
    """
    transformed_message = bytes([byte_map[byte] for byte in message])
    return {
        'transformed_message': transformed_message,
        'byte_map': byte_map
    }

def to_uint8_array(input_data: Union[bytes, str]) -> bytes:
    """
    Converts a string or a byte array to a byte array
    
    :param input_data: The data to be converted
    """
    if isinstance(input_data, str):
        return input_data.encode('utf-8')
    elif isinstance(input_data, bytes):
        return input_data
    else:
        raise ValueError('Input must be a bytes or a string')

def reverse_transform_data(message: bytes, inverse_byte_map: List[int]) -> bytes:
    """
    Reverses the transformation of a byte array using an inverse byte map
    
    :param message: The byte array to be transformed
    :param inverse_byte_map: A list of integers that will be used to transform the data
    """
    return bytes([inverse_byte_map[byte] for byte in message])

def shard_file(file_path: str, byte_map: Optional[List[int]] = None) -> List[bytes]:
    """
    Splits a file into shards of 100 bytes
    
    :param file_path: The path to the file to be split
    :param byte_map: A list of integers that will be used to transform the data
    """
    with open(file_path, 'rb') as file:
        data = file.read()
    return split_into_shards(data, 100, byte_map)

def readdir_async(folder_path: str) -> List[str]:
    """
    Reads the contents of a folder asynchronously
    
    :param folder_path: The path to the folder to be read
    """
    try:
        return os.listdir(folder_path)
    except Exception as e:
        raise e

def stat_async(file_path: str) -> os.stat_result:
    """
    Gets the status of a file asynchronously
    
    :param file_path: The path to the file to get the status of
    """
    try:
        return os.stat(file_path)
    except Exception as e:
        raise e
