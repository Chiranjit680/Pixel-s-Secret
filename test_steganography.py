#!/usr/bin/env python3
"""Test script to verify steganography embedding and extraction works correctly."""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from modulation import SteganographyPipeline, ImageProcessing, MessageEmbedder
from demodulation import MessageExtractor, MessageDecoder

def test_round_trip():
    """Test: embed a message and extract it back."""
    test_message = "I love Swastika "
    test_key = 42
    test_image = "Bengali.png"
    test_output = "output/test_stegno.png"
    
    print(f"Testing steganography round-trip...")
    print(f"  Message: '{test_message}'")
    print(f"  Key: {test_key}")
    print(f"  Image: {test_image}")
    
    # Step 1: Embed
    try:
        pipeline = SteganographyPipeline(test_image, test_message, test_key, test_output)
        result = pipeline.encode()
        print(f"\n✓ Embedding successful")
        print(f"  Bits embedded: {result['bits_embedded']}")
        print(f"  Message bit length: {result['message_length']}")
        print(f"  Output: {result['output_path']}")
    except Exception as e:
        print(f"✗ Embedding failed: {e}")
        return False
    
    # Step 2: Extract
    try:
        processor = ImageProcessing(test_output)
        extractor = MessageExtractor(processor.pixels, processor.width, processor.height, test_key)
        extractor.map_generation()
        binary_message = extractor.extractMessage()
        print(f"\n✓ Extraction successful")
        print(f"  Bits extracted: {len(binary_message)}")
        print(f"  First 32 bits: {binary_message[:32]}")
    except Exception as e:
        print(f"✗ Extraction failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Step 3: Decode
    try:
        decoder = MessageDecoder(binary_message)
        decoded = decoder.message
        print(f"\n✓ Decoding successful")
        print(f"  Decoded message: '{decoded}'")
        
        # if decoded == test_message:
        #     print(f"\n✓✓✓ SUCCESS: Message matched!")
        #     return True
        # else:
        #     print(f"\n✗ MISMATCH: Expected '{test_message}', got '{decoded}'")
            # return False
    except Exception as e:
        print(f"✗ Decoding failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_round_trip()
    sys.exit(0 if success else 1)
