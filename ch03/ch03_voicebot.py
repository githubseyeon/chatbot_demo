import streamlit as st
from audiorecorder import audiorecorder    # audiorecorder 피키지 추가
import openai   # OpenAI 패키지 추가
import os   # 파일 삭제를 위한 패키지 추가
from datetime import datetime   # 시간 정보를 위한 패키지 추가
from gtts import gTTS   # TTS 패키지 추가
import base64   # 음원 파일을 재생하기 위한 패키지 추가


### 메인 함수 ###
def main():
    # 기본 설정
    st.set_page_config(
        page_title = "음성 비서 프로그램",
        layout = "wide"
    )

    # 제목
    st.header("음성 비서 프로그램")

    # 구분선
    st.markdown("---")

    # 기본 설명
    with st.expander("음성 비서 프로그램에 관하여", expanded=True):
        st.write(
        """
        - 음성 비서 프로그램의 UI는 스트림릿을 활용
        - STT(Speech-To-Text)는 OpenAI의 Whisper AI를 활용
        - 답변은 OpenAI의 GPT 모델을 활용
        0 TTS(Text-To-Speech)는 구글의 Google Translate TTS를 활용
        """
        )

        st.markdown("")

    # session state 초기화
    if "chat" not in st.session_state:
        st.session_state["chat"] = []

    if "OPENAI_API" not in st.session_state:
        st.session_state["OPENAI_API"] = ""

    if "message" not in st.session_state:
        st.session_state["messages"] = [{"role": "system",
                                         "content": "You are a thoughtful assistant. Respond to all inputs in 25 words and answer in Korean"}]

    if "check_audio" not in st.session_state:
        st.session_state["check_reset"] = False 

    # 사이드바 생성
    with st.sidebar:

        # Open AI API 키 입력받기
        st.session_state["OPENAI_API"] = st.text_input(label="OPENAI API 키",
                                                       placeholder="Enter Your API Key",
                                                       value="",
                                                       type="password")
        
        st.markdown("---")

        # GPT 모델을 선택하기 위한 라디오 버튼 생성
        model = st.radio(label="GPT 모델", options=["gpt-4", "gpt-3.5-turbo"])

        st.markdown("---")

        # 리셋 버튼 설정
        if st.button(label="초기화"):
            # 리셋 코드
            st.session_state["chat"] = []
            st.session_state["messages"] = [{"role": "system",
                                         "content": "You are a thoughtful assistant. Respond to all inputs in 25 words and answer in Korean"}]
            st.session_state["check_reset"] = True 

    # 기능 구현 공간
    col1, col2 = st.columns(2)
    with col1:
        # 왼쪽 영역 작성
        st.subheader("질문하기")
        # 음성 녹음 아이콘 추가
        audio = audiorecorder("클릭하여 녹음하기", "녹음 중...")
        if (audio.duration_seconds > 0) and (st.session_state["check_reset"] == False):    # 녹음을 실행하면?
            # 음성 재생
            st.audio(audio.export().read())

            # 음원 파일에서 텍스트 추출
            question = STT(audio, st.session_state["OPENAI_API"])

            # 채팅을 시각화하기 위해 질문 내용 저장
            now = datetime.now().strftime("%H:%M")
            st.session_state["chat"] = st.session_state["chat"]+[("user", now, question)]

            # GPT 모델에 넣을 프롬프트를 위해 질문 내용 저장
            st.session_state["messages"] = st.session_state["messages"]+[{"role": "user", "content": question}]

    with col2:
        # 오른쪽 영역 작성
        st.subheader("질문/답변")
        if (audio.duration_seconds > 0) and (st.session_state["check_reset"]==False):
            # ChatGPT에게 답변 받기
            response = ask_gpt(st.session_state["messages"], model, st.session_state["OPENAI_API"])

            # GPT 모델에 넣을 프롬프트를 위해 답변 내용 저장
            st.session_state["messages"] = st.session_state["messages"] + [{"role": "system", "content": response}]

            # 채팅 시각화를 위한 답변 내용 저장
            now = datetime.now().strftime("%H:%M")
            st.session_state["chat"] = st.session_state["chat"] + [("bot", now, response)]

            # 채팅 형식으로 시각화하기
            for sender, time, message in st.session_state["chat"]:
                if sender == "user":
                    st.write(f'<div style="display:flex;align-items:center;"><div style="background-color:#007AFF;color:white;border-radius:12px;padding:8px 12px;marginright:8px;">{message}</div><div style="font-size:0.8rem;color:gray;">{time}</div></ div>', unsafe_allow_html=True)
                    st.write("")
                else:
                    st.write(f'<div style="display:flex;align-items:center;justifycontent:flex-end;"><div style="background-color:lightgray;border-radius:12px;padding:8px 12px;margin-left:8px;">{message}</div><div style="font-size:0.8rem;color:gray;">{time}</ div></div>', unsafe_allow_html=True)
                    st.write("")

            # gTTS를 활용하여 음성 파일 생성 및 재생
            TTS(response)


##### 기능 구현 함수 #####
def STT(audio, apikey):
    # 파일 저장
    filename = 'input.mp3'
    audio.export(filename, format="mp3")

    # 음원 파일 열기
    audio_file = open(filename, "rb")
    # Whisper 모델을 활용해 텍스트 얻기
    client = openai.OpenAI(api_key = apikey)
    response = client.audio.transcriptions.create(model = "whisper-1", file = audio_file)
    audio_file.close()
    # 파일 삭제
    os.remove(filename)
    return response.text

def ask_gpt(prompt, model, apikey):
    client = openai.OpenAI(api_key = apikey)
    response = client.chat.completions.create(
        model=model,
        messages=prompt
    )
    gptResponse = response.choices[0].message.content
    return gptResponse

def TTS(response):
    # gTTS를 활용하여 음성 파일 생성
    filename = "output.mp3"
    tts = gTTS(text=response, lang="ko")
    tts.save(filename)
    # 음원 파일 자동 재생
    with open(filename, "rb") as f:
        data = f.read()
        b64 = base64.b64encode(data).decode()
        md = f"""
        <audio autoplay="True">
        <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
        </audio>
        """
        st.markdown(md, unsafe_allow_html=True,)
    # 파일 삭제
    os.remove(filename)


if __name__ == "__main__":
    main()






