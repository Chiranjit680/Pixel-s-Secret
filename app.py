#!/usr/bin/env python3
"""Streamlit frontend for the Steganography API."""

import streamlit as st
import requests
from PIL import Image
import io
import os

# Configuration
API_URL = os.getenv("API_URL", "http://localhost:8000")

# Page configuration
st.set_page_config(
    page_title="Steganography Tool",
    page_icon="🔐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .stButton>button {
        width: 100%;
    }
    .success-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
        margin: 1rem 0;
    }
    .error-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
        margin: 1rem 0;
    }
    .info-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        color: #0c5460;
        margin: 1rem 0;
    }
    </style>
""", unsafe_allow_html=True)

# Title and description
st.title("🔐 Steganography Tool")
st.markdown("""
Hide secret messages inside images using advanced steganography techniques.
Your messages are encrypted and embedded in the least significant bits of the image pixels.
""")

# Sidebar
with st.sidebar:
    st.header("⚙️ Settings")
    api_status = st.empty()
    
    # Check API health
    try:
        response = requests.get(f"{API_URL}/health", timeout=2)
        if response.status_code == 200:
            api_status.success("✓ API Connected")
        else:
            api_status.error("✗ API Error")
    except:
        api_status.error("✗ API Unreachable")
    
    st.markdown("---")
    st.markdown("### 📖 How it works")
    st.markdown("""
    **Embedding:**
    1. Upload an image
    2. Enter your secret message
    3. Set an encryption key
    4. Download the steganography image
    
    **Extracting:**
    1. Upload the steganography image
    2. Enter the same encryption key
    3. Optionally specify message length
    4. Retrieve the hidden message
    """)
    
    st.markdown("---")
    st.markdown("### 🔒 Security")
    st.info("The encryption key is required to extract the message. Keep it safe!")

# Main content - Tabs
tab1, tab2, tab3 = st.tabs(["📝 Embed Message", "🔍 Extract Message", "ℹ️ About"])

# Tab 1: Embed Message
with tab1:
    st.header("Embed a Secret Message")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("1. Upload Image")
        uploaded_file = st.file_uploader(
            "Choose a cover image",
            type=["png", "jpg", "jpeg", "bmp"],
            help="Upload the image where you want to hide your message"
        )
        
        if uploaded_file:
            image = Image.open(uploaded_file)
            st.image(image, caption="Original Image", use_container_width=True)
            
            # Show image info
            st.info(f"📐 Size: {image.size[0]}x{image.size[1]} pixels")
    
    with col2:
        st.subheader("2. Enter Message")
        secret_message = st.text_area(
            "Secret message",
            height=150,
            placeholder="Type your secret message here...",
            help="The message you want to hide in the image"
        )
        
        if secret_message:
            st.info(f"✏️ Message length: {len(secret_message)} characters ({len(secret_message) * 8} bits)")
        
        st.subheader("3. Set Encryption Key")
        embed_key = st.number_input(
            "Encryption key",
            min_value=1,
            max_value=999999,
            value=42,
            help="Remember this key - you'll need it to extract the message!"
        )
    
    st.markdown("---")
    
    # Embed button
    if st.button("🔐 Embed Message", type="primary", disabled=not (uploaded_file and secret_message)):
        with st.spinner("Embedding message..."):
            try:
                # Prepare the request
                files = {"image": uploaded_file.getvalue()}
                data = {
                    "message": secret_message,
                    "key": embed_key
                }
                
                # Make API request
                response = requests.post(f"{API_URL}/embed", files=files, data=data)
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # Show success message
                    st.markdown(f"""
                    <div class="success-box">
                        <h4>✅ Message Successfully Embedded!</h4>
                        <ul>
                            <li><strong>Bits embedded:</strong> {result['bits_embedded']}</li>
                            <li><strong>Message length:</strong> {result['message_length']} bits</li>
                            <li><strong>Encryption key:</strong> {embed_key} (save this!)</li>
                        </ul>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Download the steganography image
                    download_url = f"{API_URL}{result['download_url']}"
                    stego_response = requests.get(download_url)
                    
                    if stego_response.status_code == 200:
                        stego_image = Image.open(io.BytesIO(stego_response.content))
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.image(image, caption="Original Image", use_container_width=True)
                        with col2:
                            st.image(stego_image, caption="Steganography Image", use_container_width=True)
                        
                        # Download button
                        st.download_button(
                            label="⬇️ Download Steganography Image",
                            data=stego_response.content,
                            file_name=result['output_filename'],
                            mime="image/png"
                        )
                        
                        st.success("The images look identical, but one contains your hidden message! 🎭")
                else:
                    st.markdown(f"""
                    <div class="error-box">
                        <h4>❌ Embedding Failed</h4>
                        <p>{response.json().get('detail', 'Unknown error')}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
            except Exception as e:
                st.markdown(f"""
                <div class="error-box">
                    <h4>❌ Error</h4>
                    <p>{str(e)}</p>
                </div>
                """, unsafe_allow_html=True)

# Tab 2: Extract Message
with tab2:
    st.header("Extract a Hidden Message")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("1. Upload Steganography Image")
        stego_file = st.file_uploader(
            "Choose the steganography image",
            type=["png", "jpg", "jpeg", "bmp"],
            help="Upload the image containing the hidden message",
            key="extract_uploader"
        )
        
        if stego_file:
            stego_image = Image.open(stego_file)
            st.image(stego_image, caption="Steganography Image", use_container_width=True)
    
    with col2:
        st.subheader("2. Enter Decryption Key")
        extract_key = st.number_input(
            "Decryption key",
            min_value=1,
            max_value=999999,
            value=42,
            help="Enter the same key used during embedding",
            key="extract_key"
        )
        
        st.subheader("3. Message Length (Optional)")
        use_custom_length = st.checkbox("Specify message length", help="If you know the exact message length in bits")
        
        message_length = None
        if use_custom_length:
            message_length = st.number_input(
                "Message length (bits)",
                min_value=8,
                max_value=100000,
                value=80,
                help="The exact length of the embedded message in bits"
            )
    
    st.markdown("---")
    
    # Extract button
    if st.button("🔍 Extract Message", type="primary", disabled=not stego_file):
        with st.spinner("Extracting message..."):
            try:
                # Prepare the request
                files = {"image": stego_file.getvalue()}
                data = {"key": extract_key}
                
                if message_length:
                    data["message_length"] = message_length
                
                # Make API request
                response = requests.post(f"{API_URL}/extract", files=files, data=data)
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # Show success message
                    st.markdown(f"""
                    <div class="success-box">
                        <h4>✅ Message Successfully Extracted!</h4>
                        <p><strong>Bits extracted:</strong> {result['bits_extracted']}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Display the extracted message
                    st.subheader("🔓 Extracted Message:")
                    st.text_area(
                        "Secret message",
                        value=result['message'],
                        height=200,
                        disabled=True,
                        label_visibility="collapsed"
                    )
                    
                    # Copy button (using code block for easy copying)
                    st.code(result['message'], language=None)
                    
                else:
                    st.markdown(f"""
                    <div class="error-box">
                        <h4>❌ Extraction Failed</h4>
                        <p>{response.json().get('detail', 'Unknown error')}</p>
                        <p><small>Make sure you're using the correct decryption key!</small></p>
                    </div>
                    """, unsafe_allow_html=True)
                    
            except Exception as e:
                st.markdown(f"""
                <div class="error-box">
                    <h4>❌ Error</h4>
                    <p>{str(e)}</p>
                </div>
                """, unsafe_allow_html=True)

# Tab 3: About
with tab3:
    st.header("About Steganography")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🎨 What is Steganography?")
        st.markdown("""
        Steganography is the practice of hiding secret information within ordinary, 
        non-secret data. Unlike encryption, which scrambles data to make it unreadable, 
        steganography hides the very existence of the data.
        
        This tool uses **LSB (Least Significant Bit)** steganography to hide text 
        messages in images. The message is embedded in the least significant bits of 
        the image pixels, making the changes virtually invisible to the human eye.
        """)
        
        st.subheader("🔒 Security Features")
        st.markdown("""
        - **Encryption Key**: Required for both embedding and extraction
        - **Pseudo-random Distribution**: Message bits are scattered across the image
        - **Minimal Visual Impact**: Changes are imperceptible to humans
        - **Format Preservation**: Output images maintain high quality
        """)
    
    with col2:
        st.subheader("💡 Use Cases")
        st.markdown("""
        - **Secure Communication**: Send hidden messages through public channels
        - **Digital Watermarking**: Embed copyright information in images
        - **Data Protection**: Hide sensitive information in plain sight
        - **Privacy**: Communicate without drawing attention
        """)
        
        st.subheader("⚠️ Important Notes")
        st.warning("""
        - Always keep your encryption key safe!
        - Avoid compressing steganography images (use PNG, not JPEG)
        - The original and steganography images should look identical
        - Message length is limited by image size
        """)
    
    st.markdown("---")
    st.info("🛠️ Built with FastAPI, Streamlit, and Python")

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: gray;'>Made with ❤️ for secure communications</div>",
    unsafe_allow_html=True
)