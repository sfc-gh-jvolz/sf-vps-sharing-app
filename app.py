import streamlit as st
import sql_commands as commands
import utils


#page configuration 
st.set_page_config(layout="wide", 
                   initial_sidebar_state='collapsed', 
                   page_title="Snowflake Resharing App")

#Title
st.title('Snowflake VPS Sharing App')

#SF Connection 
sf_con = st.connection("snowflake")

#sidebar
utils.display_sidebar(st, sf_con)

st.header("Request to Share with VPS Account.")

utils.generate_share_request_ui(st, sf_con)

st.header("Share Data with VPS Account.")

utils.generate_share_ui(st, sf_con)

if st.button("Clear Log", help="Clear log"): 
    utils.reset_log(st)
st.text_area("Log", value="Welcome to the Snowflake VPS Sharing App \n", key="log", disabled=True, height=400)




