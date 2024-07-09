import os

port = input("Enter communication port: ")

files = [
    ["ST7735.py", "ST7735.py"], 
    ["emotions.py", "boot.py"],
]

for file_name, upload_name in files:
    command = f"ampy --port {port.upper()} put {file_name} {upload_name}"
    result = os.system(command)
    if result == 0:
        print(f"File {file_name} sent as {upload_name}.")
    else:
        print(f"Failed to send file {file_name} as {upload_name}. Please check your connection and try again.")
