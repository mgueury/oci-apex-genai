# Author: Ansh
from my_directory_loader import MyDirectoryLoader
from langchain.docstore.document import Document
from langchain_community.vectorstores import Qdrant
import oci
import flask
import os
from flask import Flask, request
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import OCIGenAIEmbeddings
from langchain_community.vectorstores.oraclevs import OracleVS
from langchain_community.vectorstores.utils import DistanceStrategy
import oracledb
import config  # Import the configuration
from oci.generative_ai_inference import GenerativeAiInferenceClient
from oci.generative_ai_inference.models import CohereChatRequest
from oci.generative_ai_inference.models import ChatDetails, OnDemandServingMode
from oci.auth.signers import InstancePrincipalsSecurityTokenSigner
from oci.retry import NoneRetryStrategy

# Initialize connection based on DB_TYPE
if config.DB_TYPE == "oracle":
    try:
        connection = oracledb.connect(user=config.ORACLE_USERNAME, password=config.ORACLE_PASSWORD, dsn=config.ORACLE_TNS)
        print("Connection to OracleDB successful!")
    except Exception as e:
        print("Connection to OracleDB failed!")
else:
    connection = None

compartment_id=os.getenv("TF_VAR_compartment_ocid")
objectStorageLink = config.OBJECT_STORAGE_LINK  # Put your own object storage link
directory = config.DIRECTORY  # directory to your documents
prompt_context = config.PROMPT_CONTEXT
endpoint = config.ENDPOINT
embeddingModel = config.EMBEDDING_MODEL
generateModel = config.GENERATE_MODEL

oci_signer = InstancePrincipalsSecurityTokenSigner()

def load_docs(directory):
    loader = MyDirectoryLoader(directory)
    documents = loader.load(connection)
    return documents

documents = load_docs(directory)

def split_docs(documents, chunk_size=1000, chunk_overlap=100):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    docs = text_splitter.split_documents(documents)
    return docs

docs = split_docs(documents)
embeddings = OCIGenAIEmbeddings(
    model_id=embeddingModel,
    service_endpoint=endpoint,
    compartment_id=compartment_id,
    auth_type="INSTANCE_PRINCIPAL",
)

if config.DB_TYPE == "oracle":  
    db = OracleVS.from_documents(
        docs,
        embeddings,
        client=connection,
        table_name=config.ORACLE_TABLE_NAME,
        distance_strategy=DistanceStrategy.DOT_PRODUCT,
    )
else:
    db = Qdrant.from_documents(
        docs,
        embeddings,
        location=config.QDRANT_LOCATION,
        collection_name=config.QDRANT_COLLECTION_NAME,
        distance_func=config.QDRANT_DISTANCE_FUNC
    )

def get_similar_docs(query, k=3, score=False):
    if score:
        similar_docs = db.similarity_search_with_score(query, k=k)
    else:
        similar_docs = db.similarity_search(query, k=k)
    return similar_docs

flask_app = Flask(__name__)

@flask_app.route('/cohere/generate', methods=['POST'])
def generate_text():
    request_data = request.get_json()
    text = request_data.get('text')
    previous_chat_message = request_data.get('previous_chat_message', "Hi")
    previous_chat_reply = request_data.get('previous_chat_reply', "Hello")
    userDetails = request_data.get('userDetails', "Ansh")
    max_tokens = request_data.get('max_tokens', 200)
    temperature = request_data.get('temperature', 0)
    frequency_penalty = request_data.get('frequency_penalty', 1.0)
    top_p = request_data.get('top_p', 0.7)
    top_k = request_data.get('top_k', 1.0)
    model_id = request_data.get('model_id', generateModel)
    similar_docs = get_similar_docs(text)
    print("************************context *******************")
    print(similar_docs)
    concatenated_content = ""
    sourceLinks = ""
    sourcePageNumber = ""
    unique_source_links = set()
    for document in similar_docs:
        concatenated_content += document.page_content
        source_link = document.metadata["source"]
        sourcePageNumber = int(document.metadata["page"])
        sourcePageNumber = sourcePageNumber + 1
        if source_link not in unique_source_links:
            unique_source_links.add(source_link)
            sourceLinks += "<a href='" + objectStorageLink + source_link + "#page=" + str(sourcePageNumber) + "' target='_blank'>" + source_link[source_link.rfind("/") + 1:] + " (page " + str(sourcePageNumber) + ")</a>\n"

    print("************************question *******************")
    print(text)
   
    documents = [
        {
            "title": "Oracle",
            "snippet": concatenated_content,
            "website": "https://www.oracle.com/database"
        }
    ]
    # previous_chat_message = oci.generative_ai_inference.models.CohereMessage(role="USER", message=previous_chat_message)
    # previous_chat_reply = oci.generative_ai_inference.models.CohereMessage(role="CHATBOT", message=previous_chat_reply)
    # chat_request.chat_history = [previous_chat_message, previous_chat_reply]
    
    # Create the Generative AI Inference client
    generative_ai_inference_client = GenerativeAiInferenceClient(config={}, signer=oci_signer, service_endpoint=endpoint, retry_strategy=NoneRetryStrategy(), timeout=(10, 240))

    # Create the chat request
    chat_request = CohereChatRequest(
        message=text,
        max_tokens=max_tokens,
        is_stream=False,
        temperature=temperature,
        top_k=top_k,
        top_p=top_p,
        documents = documents,
        frequency_penalty=frequency_penalty,
        preamble_override = prompt_context
    )

    # Create the chat details
    chat_detail = ChatDetails(
        serving_mode=OnDemandServingMode(model_id=model_id),
        compartment_id=compartment_id,
        chat_request=chat_request
    )
    print("The chat request is ---->")
    print(chat_request)
    chat_response = generative_ai_inference_client.chat(chat_detail)

    # Print result
    print("**************************Chat Result**************************")
    chat_response_text = chat_response.data.chat_response.text
    print("Extracted text:", chat_response_text)
    return oci.util.to_dict(chat_response_text + ' For more info check the below links: \n' + sourceLinks)

if __name__ == '__main__':
    flask_app.run(host='0.0.0.0', port=3000)