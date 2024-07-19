#To Use

1. Install requirements into your python env of choice: 

```python  
pip3 install -r requirements.txt
```

2. Fill out `.streamlit/secrets.toml` with your account information. 

```
[connections.snowflake]
account = 
user = 
password = 
role = 
warehouse = 
```

3. Run app locally: 

```python
streamlit run app.py
``` 

4. Navigate to the app. Insert values into the streamlit app and run!

5. Note that the VPS account will need to use your share token to allow sharing. Have them contact Snowflake support if they are not sure how to accomplish this. 


