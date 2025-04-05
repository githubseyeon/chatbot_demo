###### Initialization Stage #######
import json
import openai
import threading
import time
import queue as q
import os

# OpenAI API KEY
client = openai.OpenAI(api_key = os.environ['OPENAI_API'])

###### Main Function Stage #######

# Main function
def lambda_handler(event, context):

    run_flag = False
    start_time = time.time()
    
    # Store Kakao request data
    kakaorequest = json.loads(event['body'])

    # Create a text file to store the response
    filename ="/tmp/botlog.txt"
    if not os.path.exists(filename):
        with open(filename, "w") as f:
            f.write("")
    else:
        print("File Exists")    

    # Run the response-generating function
    response_queue = q.Queue()
    request_respond = threading.Thread(target=responseOpenAI,
                                        args=(kakaorequest, response_queue,filename))
    request_respond.start()

    # Check response generation time
    while (time.time() - start_time < 3.5):
        if not response_queue.empty():
            # Return the response immediately if it's ready within 3.5 seconds
            response = response_queue.get()
            run_flag= True
            break
        # Add delay for stable operation 
        time.sleep(0.01)

    # If response not generated within 3.5 seconds  
    if run_flag== False:     
        response = timeover()

    return{
        'statusCode':200,
        'body': json.dumps(response),
        'headers': {
            'Access-Control-Allow-Origin': '*',
        }
    }

# Function to handle text/image requests and responses  
def responseOpenAI(request,response_queue,filename):
    # When the user clicks the button to check if the response is ready  
    if '생각 다 끝났나요?' in request["userRequest"]["utterance"]:
        # Open the text file  
        with open(filename) as f:
            last_update = f.read()
        # If there is stored information in the text file  
        if len(last_update.split())>1:
            kind = last_update.split()[0]  
            if kind == "img":
                bot_res, prompt = last_update.split()[1],last_update.split()[2]
                response_queue.put(imageResponseFormat(bot_res,prompt))
            else:
                bot_res = last_update[4:]
                response_queue.put(textResponseFormat(bot_res))
            dbReset(filename)

    # If an image generation is requested 
    elif '/img' in request["userRequest"]["utterance"]:
        dbReset(filename)
        prompt = request["userRequest"]["utterance"].replace("/img", "")
        bot_res = getImageURLFromDALLE(prompt)
        response_queue.put(imageResponseFormat(bot_res,prompt))
        save_log = "img"+ " " + str(bot_res) + " " + str(prompt)
        with open(filename, 'w') as f:
            f.write(save_log)

    # If a ChatGPT text response is requested  
    elif '/ask' in request["userRequest"]["utterance"]:
        dbReset(filename)
        prompt = request["userRequest"]["utterance"].replace("/ask", "")
        bot_res = getTextFromGPT(prompt)
        response_queue.put(textResponseFormat(bot_res))
        save_log = "ask"+ " " + str(bot_res)
        with open(filename, 'w') as f:
            f.write(save_log)

    # If the chat does not contain any specific request 
    else:
        # Default response value 
        base_response = {'version': '2.0', 'template': {'outputs': [], 'quickReplies': []}}
        response_queue.put(base_response)

###### Function Implementation Stage #######  

# Send message  
def textResponseFormat(bot_response):
    response = {'version': '2.0', 'template': {
    'outputs': [{"simpleText": {"text": bot_response}}], 'quickReplies': []}}
    return response

# Send image  
def imageResponseFormat(bot_response,prompt):
    output_text = prompt + " - Here is an image based on the content"  
    response = {'version': '2.0', 'template': {
    'outputs': [{"simpleImage": {"imageUrl": bot_response,"altText":output_text}}], 'quickReplies': []}}
    return response

# Response when generation takes too long 
def timeover():
    response = {"version":"2.0","template":{
      "outputs":[
         {
            "simpleText":{
               "text":"I'm still thinking...🙏🙏\nPlease tap the speech bubble below in a moment👆"
            }
         }
      ],
      "quickReplies":[
         {
            "action":"message",
            "label":"Are you done thinking?🙋",
            "messageText":"Are you done thinking?"
         }]}}

    return response

# Request/receive response from ChatGPT 
def getTextFromGPT(messages):
    messages_prompt = [{"role": "system", "content": 'You are a thoughtful assistant. Respond to all input in 25 words and answer in korea'}]
    messages_prompt += [{"role": "user", "content": messages}]
    response = client.chat.completions.create(model="gpt-3.5-turbo", messages=messages_prompt)
    message = response.choices[0].message.content
    return message

# Request/receive image URL from DALLE 
def getImageURLFromDALLE(messages):   
    response = client.images.generate(
    model="dall-e-2",
    prompt=messages,
    size="512x512",
    quality="standard",
    n=1)
    image_url = response.data[0].url
    return image_url

# Reset the text file 
def dbReset(filename):
    with open(filename, 'w') as f:
        f.write("")
