#!/usr/bin/env python3
"""FastAPI server for steganography embedding and extraction."""

from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import uuid
import shutil
from typing import Optional
from pathlib import Path

from modulation import SteganographyPipeline, ImageProcessing
from demodulation import MessageExtractor, MessageDecoder

app = FastAPI(
    title="Steganography API",
    description="API for embedding and extracting hidden messages in images",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create directories for temporary files
UPLOAD_DIR = Path("temp_uploads")
OUTPUT_DIR = Path("temp_outputs")
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

class EmbedRequest(BaseModel):
    """Model for embed request parameters"""
    message: str
    key: int

class ExtractRequest(BaseModel):
    """Model for extract request parameters"""
    key: int
    message_length: Optional[int] = None

class EmbedResponse(BaseModel):
    """Model for embed response"""
    success: bool
    bits_embedded: int
    message_length: int
    output_filename: str
    download_url: str

class ExtractResponse(BaseModel):
    """Model for extract response"""
    success: bool
    message: str
    bits_extracted: int

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "name": "Steganography API",
        "version": "1.0.0",
        "endpoints": {
            "POST /embed": "Embed a message in an image",
            "POST /extract": "Extract a message from an image",
            "GET /download/{filename}": "Download a steganography image",
            "GET /health": "Health check"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

@app.post("/embed", response_model=EmbedResponse)
async def embed_message(
    image: UploadFile = File(..., description="Image file (PNG, JPG, etc.)"),
    message: str = Form(..., description="Message to embed"),
    key: int = Form(..., description="Encryption key (integer)")
):
    """
    Embed a hidden message in an image.
    
    - **image**: The cover image file
    - **message**: The secret message to hide
    - **key**: An integer key for encryption/decryption
    
    Returns a JSON response with embedding details and download URL.
    """
    temp_input = None
    temp_output = None
    
    try:
        # Generate unique filenames
        unique_id = str(uuid.uuid4())
        input_ext = Path(image.filename).suffix
        temp_input = UPLOAD_DIR / f"{unique_id}_input{input_ext}"
        temp_output = OUTPUT_DIR / f"{unique_id}_output.png"
        
        # Save uploaded file
        with temp_input.open("wb") as buffer:
            shutil.copyfileobj(image.file, buffer)
        
        # Perform steganography
        pipeline = SteganographyPipeline(
            str(temp_input),
            message,
            key,
            str(temp_output)
        )
        result = pipeline.encode()
        
        # Clean up input file
        temp_input.unlink()
        
        return EmbedResponse(
            success=True,
            bits_embedded=result['bits_embedded'],
            message_length=result['message_length'],
            output_filename=temp_output.name,
            download_url=f"/download/{temp_output.name}"
        )
        
    except Exception as e:
        # Clean up files on error
        if temp_input and temp_input.exists():
            temp_input.unlink()
        if temp_output and temp_output.exists():
            temp_output.unlink()
        
        raise HTTPException(status_code=500, detail=f"Embedding failed: {str(e)}")

@app.post("/extract", response_model=ExtractResponse)
async def extract_message(
    image: UploadFile = File(..., description="Steganography image file"),
    key: int = Form(..., description="Decryption key (integer)"),
    message_length: Optional[int] = Form(None, description="Message length in bits (optional)")
):
    """
    Extract a hidden message from a steganography image.
    
    - **image**: The steganography image file
    - **key**: The integer key used during embedding
    - **message_length**: (Optional) The length of the embedded message in bits
    
    Returns the extracted message.
    """
    temp_input = None
    
    try:
        # Generate unique filename
        unique_id = str(uuid.uuid4())
        input_ext = Path(image.filename).suffix
        temp_input = UPLOAD_DIR / f"{unique_id}_extract{input_ext}"
        
        # Save uploaded file
        with temp_input.open("wb") as buffer:
            shutil.copyfileobj(image.file, buffer)
        
        # Load image
        processor = ImageProcessing(str(temp_input))
        
        # Extract message
        extractor = MessageExtractor(
            processor.pixels,
            processor.width,
            processor.height,
            key
        )
        extractor.map_generation()
        binary_message = extractor.extractMessage()
        
        # Decode message
        decoder = MessageDecoder(binary_message)
        decoded_message = decoder.message
        
        # Clean up
        temp_input.unlink()
        
        return ExtractResponse(
            success=True,
            message=decoded_message,
            bits_extracted=len(binary_message)
        )
        
    except Exception as e:
        # Clean up files on error
        if temp_input and temp_input.exists():
            temp_input.unlink()
        
        raise HTTPException(status_code=500, detail=f"Extraction failed: {str(e)}")

@app.get("/download/{filename}")
async def download_file(filename: str):
    """
    Download a steganography image.
    
    - **filename**: The name of the file to download
    """
    file_path = OUTPUT_DIR / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(
        path=file_path,
        media_type="image/png",
        filename=filename
    )

@app.delete("/cleanup/{filename}")
async def cleanup_file(filename: str):
    """
    Delete a generated steganography image.
    
    - **filename**: The name of the file to delete
    """
    file_path = OUTPUT_DIR / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    try:
        file_path.unlink()
        return {"success": True, "message": f"File {filename} deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete file: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)