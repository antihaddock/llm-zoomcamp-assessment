# llm-zoomcamp-assignment
Assignment for DataTalks Club LLM Zoomcamp
Submitted October 2024




# Problem description

We want to build a LLM chatbot which can help individuals get information related to their health and symptoms. This is not a diagnostic tool but is aimed to be a triage tool to possibly assist health professionals and patients identify the urgency of there condition. The chatbot is built off  a medical diagnosis Q and A chatbot built off a public source dataset know as the chat doctor 5K dataset. It can be found here:
https://raw.githubusercontent.com/Kent0n-Li/ChatDoctor/main/chatdoctor5k.json

This dataset has 5000 questions in a Q and A format for a variety of different medical issues. It fits nicely into a format which can be used in a
Q and A LLM process. The dataset is designed to allow you to ask the chatbot about various medical symptoms and return a response from the chatbot about the possible diagnosis going on.

This allows for individuals to converse with the chatbot to ask questions related to symptoms they may be having and recieve information back for them to determine the severity of there symptoms and urgency for seeking treatment.

# RAG flow

This process utilises a RAG retrieval process using Elastic Search as our knowledge database and a LLM for retrieval. Our dataset is ingested into Elastic search where it is stored as text and vectors.

When a user submits a query this is indexed against the most relevant embeddings in the elastic search database. This embeddings are then converted back to text and passed to the prompt for the LLM along with the query. The LLM prompt is built in such a way that the LLM will only provide an answer from information contained within the prompt. If no relevant embeddings are retrieved then the LLM will respond it does not know an answer to that question.


# RAG evaluation

The following evaluation approaches are used:
1. LLM as a judge is undertaken to rate the response into relevant, partially relevant or not relevant.

There was not enough time to generate ground truths and apply non LLM based metrics for the quality of the LLM responses.

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

This file can be called after `docker compose run` via calling in the backend container (specific steps are detailed below)
   
  
# Monitoring
The RAG LLM is monitored by Grafana dashboard. This dashboard is connected to a postgres database from which data is logged from LLM interactions. User feedback, LLM conversations and metadata related to the LLM are provided on the dashboard. THe dashboard can be accessed via `localhost:3001`, A dashboard monitoring the chatbot performance is configured in the container. To load the dashboard for the first time you will need to load the json file in `./grafan/dashboard.json`

# Containerization
The entire app and its dependencies in containerised in the `docker-compose` file in the root directory. There are the following container dependencies
1. Frontend stream lit UI
2. Backend Fast API with multiple API end points, callable directly or via the UI
3. Ollama docker container
4. Postgres docker container for storage of conversation data and feedback
5. Elastic search container for storage documents ingested
6. Grafana container running a Grafan instance for monitoring

The frontend and backend contain there own specific `Dockerfile` in there subdirectories while the remainder of the containers are the official offerings from each vendor.

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
3. `docker compose build` to build all the containers
4. `docker compose run`
5. For the first time running you will need to call `docker-compose exec backend python data_and_es_setup.py` This will initialise the database and index the documents in ElasticSearch
6. You can then interact with the app either directly via the FastAPI end points (seen in /backend/main.py) or via the streamlit app frontend on URL: http://0.0.0.0:8501
The individual backend API endpoints can be seen in `backend/main.py` . All environmental variables and dependencies are stored in `.env` in the root directory and `requirements.txt` in the `./backend/` and `./frontend/` sub directories


# Best practices

We implement the following best practices.

Query rewriting
User query rewriting is done via the function `improve_query` in `./backend/chat_function.py` at line 274. Here we pass the original prompt to a LLM (defaults to OpenAI but can be connected to Ollama instead). This will check for spelling, grammar and clarity, adjusting the prompt as required.
