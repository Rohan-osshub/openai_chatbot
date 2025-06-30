import openai
import pyaudio
import wave
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# Audio recording parameters
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 24000
CHUNK = 1024
RECORD_SECONDS = 5
WAVE_OUTPUT_FILENAME = "input.wav"

def record_audio():
    """Record audio from the microphone and save to a WAV file."""
    audio = pyaudio.PyAudio()
    stream = audio.open(format=FORMAT, channels=CHANNELS,
                        rate=RATE, input=True, frames_per_buffer=CHUNK)
    print("Recording... Speak now.")
    frames = []
    for _ in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
        data = stream.read(CHUNK)
        frames.append(data)
    print("Recording finished.")
    stream.stop_stream()
    stream.close()
    audio.terminate()
    wf = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(audio.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(frames))
    wf.close()

def transcribe_audio(filename):
    """Transcribe audio file using OpenAI Whisper."""
    with open(filename, "rb") as audio_file:
        transcript = openai.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file
        )
    return transcript.text

def chat_with_gpt(prompt, messages, force_arabic=False):
    """Send user prompt to OpenAI GPT and get response."""
    if force_arabic:
        messages.append({"role": "system", "content": "الرجاء الرد باللغة العربية فقط."})
    messages.append({"role": "user", "content": prompt})
    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages
    )
    reply = response.choices[0].message.content
    messages.append({"role": "assistant", "content": reply})
    return reply

def text_to_speech(text, output_filename="output.wav", voice="nova"):
    """Convert text to speech using OpenAI TTS and save as WAV."""
    response = openai.audio.speech.create(
        model="tts-1",
        voice=voice,
        input=text,
        response_format="wav"
    )
    with open(output_filename, "wb") as f:
        f.write(response.content)

def play_audio(filename):
    """Play a WAV audio file."""
    chunk = 1024
    wf = wave.open(filename, 'rb')
    pa = pyaudio.PyAudio()
    stream = pa.open(format=pa.get_format_from_width(wf.getsampwidth()),
                     channels=wf.getnchannels(),
                     rate=wf.getframerate(),
                     output=True)
    data = wf.readframes(chunk)
    while data:
        stream.write(data)
        data = wf.readframes(chunk)
    stream.stop_stream()
    stream.close()
    pa.terminate()
    wf.close()

def is_arabic(text):
    """Detect if the text contains Arabic characters."""
    return any('\u0600' <= c <= '\u06FF' for c in text)

def main():
    messages = [
        {"role": "system", "content": "You are AI Therapist, and your job is to help users with their mental health. Respond in Arabic if the user asks for Arabic or starts the conversation in Arabic."}
    ]
    print("Hello! I am Nova, How may I assist you today?")
    print("Choose input mode:")
    print("1. Voice (English/Arabic)")
    print("2. Text (English)")
    print("3. Text (Arabic)")
    mode = input("Enter 1 for Voice, 2 for Text (English), or 3 for Text (Arabic): ").strip()

    while True:
        if mode == "1":
            record_audio()
            user_input = transcribe_audio(WAVE_OUTPUT_FILENAME)
            print(f"User: {user_input}")
            if user_input.lower() in ["exit", "quit", "bye", "خروج", "انهاء"]:
                print("Goodbye!")
                break
            force_arabic = is_arabic(user_input)
            reply = chat_with_gpt(user_input, messages, force_arabic=force_arabic)
            print(f"Nova: {reply}")
            # Use shimmer for Arabic, nova for English
            voice = "shimmer" if is_arabic(reply) else "nova"
            text_to_speech(reply, voice=voice)
            play_audio("output.wav")
            os.remove(WAVE_OUTPUT_FILENAME)
            os.remove("output.wav")
        elif mode == "2":
            user_input = input("You: ")
            if user_input.lower() in ["exit", "quit", "bye"]:
                print("Goodbye!")
                break
            reply = chat_with_gpt(user_input, messages)
            print(f"Nova: {reply}")
            text_to_speech(reply, voice="nova")
            play_audio("output.wav")
            os.remove("output.wav")
        elif mode == "3":
            user_input = input("أنت: ")
            if user_input.lower() in ["خروج", "انهاء", "exit", "quit", "bye"]:
                print("مع السلامة!")
                break
            reply = chat_with_gpt(user_input, messages, force_arabic=True)
            print(f"نوفا: {reply}")
            text_to_speech(reply, voice="shimmer")
            play_audio("output.wav")
            os.remove("output.wav")
        else:
            print("Invalid mode. Please restart and choose 1, 2, or 3.")
            break

if __name__ == "__main__":
    main()