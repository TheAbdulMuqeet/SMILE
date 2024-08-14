import requests
from random import randint
import threading
from speech import stt, tts

def getsid(version):
    """Generates a unique id for each session using numpy.random.randit() \nCompares the new id with all of the past ids (stores in a text file)"""
    id = 0
    past_sessions = []

    with open("./" + version + "/docs/past_sessions.txt", "r") as past:
        past_sessions = past.read().split('\n')
    while str(id) in past_sessions:
        for i in range(5):
            id += randint(1000, 9999)

    with open("./" + version + "/docs/past_sessions.txt", "a") as past:
        past.write(f"{str(id)}\n")
    return id

sid = getsid("app")
counter = 0

# login credentials
# You need to signup on the front end first in order
# to create an account. Then use those credentials
print("--- WARNING: Only proceed if you have already registered at http://127.0.0.1:5000/register")
uname = input("Enter your username: ")
passw = input("Enter your password: ")

print("--- WARNING: Only proceed if your ESP32 code is running")
esp_ip = input("Enter ESP32 IP: ")

login_data = {
    'username': uname,
    'password': passw,
    'sid': sid,
    'counter': counter
}

session = requests.Session()
login_url = "http://127.0.0.1:5000/login"
login_response = session.post(login_url, data=login_data)


def calculate_duration(text):
    return 0.5 * len(text.split(" "))

no_response_count = 0

def esp(emotion, bot_response):
    """Sends which emotion to show to esp32 server"""
    esp_response = requests.post(f"http://{esp_ip}:80", json={"emotion": emotion, "duration": calculate_duration(bot_response)})

def process_text():
    """Performs following\n1. Sends user message to Sam's server\n2. Sends emotion to ESP32 server\n3. Handles user input and Sam's output"""
    global no_response_count
    halt = False
    while True:
        try:
            text = stt()
            if text is None:
                bot_response = "I cannot hear you, can you please repeat that?"
                emotion = None
                no_response_count += 1
            elif text.lower() == "bye":
                halt = True
            else:
                response_json = session.post("http://127.0.0.1:5000/user_message/", data={'message': text}).json()
                emotion = response_json['emotion']
                bot_response = response_json['response']
                no_response_count = 0
            
            if no_response_count >= 3:
                bot_response = "I was not able to get a response from you, guess you're not there. Anytime, see ye later!"
                emotion = None
                halt = True

            print("Bot:", bot_response, f"({emotion})")
            
            t1 = threading.Thread(target=tts, args=(bot_response,))
            t2 = threading.Thread(target=esp, args=(emotion, bot_response,))
            
            t1.start()
            t2.start()
            
            t1.join()
            t2.join()
            
            if halt:
                exit() 

        except Exception as e:
            print("Error occurred.", e)

if login_response.status_code == 200:
    text_thread = threading.Thread(target=process_text)
    text_thread.start()
    text_thread.join()