import speech_recognition as sr
from gtts import gTTS
from pydub import AudioSegment
from pydub.playback import play
import io

def stt(speaker="User"):
    """Listens for user voice and converts into text"""
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening...")
        audio = recognizer.listen(source)
        
        try:
            text = recognizer.recognize_google(audio)
            print(f"{speaker}: " + text)
            return text
        except sr.UnknownValueError:
            print("Google Speech Recognition could not understand audio")
        except sr.RequestError as e:
            print("Could not request results from Google Speech Recognition service; {0}".format(e))


def robotic(sound):
    """Changes pitch and adds a delay to give a robotic voice effect""" 
    octaves = 0.15  # Adjust as needed to change pitch
    new_sample_rate = int(sound.frame_rate * (2.0 ** octaves))
    pitched_sound = sound._spawn(sound.raw_data, overrides={'frame_rate': new_sample_rate})
    pitched_sound = pitched_sound.set_frame_rate(44100)

    delay_ms = 5  # Short delay for robotic effect
    echo = pitched_sound + AudioSegment.silent(duration=delay_ms)
    combined = pitched_sound.overlay(echo, delay_ms, gain_during_overlay=-6)

    combined = combined + 10  # Increase volume slightly to simulate distortion
    
    return combined

def tts(text):
    """Converts given text into speech"""
    tts = gTTS(text=text, lang='en')
    audio_buffer = io.BytesIO()
    tts.write_to_fp(audio_buffer)
    audio_buffer.seek(0)

    sound = AudioSegment.from_file(audio_buffer, format="mp3")
    robot_sound = robotic(sound)
    
    play(robot_sound)
