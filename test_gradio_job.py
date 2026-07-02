from gradio_client import Client, handle_file
import json

client = Client("Kwai-Kolors/Kolors-Virtual-Try-On")
client.endpoints[2].api_name = '/predict'
client.endpoints[2].is_valid = True

try:
    job = client.submit(
        handle_file("/Users/apple/Documents/outfit/backend/test.jpg"),
        handle_file("/Users/apple/Documents/outfit/backend/test.jpg"),
        42,
        True,
        fn_index=2
    )
    result = job.result()
    print("SUCCESS")
    print(result)
except Exception as e:
    print("ERROR")
    print(e)
