#!/bin/bash
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
cd $SCRIPT_DIR

# APEX Forward
sudo dnf module reset nginx -y
sudo dnf module enable nginx:1.22 -y
# sudo yum remove nginx-mod*
# sudo yum install nginx-mod-*

# ORACLE Instant Client 
if [[ "$JDBC_URL" == *"jdbc:oracle"* ]]; then
    if [[ `arch` == "aarch64" ]]; then
        sudo dnf install -y oracle-release-el8
        sudo dnf install -y oracle-instantclient19.19-basic oracle-instantclient19.19-devel
    else
        export INSTANT_VERSION=23.4.0.24.05-1
        wget https://download.oracle.com/otn_software/linux/instantclient/2340000/oracle-instantclient-basic-${INSTANT_VERSION}.el8.x86_64.rpm
        wget https://download.oracle.com/otn_software/linux/instantclient/2340000/oracle-instantclient-sqlplus-${INSTANT_VERSION}.el8.x86_64.rpm
        sudo dnf install -y oracle-instantclient-basic-23.4.0.24.05-1.el8.x86_64.rpm oracle-instantclient-sqlplus-${INSTANT_VERSION}.el8.x86_64.rpm
        mv *.rpm /tmp
    fi
fi

# Python Server
sudo dnf -y install git gcc-c++
sudo dnf install -y python3.11 python3.11-pip python3-devel
sudo pip3.11 install pip --upgrade

# Install virtual env myenv
python3.11 -m venv myenv
source myenv/bin/activate
pip3 install --upgrade pip
pip3 install -r requirements.txt

# Store the db_connection in the start.sh

# Get COMPARTMENT_OCID
curl -s -H "Authorization: Bearer Oracle" -L http://169.254.169.254/opc/v2/instance/ > /tmp/instance.json
export TF_VAR_compartment_ocid=`cat /tmp/instance.json | jq -r .compartmentId`
export TF_VAR_region=`cat /tmp/instance.json | jq -r .canonicalRegionName`

# TNS_NAMES.ORA
cat > tnsnames.ora <<EOT
DB  = $DB_URL
EOT

# Change the env.sh
CONFIG_FILE=config.py
sed -i "s/##DB_USER##/apex_app/" $CONFIG_FILE
sed -i "s/##DB_PASSWORD##/$DB_PASSWORD/" $CONFIG_FILE
sed -i "s/##DB_URL##/DB/" $CONFIG_FILE
sed -i "s/##NAMESPACE##/$TF_VAR_namespace/" $CONFIG_FILE
sed -i "s/##PREFIX##/$TF_VAR_prefix/" $CONFIG_FILE
sed -i "s/##REGION##/$TF_VAR_region/" $CONFIG_FILE

# Optional
sed -i "s/##STREAM_OCID##/$STREAM_OCID/" $CONFIG_FILE
sed -i "s/##FN_OCID##/$FN_OCID/" $CONFIG_FILE

## Contain "/"
sed -i "s!##STREAM_MESSAGE_ENDPOINT##!$STREAM_MESSAGE_ENDPOINT!" $CONFIG_FILE
sed -i "s!##FN_INVOKE_ENDPOINT##!$FN_INVOKE_ENDPOINT!" $CONFIG_FILE

# Create services
create_service () {
    APP_DIR=$1
    COMMAND=$2
    # Create an db service
    cat > /tmp/$COMMAND.service << EOT
[Unit]
Description=$COMMAND
After=network.target

[Service]
Type=simple
ExecStart=/home/opc/$APP_DIR/${COMMAND}.sh
TimeoutStartSec=0
User=opc

[Install]
WantedBy=default.target
EOT
    sudo cp /tmp/$COMMAND.service /etc/systemd/system
    sudo chmod 664 /etc/systemd/system/$COMMAND.service
    sudo systemctl daemon-reload
    sudo systemctl enable $COMMAND.service
    sudo systemctl restart $COMMAND.service
}

create_service app cohere
