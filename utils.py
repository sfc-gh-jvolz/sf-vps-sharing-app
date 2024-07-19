import pandas as pd 
import sql_commands as commands
from datetime import datetime
import time 

MANIFEST = """artifacts:
 setup_script: setup.sql
"""

def get_current_org(sf_con): 
    query = commands.current_org
    df = execute_command(query, sf_con)
    try: 
        org_name = df['CURRENT_ORGANIZATION_NAME()'][0]
    except: 
        org_name = sf_con.raw_connection.account

    return org_name

def get_databases(sf_con): 
    query = commands.show_databases
    df = execute_command(query, sf_con)
    try: 
        databases = df['name'].to_list()
    except: 
        databases = [sf_con.raw_connection.database]

    return databases

def get_objects(sf_con, database):
    query = commands.show_objects.replace("<DB_NAME>", database)
    df = execute_command(query, sf_con)
    df = df[df.schema_name != 'INFORMATION_SCHEMA']
    try: 
        df["objects"] = df["schema_name"]  + "." + df['name']
        object_types = df['kind'].to_list() 
        objects = df["objects"].to_list()
    except: 
        object_types=[]
        objects = []

    return objects, object_types
    

def generate_share_request_ui(st, sf_con): 

    org_name = get_current_org(sf_con)
    
    client_name = st.text_input("Your Company Name", value=org_name, key="company_name")

    contact_email = st.text_input ("VPS Account Email", key="contact_email", help = "Email address of someone in the vps account who can enable sharing. This is where the share token will be sent.")
    if st.button("Generate Share Request", type="primary"):
    
        with st.spinner('Generating...'):
            
            token = generate_share_token(sf_con)
            log(st, "Created token: %s" %token)

            query = commands.create_email_integration
            df = execute_command(query, sf_con)

            query = commands.send_email\
                .replace("<CLIENT_NAME>", client_name)\
                .replace("<TOKEN>", token)\
                .replace("<EMAIL>", contact_email)
            execute_command(query, sf_con)

            log(st, "Sent email to %s with token." %contact_email)
            log(st, "When you have received confirmation from the VPS account that sharing is enabled, please proceed to the next step to share your data with the VPS account.")

def generate_share_token(sf_con): 
    #save current user
    current_role = sf_con.raw_connection.role 
    
    #change to org admin
    #currently required to generate token
    query = commands.use_orgadmin
    df = execute_command(query, sf_con)

    try: 
        #generate token 
        query = commands.create_share_token.replace("<PROVIDER_TYPE>", 'PUBLIC_PROVIDER')
        df = execute_command(query, sf_con)
        token = df['SYSTEM$GENERATE_CROSS_REGION_GROUP_SHARING_TOKEN'][0]
    finally: 
        #switch back to current role
        query = commands.use_role.replace("<ROLE>", current_role)
        df = execute_command(query, sf_con)

    return token 
 
def generate_share_ui(st, sf_con): 

    databases = get_databases(sf_con)
    database = st.selectbox("Which Database would you like to share from?", databases, index=0)

    objects, object_types = get_objects(sf_con, database)
    objects_map = {objects[i]:object_types[i] for i in range(len(objects))}
    tables = st.multiselect("Select the objects to share.", objects)

    org_name = st.session_state.company_name
    share_name = st.text_input("Data Share Name", value = "%s_DATA_SHARE" %org_name)
    listing_name = st.text_input("Listing Name", value = "%s_LISTING" %share_name)
    target_accounts = st.text_input("Target Accounts", help = "A comma-separated list of accounts you wish to share to")

    if st.button("Share Data", type="primary"):
    
        with st.spinner('Sharing...'):

            
            log(st, "Creating Share %s" %share_name)
            create_share(st, sf_con, share_name)
            
            if len(tables)>0: 
                schema_list, table_list, = zip(*[x.split(".") for x in tables])
                
                populate_share(st, sf_con, database, schema_list, tables, share_name, objects_map)
                    
                create_listing(st, sf_con, listing_name, share_name, org_name, target_accounts)

                publish_listing(st, sf_con, listing_name)
            else: 
                log(st, "No tables selected for share. Please select tables to share before trying to share data.")

def create_share(st, sf_con, share_name): 
    #create share 
    query = commands.create_share.replace("<SHARE_NAME>", share_name).replace("<SECURE_OBJECTS_ONLY>", 'True')
    r = execute_command(query, sf_con)

def populate_share(st, sf_con, database, schemas, tables, share_name, objects_map): 
    #add database to share 
    query = commands.grant_to_share.replace("<SHARE_NAME>", share_name)\
            .replace("<OBJECT_TYPE>", "database")\
            .replace("<OBJECT_NAME>", database)\
            .replace("<OPERATION>", "usage")
    execute_command(query, sf_con)

    #add schemas to share
    for s in set(schemas): 
        query = commands.grant_to_share.replace("<SHARE_NAME>", share_name)\
            .replace("<OBJECT_TYPE>", "schema")\
            .replace("<OBJECT_NAME>", "%s.%s" %(database, s))\
            .replace("<OPERATION>", "usage")
        execute_command(query, sf_con)

    #add tables to share
    for t in tables: 
        query = commands.grant_to_share.replace("<SHARE_NAME>", share_name)\
                .replace("<OBJECT_TYPE>", objects_map.get(t))\
                .replace("<OBJECT_NAME>", "%s.%s" %(database, t))\
                .replace("<OPERATION>", "select")
        execute_command(query, sf_con)

def create_listing(st, sf_con, listing_name, share_name, org_name, target_accounts): 
    listing_manifest = get_listing_manifest(st, listing_name, org_name, target_accounts) 
    #create listing
    try: 
        query = commands.create_listing.replace("<LISTING_NAME>", listing_name)\
            .replace("<SHARE_TYPE>", "SHARE")\
            .replace("<SHARE_NAME>", share_name)\
            .replace("<LISTING_MANIFEST>", listing_manifest )\
            .replace("<PUBLISH>", "False")\
            .replace("<REVIEW>", "False")
        execute_command(query, sf_con)

        log(st,"Successfully created private listing %s!" %listing_name)
    except Exception as e:
        log(st, "Exception: %s" %str(e)) 

def publish_listing(st, sf_con, listing_name): 
    #publish listing
    query = commands.publish_listing.replace("<LISTING_NAME>", listing_name)
    execute_command(query, sf_con)
    log(st, "Successfully published private listing %s" %listing_name)

def get_listing_manifest(st, listing_name, org_name, target_accounts): 
    target_accounts = "'" + "','".join(target_accounts.split(",")) + "'" 

    manifest = commands.listing_manfiest.replace("<LISTING_TITLE>", listing_name)\
        .replace("<LISTING_SUBTITLE>", "Data Shared from %s to VPS account" %org_name)\
        .replace("<LISTING_DESCRIPTION>", "Daata Shared from %s to VPS account" %org_name)\
        .replace("<LISTING_TERMS>", "'OFFLINE'")\
        .replace("<REFRESH_SCHEDULE>", "\n      refresh_schedule: '1440 MINUTE'")\
        .replace("<REFRESH_TYPE>", "'FULL_DATABASE'")\
        .replace("<TARGET_ACCOUNTS>", target_accounts)
        
    return manifest


#Helper Functions
def execute_command(cmd, sf_con):
    cursor = sf_con.raw_connection.execute_string(cmd)[0]
    columns = [x.name for x in cursor.description]
    res = cursor.fetchall()
    return pd.DataFrame(res, columns=columns)

#display connection info in sidebar
def display_sidebar(st, sf_con):
    with st.sidebar: 
        st.subheader("Connection Info:")
        st.write("Account: %s" %sf_con.raw_connection.account)
        st.write("User: %s" %sf_con.raw_connection.user)
        st.write("Role: %s" %sf_con.raw_connection.role)
        st.write("Warehouse: %s" %sf_con.raw_connection.warehouse)
        st.write("Database: %s" %sf_con.raw_connection.database)
        st.write("Schema: %s" %sf_con.raw_connection.schema)

def log(st, msg="", level="INFO"): 
    st.session_state.log = st.session_state.log + \
        "%s[%s]: %s \n" %(datetime.now().strftime('%Y/%m/%d %H:%M:%s'),level,msg)
    
def reset_log(st): 
    st.session_state.log = "Welcome to the Snowflake Resharing App!"