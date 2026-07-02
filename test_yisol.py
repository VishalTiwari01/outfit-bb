from gradio_client import Client, handle_file

client = Client("yisol/IDM-VTON")
print(client.view_api(return_format='dict'))
