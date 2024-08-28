# llm-zoomcamp-assignment
Assignment for DataTalks Club LLM Zoomcamp


Dataset used:
https://github.com/Kent0n-Li/ChatDoctor/blob/main/chatdoctor5k.json



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