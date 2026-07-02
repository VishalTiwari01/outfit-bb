from gradio_client import Client, handle_file

try:
    client = Client("yisol/IDM-VTON")
    result = client.predict(
        dict={"background": handle_file("test.jpg"), "layers": [], "composite": None},
        garm_img=handle_file("test.jpg"),
        garment_des="A piece of clothing",
        is_checked=True,
        is_checked_crop=False,
        denoise_steps=30,
        seed=42,
        api_name="/tryon"
    )
    print("Success:", result)
except Exception as e:
    print("Error:", e)
