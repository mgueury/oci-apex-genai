#!/bin/bash
PROJECT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
export BIN_DIR=$PROJECT_DIR/bin

# Env Variables
export TF_VAR_prefix="apexgenai"

export TF_VAR_ui_type="html"
export TF_VAR_db_type="autonomous"
export TF_VAR_license_model="LICENSE_INCLUDED"
export TF_VAR_oke_type="managed"
export TF_VAR_deploy_type="compute"
export TF_VAR_language="apex"
export TF_VAR_db_install="shared_compute"
export TF_VAR_db_user="admin"

# export TF_VAR_compartment_ocid=ocid1.compartment.xxxxx
# TF_VAR_db_password : Min length 12 characters, 2 lowercase, 2 uppercase, 2 numbers, 2 special characters. Ex: LiveLab__12345
#   If not filled, it will be generated randomly during the first build.
export TF_VAR_db_password="__TO_FILL__"

if [ -f $PROJECT_DIR/../group_common_env.sh ]; then
  . $PROJECT_DIR/../group_common_env.sh
elif [ -f $PROJECT_DIR/../../group_common_env.sh ]; then
  . $PROJECT_DIR/../../group_common_env.sh
elif [ -f $HOME/.oci_starter_profile ]; then
  . $HOME/.oci_starter_profile
fi

# Creation Details
export OCI_STARTER_CREATION_DATE=2024-07-25-18-51-24-078742
export OCI_STARTER_VERSION=2.0
export OCI_STARTER_PARAMS="prefix,java_framework,java_vm,java_version,ui_type,db_type,license_model,mode,infra_as_code,db_password,oke_type,deploy_type,language,db_install"

# Get other env variables automatically (-silent flag can be passed)
. $BIN_DIR/auto_env.sh $1
