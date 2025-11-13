from PIL import Image, UnidentifiedImageError
import os
import numpy as np
from modulation import ImageProcessing


class MessageDecoder:
    def __init__(self, binary_message):
        self.binary_message = binary_message
        self.message = self.from_binary()

    def from_binary(self):
        bytes_list = []
        for i in range(0, len(self.binary_message), 8):
            byte_bits = self.binary_message[i:i+8]
            if len(byte_bits) == 8:
                byte_value = int(''.join(map(str, byte_bits)), 2)
                bytes_list.append(byte_value)
        try:
            return bytes(bytes_list).decode('utf-8', errors='ignore')
        except Exception as e:
            raise ValueError(f"Error decoding UTF-8 message: {e}")


class MessageExtractor:
    def __init__(self, pixelAccess, width, height, key, message_length=None):
        self.pixels = pixelAccess
        self.width = width
        self.height = height
        self.key = key
        self.message_length = message_length
        self.embedding_map = []
        self.binary_message = []

    def map_generation(self):
        map_size = self.width * self.height * 3
        np.random.seed(self.key)
        lst = np.random.randint(0, 2, map_size)
        self.embedding_map = np.array(lst).reshape(-1, 3)
        if self.message_length is None:
            self.message_length = int(np.sum(lst))
        print(f"[info] Using message length: {self.message_length} bits")

    def extractMessage(self):
        msg_pointer = 0
        for i in range(self.height):
            for j in range(self.width):
                pixel = self.pixels[j, i]
                pixel_idx = i * self.width + j

                for channel in range(3):
                    if self.embedding_map[pixel_idx][channel] == 1:
                        if msg_pointer < self.message_length:
                            bit = pixel[channel] & 0x01
                            self.binary_message.append(bit)
                            msg_pointer += 1

                        if msg_pointer >= self.message_length:
                            return self.binary_message
        return self.binary_message


class SteganographyDecodePipeline:
    def __init__(self, image_path, key, message_length=None):
        self.image_path = image_path
        self.key = key
        self.message_length = message_length

    def decode(self):
        image_processor = ImageProcessing(self.image_path)
        extractor = MessageExtractor(
            image_processor.pixels,
            image_processor.width,
            image_processor.height,
            self.key,
            self.message_length
        )
        extractor.map_generation()
        binary_message = extractor.extractMessage()

        decoder = MessageDecoder(binary_message)
        return {
            'message': decoder.message,
            'bits_extracted': len(binary_message)
        }


if __name__ == "__main__":
    pipeline = SteganographyDecodePipeline(
        image_path='output/embedded_image.png',
        key=42
    )
    result = pipeline.decode()
    print(f"✅ Extraction complete")
    print(f"Bits extracted: {result['bits_extracted']}")
    print(f"Decoded message:\n{result['message']}")
