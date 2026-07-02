from gradio_client import Client, handle_file

client = Client("Nymbo/Virtual-Try-On")
result = client.predict(
		dict={"background":handle_file("/Users/apple/Documents/outfit/backend/test.jpg"),"layers":[],"composite":None},
		garm_img=handle_file("/Users/apple/Documents/outfit/backend/test.jpg"),
		garment_des="A test shirt",
		is_checked=True,
		is_checked_crop=False,
		denoise_steps=30,
		seed=42,
		api_name="/tryon"
)
print(result)
