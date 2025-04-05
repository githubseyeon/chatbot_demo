###### Initialization Stage #######
from fastapi import Request, FastAPI
import openai
import threading
import time
import queue as q
import os

# OpenAI API KEY
API_KEY = "OpenAI API Key"
client = openai.OpenAI(api_key = API_KEY)

###### Function Implementation Staeg #######

# Sending message
def textResponseFormat(bot_response):
    response = {'version': '2.0', 'template': {
    'outputs': [{"simpleText": {"text": bot_response}}], 'quickReplies': []}}
    return response

# Sending image
def imageResponseFormat(bot_response,prompt):
    output_text = prompt+"내용에 관한 이미지 입니다"
    response = {'version': '2.0', 'template': {
    'outputs': [{"simpleImage": {"imageUrl": bot_response,"altText":output_text}}], 'quickReplies': []}}
    return response

# Response when overflow
def timeover():
    response = {"version":"2.0","template":{
      "outputs":[
         {
            "simpleText":{
               "text":"아직 제가 생각이 끝나지 않았어요🙏🙏\n잠시후 아래 말풍선을 눌러주세요👆"
            }
         }
      ],
      "quickReplies":[
         {
            "action":"message",
            "label":"생각 다 끝났나요?🙋",
            "messageText":"생각 다 끝났나요?"
         }]}}
    return response

# Getting response from ChatGPT
def getTextFromGPT(messages):
    messages_prompt = [{"role": "system", "content": 'You are a thoughtful assistant. Respond to all input in 25 words and answer in korea'}]
    messages_prompt += [{"role": "user", "content": messages}]
    response = client.chat.completions.create(model="gpt-3.5-turbo", messages=messages_prompt)
    message = response.choices[0].message.content
    return message

# Getting question/image URL from DALLE
def getImageURLFromDALLE(messages):   
    response = client.images.generate(
    model="dall-e-2",
    prompt=messages,
    size="512x512",
    quality="standard",
    n=1)
    image_url = response.data[0].url
    return image_url


# Resetting text file
def dbReset(filename):
    with open(filename, 'w') as f:
        f.write("")


###### Server Generation Stage #######
app = FastAPI()

@app.get("/")
async def root():
    return {"message": "kakaoTest"}

@app.post("/chat/")
async def chat(request: Request):
    kakaorequest = await request.json()
    return mainChat(kakaorequest)

###### Main Function Stage #######

# Main function
def mainChat(kakaorequest):

    run_flag = False
    start_time = time.time()

    # Generating text file to save the response
    cwd = os.getcwd()
    filename = cwd + '/botlog.txt'
    if not os.path.exists(filename):
        with open(filename, "w") as f:
            f.write("")
    else:
        print("File Exists")    

    # Running response generating function
    response_queue = q.Queue()
    request_respond = threading.Thread(target=responseOpenAI,
                                        args=(kakaorequest, response_queue,filename))
    request_respond.start()

    # checking time taken to generate the response
    while (time.time() - start_time < 3.5):
        if not response_queue.empty():
            # if time <= 3.5s, return the response right away
            response = response_queue.get()
            run_flag= True
            break
        # delay time for stable operation
        time.sleep(0.01)

    # if time > 3.5s
    if run_flag== False:     
        response = timeover()

    return response

# Function to handle text/image requests and responses
def responseOpenAI(request,response_queue,filename):
    # When the user clicks the button to check if the response is ready
    if '생각 다 끝났나요?' in request["userRequest"]["utterance"]:
        # Open text file
        with open(filename) as f:
            last_update = f.read()
        # If there exists some stored information in the text file
        if len(last_update.split())>1:
            kind = last_update.split()[0]  
            if kind == "img":
                bot_res, prompt = last_update.split()[1],last_update.split()[2]
                response_queue.put(imageResponseFormat(bot_res,prompt))
            else:
                bot_res = last_update[4:]
                response_queue.put(textResponseFormat(bot_res))
            dbReset(filename)

    # If image generation is requested
    elif '/img' in request["userRequest"]["utterance"]:
        dbReset(filename)
        prompt = request["userRequest"]["utterance"].replace("/img", "")
        bot_res = getImageURLFromDALLE(prompt)
        response_queue.put(imageResponseFormat(bot_res,prompt))
        save_log = "img"+ " " + str(bot_res) + " " + str(prompt)
        with open(filename, 'w') as f:
            f.write(save_log)

    # If ChatGPT text response is requested
    elif '/ask' in request["userRequest"]["utterance"]:
        dbReset(filename)
        prompt = request["userRequest"]["utterance"].replace("/ask", "")
        bot_res = getTextFromGPT(prompt)
        response_queue.put(textResponseFormat(bot_res))

        save_log = "ask"+ " " + str(bot_res)
        with open(filename, 'w') as f:
            f.write(save_log)
            
    # If the chat x contain any specific request
    else:
        # Default response value
        base_response = {'version': '2.0', 'template': {'outputs': [], 'quickReplies': []}}
        response_queue.put(base_response)