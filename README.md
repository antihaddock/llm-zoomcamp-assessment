# llm-zoomcamp-assignment
Assignment for DataTalks Club LLM Zoomcamp





## Additional notes for those trying the streamlit/grafana out

1) The following packages are required when you run some of .py scripts

```
pip install psycopg2-binary python-dotenv
pip install pgcli
```


2) To download the phi3 model to the container
```
docker-compose up -d
docker-compose exec ollama ollama pull phi3
```

# Problem description

This is a medical diagnosis Q and A chatbot built off a public source dataset know as the chat doctor 5K dataset. It can be found here:
https://raw.githubusercontent.com/Kent0n-Li/ChatDoctor/main/chatdoctor5k.json

This dataset has 5000 questions in a Q and A format for a variety of different medical issues. It fits nicely into a format which can be used in a
Q and A LLM process. The dataset is designed to allow you to ask the chatbot about various medical symptoms and return a response from the chatbot about the possible diagnosis going on.



# RAG flow

# Retrieval evaluation

# RAG evaluation

# Interface

There are two ways to interact with this RAG App:
1. Via the Streamlit front end UI
2. Directly via the backend API end points

Both will achieve the same outcome. The UI makes for an easier interaction and conversation flow for the user.


# Ingestion pipeline
Data is ingested via a simple python script located in `./backend/data_and_es_setup.py` This file will:
1. Download the dataset
2. Initialise and index the dataset in ElasticSearch
3. Create the postgres database for use of logging interactions.


# Monitoring

# Containerization

# Reproducibility
In order to run this app locally you will need to do the following steps:
1. Have docker installed locally
2. setup a .env file in the root directory in this format (insert your own Open AI key):

```
# PostgreSQL Configuration
POSTGRES_HOST=postgres
POSTGRES_DB=course_assistant
POSTGRES_USER=your_username
POSTGRES_PASSWORD=your_password
POSTGRES_PORT=5432

# Elasticsearch Configuration
ELASTIC_URL_LOCAL=http://localhost:9200
ELASTIC_URL=http://elasticsearch:9200
ELASTIC_PORT=9200

# Ollama Configuration
OLLAMA_PORT=11434

# Streamlit Configuration
STREAMLIT_PORT=8501

# Other Configuration
MODEL_NAME=multi-qa-MiniLM-L6-cos-v1
INDEX_NAME=chat_doctor_questions

#Open API Key
OPENAI_API_KEY= <your_API_KEY_HERE>
```
3. Docker compose build to build all the containers
4. Docker compose run
5. For the first time running you will need to call `docker-compose exec backend python data_and_es_setup.py` This will initialise the database and index the documents in ElasticSearch
6. You can then interact with the app either directly via the FastAPI end points (seen in /backend/main.py) or via the streamlit app frontend on URL: http://0.0.0.0:8501





# Scoring Criteria

    Problem description
        0 points: The problem is not described
        1 point: The problem is described but briefly or unclearly
        2 points: The problem is well-described and it's clear what problem the project solves
    RAG flow
        0 points: No knowledge base or LLM is used
        1 point: No knowledge base is used, and the LLM is queried directly
        2 points: Both a knowledge base and an LLM are used in the RAG flow
    Retrieval evaluation
        0 points: No evaluation of retrieval is provided
        1 point: Only one retrieval approach is evaluated
        2 points: Multiple retrieval approaches are evaluated, and the best one is used
    RAG evaluation
        0 points: No evaluation of RAG is provided
        1 point: Only one RAG approach (e.g., one prompt) is evaluated
        2 points: Multiple RAG approaches are evaluated, and the best one is used
    Interface
        0 points: No way to interact with the application at all
        1 point: Command line interface, a script, or a Jupyter notebook
        2 points: UI (e.g., Streamlit), web application (e.g., Django), or an API (e.g., built with FastAPI)
    Ingestion pipeline
        0 points: No ingestion
        1 point: Semi-automated ingestion of the dataset into the knowledge base, e.g., with a Jupyter notebook
        2 points: Automated ingestion with a Python script or a special tool (e.g., Mage, dlt, Airflow, Prefect)
    Monitoring
        0 points: No monitoring
        1 point: User feedback is collected OR there's a monitoring dashboard
        2 points: User feedback is collected and there's a dashboard with at least 5 charts
    Containerization
        0 points: No containerization
        1 point: Dockerfile is provided for the main application OR there's a docker-compose for the dependencies only
        2 points: Everything is in docker-compose
    Reproducibility
        0 points: No instructions on how to run the code, the data is missing, or it's unclear how to access it
        1 point: Some instructions are provided but are incomplete, OR instructions are clear and complete, the code works, but the data is missing
        2 points: Instructions are clear, the dataset is accessible, it's easy to run the code, and it works. The versions for all dependencies are specified.
    Best practices
        Hybrid search: combining both text and vector search (at least evaluating it) (1 point)
        Document re-ranking (1 point)
        User query rewriting (1 point)
    Bonus points (not covered in the course)
        Deployment to the cloud (2 points)
        Up to 3 extra bonus points if you want to award for something extra (write in feedback for what)
