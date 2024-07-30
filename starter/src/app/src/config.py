# config.py
# Author: Ansh
import os

DB_TYPE = "oracle"  # Options: "oracle", "qdrant"

# OracleDB Configuration
# ORACLE_DB_USER = "xxx"  #Enter your oracle vector Db username
# ORACLE_DB_PWD = "xxxx"  #Enter your oracle vector Db password
# ORACLE_DB_HOST_IP = "xxxx"  #Enter your oracle vector Db host ip
# ORACLE_DB_PORT = xxx   #Enter your oracle vector Db host port
# ORACLE_DB_SERVICE = "xxx.xxx.oraclevcn.com" 
ORACLE_TNS = "##DB_URL##"
ORACLE_USERNAME = "##DB_USER##"
ORACLE_PASSWORD = "##DB_PASSWORD##"
ORACLE_TABLE_NAME = "docs_langchain" #name of table where you want to store the embeddings in oracle DB

# Qdrant Configuration
# QDRANT_LOCATION = ":memory:"
# QDRANT_COLLECTION_NAME = "my_documents" #name of table where you want to store the embeddings in qdrant DB
# QDRANT_DISTANCE_FUNC = "Dot"

# Common Configuration
OBJECT_STORAGE_LINK = "https://objectstorage.##REGION##.oraclecloud.com/n/##NAMESPACE##/b/##PREFIX##-public-bucket/o/"
DIRECTORY = 'data'  # directory to store the pdf's from where the RAG model should take the documents from
PROMPT_CONTEXT = "You are an AI Assistant trained to give answers based only on the information provided. Given only the above text provided and not prior knowledge, answer the query. If someone asks you a question and you don't know the answer, don't try to make up a response, simply say: I don't know."
ENDPOINT= "https://inference.generativeai.eu-frankfurt-1.oci.oraclecloud.com" #change in case you want to select a diff region
EMBEDDING_MODEL = "cohere.embed-multilingual-v3.0"
GENERATE_MODEL = "cohere.command-r-plus"  # cohere.command-r-16k or cohere.command-r-plus
