import openai

# 모델 생성 및 API key 입력
API_KEY = 'Enter your API key here'
client = openai.OpenAI(api_key = API_KEY)

# 녹음 파일 열기
audio_file = open("output.mp3", "rb")

# whisper 모델에 음원 파일 전달
transcript = client.audio.transcriptions.create(model = "whisper-1", file = audio_file)

# 결과 보기
print(transcript.text)
