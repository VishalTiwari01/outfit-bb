from gradio_client import Client, handle_file
import sys
import shutil

client = Client("Kwai-Kolors/Kolors-Virtual-Try-On")
# client.endpoints[2].api_name = '/predict'
# client.endpoints[2].is_valid = True

print(client.view_api(return_format="dict"))
