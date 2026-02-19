import json
import zlib
import base64
import os

def compress_encode(data: bytes) -> str:
    """Equivalent to Java's compressEncode() using zlib (Deflater) and Base64."""
    # Compress the bytes (zlib.compress matches Java's default Deflater format)
    compressed_data = zlib.compress(data)
    # Encode to Base64 and return as a UTF-8 string
    return base64.b64encode(compressed_data).decode('utf-8')

def encrypt(config_data, output_dir: str = "."):
    """Equivalent to Java's encrypt(Context ctx)."""
    try:
        # Remove AppsLshModels if present (no longer exported/required)
        config_data.pop("AppsLshModels", None)

        # --- File 2: Process OnDeviceModels (anagog_js_model.bin) ---
        if "OnDeviceModels" in config_data:
            on_device_models = config_data.pop("OnDeviceModels") # Removes it from config_data
            js_models_str = json.dumps(on_device_models)
            encoded_js = compress_encode(js_models_str.encode('utf-8'))
            
            js_file_path = os.path.join(output_dir, "anagog_js_model.bin")
            with open(js_file_path, 'wb') as f:
                f.write(encoded_js.encode('utf-8'))
                
        # --- File 3: Process the remaining configuration (anagog_config.bin) ---
        config_str = json.dumps(config_data)
        encoded_config = compress_encode(config_str.encode('utf-8'))
        
        config_file_path = os.path.join(output_dir, "anagog_config.bin")
        with open(config_file_path, 'wb') as f:
            f.write(encoded_config.encode('utf-8'))
            
        print("Successfully encrypted and exported all binary files.")
        
    except Exception as e:
        print(f"An error occurred: {e}")
        raise e

# Example execution:
# encrypt('DeepMs.json', './output')