
import sounddevice as sd
import speech_recognition as sr

# Microphone settings
SAMPLE_RATE = 16000
DURATION = 5

recognizer = sr.Recognizer()

print("\nSHRUVI MICROPHONE TEST")
print("----------------------")

try:
    print("\nAvailable microphones:")

    print(sd.query_devices())

    print("\nSHRUVI: I am listening...")
    print("Speak something for 5 seconds!")

    # Record your voice
    audio = sd.rec(
        int(DURATION * SAMPLE_RATE),
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype="int16"
    )

    sd.wait()

    print("\nSHRUVI: Recording completed!")
    print("SHRUVI: Understanding your voice...")

    # Convert recording into SpeechRecognition audio
    audio_data = sr.AudioData(
        audio.tobytes(),
        SAMPLE_RATE,
        2
    )

    # Recognize speech using Google Speech Recognition
    text = recognizer.recognize_google(
        audio_data,
        language="en-IN"
    )

    print("\nYOU SAID:", text)

    print("\nSHRUVI: I heard you!")

except sr.UnknownValueError:
    print("SHRUVI: Sorry, I couldn't understand your voice.")

except sr.RequestError as error:
    print("Internet recognition error:", error)

except Exception as error:
    print("Microphone error:", error)

