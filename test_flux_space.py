from gradio_client import Client
import json

try:
    client = Client("M3st3rJ4k3l/FLUX.2-Klein-Multi-LoRA")
    api_info = client.view_api(return_format='dict')
    print(json.dumps(api_info, indent=2))
except Exception as e:
    print(f"Error: {e}")
