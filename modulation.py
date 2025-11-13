from PIL import Image, UnidentifiedImageError
import os
import numpy as np

class ImageProcessing:
    img_width = 2048
    img_height = 2048
    
    def __init__(self, image_path):
        self.image_path = image_path
        try:
            self.image = Image.open(image_path)
        except FileNotFoundError:
            raise
        except UnidentifiedImageError:
            raise
        
        if self.image.mode != 'RGB':
            self.image = self.image.convert('RGB')
        
        self.pixels = self.image.load()
        self.width, self.height = self.image.size
    
    def resize_image(self):
        self.image = self.image.resize((self.img_width, self.img_height))
        self.pixels = self.image.load()
        self.width, self.height = self.image.size
    
    def save_image(self, output_path):
        os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
        self.image.save(output_path)


class MessageEncoder:
    def __init__(self, message):
        self.message = message
        self.binary_message = self.to_binary()
        self.msg_length = len(self.binary_message)
    
    def to_binary(self):
        return [int(bit) for byte in self.message.encode('utf-8') for bit in format(byte, '08b')]


class MessageEmbedder:
    def __init__(self, pixelAccess, binary_message, width, height, key):
        self.pixels = pixelAccess
        self.binary_message = binary_message
        self.width = width
        self.height = height
        self.key = key
        self.embedding_map = []
        self.map_generated = False

    def map_generation(self):
        map_size = self.width * self.height * 3
        np.random.seed(self.key)
        lst = np.random.randint(0, 2, map_size)
        self.embedding_map = np.array(lst).reshape(-1, 3)
        self.map_generated = True
        return int(np.sum(lst))  # total embedding capacity
    
    def embedMessage(self):
        if not self.map_generated:
            raise RuntimeError("Call map_generation() before embedding.")
        
        total_positions = int(np.sum(self.embedding_map))
        if len(self.binary_message) < total_positions:
            self.binary_message = list(self.binary_message) + [0] * (total_positions - len(self.binary_message))
        
        msg_pointer = 0
        
        for i in range(self.height):
            for j in range(self.width):
                pixel = list(self.pixels[j, i])
                pixel_idx = i * self.width + j
                
                for channel in range(3):
                    if self.embedding_map[pixel_idx][channel] == 1:
                        if msg_pointer < len(self.binary_message):
                            pixel[channel] = (pixel[channel] & 0xFE) | self.binary_message[msg_pointer]
                            msg_pointer += 1
                self.pixels[j, i] = tuple(pixel)
        
        return msg_pointer


class SteganographyPipeline:
    def __init__(self, image_path, message, key, output_path='output/embedded_image.png'):
        self.image_path = image_path
        self.message = message
        self.key = key
        self.output_path = output_path

    def encode(self):
        image_processor = ImageProcessing(self.image_path)
        image_processor.resize_image()

        encoder = MessageEncoder(self.message)
        embedder = MessageEmbedder(
            image_processor.pixels,
            encoder.binary_message,
            image_processor.width,
            image_processor.height,
            self.key
        )
        
        capacity = embedder.map_generation()
        bits_embedded = embedder.embedMessage()
        image_processor.save_image(self.output_path)
        
        return {
            'bits_embedded': bits_embedded,
            'message_length': encoder.msg_length,
            'capacity': capacity,
            'output_path': self.output_path
        }


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Embed a message into an image using LSB steganography")
    parser.add_argument("--input", "-i", default="Family.png", help="Input image path")
    parser.add_argument("--output", "-o", default="output/embedded_image.png", help="Output image path")
    parser.add_argument("--message", "-m", default="This is a secret message!", help="Message to embed")
    parser.add_argument("--key", "-k", type=int, default=42, help="Random seed/key for embedding map")
    args = parser.parse_args()

    pipeline = SteganographyPipeline(args.input, args.message, args.key, args.output)
    result = pipeline.encode()

    print(f"✅ Embedding successful!")
    print(f"Bits embedded: {result['bits_embedded']}")
    print(f"Message length: {result['message_length']}")
    print(f"Capacity: {result['capacity']}")
    print(f"Saved to: {result['output_path']}")
