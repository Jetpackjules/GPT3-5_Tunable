# from gpt_index import SimpleDirectoryReader, GPTListIndex, GPTSimpleVectorIndex, LLMPredictor, PromptHelper
import gpt_index
from gpt_index import *
from langchain import OpenAI
import gradio as gr
import sys
import os
from langchain.chat_models import ChatOpenAI

os.environ["OPENAI_API_KEY"] = 'API KEY HERE'

def construct_index(directory_path):
    max_input_size = 4096
    num_outputs = 2500
    max_chunk_overlap = 20
    chunk_size_limit = 600

    prompt_helper = PromptHelper(max_input_size, num_outputs, max_chunk_overlap, chunk_size_limit=chunk_size_limit)

    llm_predictor = LLMPredictor(llm=ChatOpenAI(temperature=0.7, model_name="gpt-3.5-turbo-0301", max_tokens=num_outputs))
    # llm_predictor = LLMPredictor(llm=OpenAI(temperature=0.7, model_name="gpt-3.5-turbo-0301", max_tokens=num_outputs))
    # gpt-3.5-turbo-0301
    # text-davinci-003
    documents = SimpleDirectoryReader(directory_path).load_data()

    index = GPTSimpleVectorIndex(documents, llm_predictor=llm_predictor, prompt_helper=prompt_helper)
    # index = GPTSimpleVectorIndex(documents, prompt_helper=prompt_helper)
    
    # pip install gpt_index==0.4.27

    index.save_to_disk('index.json')

    return index

def chatbot(input_text):
    index = GPTSimpleVectorIndex.load_from_disk('index.json')
    response = index.query(input_text, response_mode="compact")
    return response.response

iface = gr.Interface(fn=chatbot,
                     inputs=gr.inputs.Textbox(lines=7, label="Enter your text"),
                     outputs="text",
                     title="Custom-trained AI Chatbot")

#index = construct_index("docs")
iface.launch(share=True)