create_share_token = "CALL SYSTEM$GENERATE_CROSS_REGION_GROUP_SHARING_TOKEN('<PROVIDER_TYPE>');"

use_orgadmin = "USE ROLE ORGADMIN;"

use_role = "USE ROLE <ROLE>;"

create_email_integration= """
CREATE NOTIFICATION INTEGRATION if not exists vps_sharing_app_email_notification
  TYPE=EMAIL
  ENABLED=TRUE;
"""

send_email = """
CALL SYSTEM$SEND_EMAIL('vps_sharing_app_email_notification','<EMAIL>', 'Request to share data to VPS account from <CLIENT_NAME>','The client <CLIENT_NAME> wishes to share data with the VPS account team. If you wish to accept data, you will need to enable sharing into your Snowflake account. To enable sharing with this account, have someone with orgadmin permissions execute the following command in your Snowflake VPS account: \\n\\n `select system$allow_provider_org_sharing_into_vps(\\'<TOKEN>\\', \\'DRY_RUN\\');` \\n\\n If the command returns the expected provider name, then you can proceed to execute the following: \\n\\n`select system$allow_provider_org_sharing_into_vps(\\'<TOKEN>\\');`. \\n\\n Please contact Snowflake support if you have any questions. Thank You!');
"""

current_org = "SELECT CURRENT_ORGANIZATION_NAME();"

show_databases = "SHOW DATABASES;"

show_objects = "show objects in database <DB_NAME>;"

create_share = "create share if not exists <SHARE_NAME> secure_objects_only=<SECURE_OBJECTS_ONLY>;"

grant_to_share = "grant <OPERATION> on <OBJECT_TYPE> <OBJECT_NAME> to share <SHARE_NAME>;"

listing_manfiest = """  title: <LISTING_TITLE> 
  subtitle: <LISTING_SUBTITLE>
  description: <LISTING_DESCRIPTION>
  listing_terms: 
      type: <LISTING_TERMS>
  auto_fulfillment: 
      refresh_type: <REFRESH_TYPE> <REFRESH_SCHEDULE>
  targets: 
      accounts: [<TARGET_ACCOUNTS>]"""

create_listing = """ 
create external listing if not exists <LISTING_NAME> 
<SHARE_TYPE> <SHARE_NAME> AS
$$
<LISTING_MANIFEST> 
$$ PUBLISH=<PUBLISH> REVIEW=<REVIEW>
"""

publish_listing = "ALTER LISTING <LISTING_NAME> PUBLISH;"