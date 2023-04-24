import gradio as gr
import os
from langchain.chat_models import ChatOpenAI
import json
from llama_index import SimpleDirectoryReader
from llama_index import LLMPredictor, GPTSimpleVectorIndex, PromptHelper, ServiceContext
os.environ["OPENAI_API_KEY"] = 'API KEY HERE'

global service_context
def construct_index(directory_path):
    global service_context
    max_input_size = 4096
    num_output = 256
    max_chunk_overlap = 20
    chunk_size_limit = 1200


    documents = SimpleDirectoryReader(directory_path).load_data()

    llm_predictor = LLMPredictor(llm=ChatOpenAI(temperature=0.7, model_name="gpt-3.5-turbo-0301"))
    # suggested models:
    # gpt-4-0314
    # gpt-3.5-turbo-0301

    prompt_helper = PromptHelper(max_input_size, num_output, max_chunk_overlap)
    service_context = ServiceContext.from_defaults(llm_predictor=llm_predictor, prompt_helper=prompt_helper)
    index = GPTSimpleVectorIndex.from_documents(
    documents, service_context=service_context
    )
    

 
    
    index.save_to_disk('index.json')

    return index

# Managing json user data:
def load_usage_data(file_path='usage_data.json'):
    if not os.path.exists(file_path):
        return {}
    with open(file_path, 'r') as file:
        return json.load(file)

def save_usage_data(usage_data, file_path='usage_data.json'):
    with open(file_path, 'w') as file:
        json.dump(usage_data, file)



import time

def reset_usage_count_if_needed(usage_data, client_ip):
    current_time = int(time.time())
    last_usage_time = usage_data.get(str(client_ip), {}).get('last_usage_time', 0)
    time_difference = current_time - last_usage_time

    if time_difference > 24 * 60 * 60:  # Cooldown Timer (Hours * Minutes * Seconds) (set to 1 instead of zero for none)
        usage_data[str(client_ip)] = {'uses': 0, 'last_usage_time': current_time}

    return usage_data

def log_prompt_and_response(prompt, response, file_path='chat_log.txt'):
    with open(file_path, 'a') as file:
        file.write(f'Prompt: {prompt}\n')
        file.write(f'Response: {response}\n\n')

# Update the chatbot function
def chatbot(input_text, request: gr.Request):
    global service_context
    limit = 10
    client_ip = request.client.host
    print("IP ADDRESS: ", client_ip)

    usage_data = load_usage_data()
    usage_data = reset_usage_count_if_needed(usage_data, client_ip)

    uses = usage_data.get(str(client_ip), {}).get('uses', 0)

    if input_text == "admin_mode":
        uses = limit + 1
        response = "Infinite limit enabled for your IP!"
    elif uses == limit:
        return "Maximum of 10 uses reached! Wait 4 hours before trying again..."
    else:
        index = GPTSimpleVectorIndex.load_from_disk('index.json', service_context=service_context)
        response = index.query(input_text, response_mode="compact").response

    uses += 1
    usage_data[str(client_ip)] = {'uses': uses, 'last_usage_time': int(time.time())}
    save_usage_data(usage_data)

    # Log the prompt and response
    log_prompt_and_response(input_text, response)

    return response




iface = gr.Interface(fn=chatbot,
                     inputs=gr.inputs.Textbox(lines=15, label="Enter your text"),
                     outputs="text",
                     title="Custom-trained AI Chatbot")

index = construct_index("docs")
iface.launch(share=True)
