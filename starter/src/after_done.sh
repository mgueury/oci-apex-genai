# Upload to Object storage
oci os object put -bn ${TF_VAR_prefix}-public-bucket -ns $TF_VAR_namespace --file src/app/src/data/expensepolicy.pdf --content-type application/pdf --no-overwrite                                                                                                       
oci os object put -bn ${TF_VAR_prefix}-public-bucket -ns $TF_VAR_namespace --file src/app/src/data/human_policy.txt --content-type text/html --no-overwrite
oci os object rename -bn ${TF_VAR_prefix}-public-bucket -ns $TF_VAR_namespace --source-name expensepolicy.pdf --new-name data/expensepolicy.pdf  
oci os object rename -bn ${TF_VAR_prefix}-public-bucket -ns $TF_VAR_namespace --source-name human_policy.txt --new-name data/human_policy.txt

# Info
echo "-----------------------------------------------------------------------"
echo "APEX login:"
echo
echo "APEX Workspace"
echo "$UI_URL/ords/_/landing"
echo "  Workspace: APEX_APP"
echo "  User: APEX_APP"
echo "  Password: $TF_VAR_db_password"
echo
echo "APEX APP"
echo "$UI_URL/ords/r/apex_app/apex_app/"
echo "  User: APEX_APP / $TF_VAR_db_password"
