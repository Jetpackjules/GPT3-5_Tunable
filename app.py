from gpt_index import SimpleDirectoryReader, GPTListIndex, GPTSimpleVectorIndex, LLMPredictor, PromptHelper
import gradio as gr
import os
from langchain.chat_models import ChatOpenAI
import json

os.environ["OPENAI_API_KEY"] = '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'

def construct_index(directory_path):
    max_input_size = 1096
    num_outputs = 2500
    max_chunk_overlap = 20
    chunk_size_limit = 600

    prompt_helper = PromptHelper(max_input_size, num_outputs, max_chunk_overlap, chunk_size_limit=chunk_size_limit)

    llm_predictor = LLMPredictor(llm=ChatOpenAI(temperature=0.7, model_name="gpt-3.5-turbo-0301", max_tokens=num_outputs))
    # gpt-3.5-turbo-0301
    # text-davinci-003

    documents = SimpleDirectoryReader(directory_path).load_data()

    index = GPTSimpleVectorIndex(documents, llm_predictor=llm_predictor, prompt_helper=prompt_helper)

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

    if time_difference > 1 * 1 * 60:  # Cooldown Timer (Hours * Minutes * Seconds) (set to 1 instead of zero for none)
        usage_data[str(client_ip)] = {'uses': 0, 'last_usage_time': current_time}

    return usage_data

def log_prompt_and_response(prompt, response, file_path='chat_log.txt'):
    with open(file_path, 'a') as file:
        file.write(f'Prompt: {prompt}\n')
        file.write(f'Response: {response}\n\n')

# Update the chatbot function
def chatbot(input_text, request: gr.Request):
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
        index = GPTSimpleVectorIndex.load_from_disk('index.json')
        response = index.query(input_text, response_mode="compact").response

    uses += 1
    usage_data[str(client_ip)] = {'uses': uses, 'last_usage_time': int(time.time())}
    save_usage_data(usage_data)

    # Log the prompt and response
    log_prompt_and_response(input_text, response)

    return response




iface = gr.Interface(fn=chatbot,
                     inputs=gr.inputs.Textbox(lines=7, label="Enter your text"),
                     outputs="text",
                     title="Custom-trained AI Chatbot")

# index = construct_index("docs")
iface.launch(share=True)
