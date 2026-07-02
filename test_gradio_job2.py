from gradio_client import Client, handle_file
import json
import httpx

client = Client("Kwai-Kolors/Kolors-Virtual-Try-On")
client.endpoints[2].api_name = '/predict'
client.endpoints[2].is_valid = True

job = client.submit(
    handle_file("/Users/apple/Documents/outfit/backend/test.jpg"),
    handle_file("/Users/apple/Documents/outfit/backend/test.jpg"),
    42,
    True,
    fn_index=2
)
# Don't call result(), just wait for it to be done
while not job.done():
    pass

try:
    print(job.outputs())
except Exception as e:
    print("outputs ERROR", e)

