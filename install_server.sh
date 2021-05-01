#!/bin/bash

#@author: dtechshield 
#@author: linted

which dpkg
if [ $? -eq 1 ]; then
  echo "ERROR! Couldn't find dpkg! Is this a debian based system?"
  exit 1
fi 

# check to see the type of db they want
standalone="q"
while [ 1 ]; do
  echo "postgresql is not recomended for use with CTFd"
  read -p "Install and setup postgresql? (y/n) " -n1 $standalone
  echo # to get a new line since read doesn't give us one
  standalone=$(echo "$standalone" | awk '{print tolower($0)}')
  if [ $standalone = 'y' ] && [ $standalone = 'n' ]; then
    break
  fi
done

#This assumes all is installed under /opt/HardwareCheckout
GIT_PATH="$( cd "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"
APP_PATH=/opt/HardwareCheckout
COOKIEKEY=cookie.key
DBNAME=chvapp
DBUNAME=chvapp

echo "Run this once and you should be set... Make sure to run it as root!"
echo "Installing required system packages...(if needed)"

if sudo dpkg -l | sudo grep python3-pip 2>&1 > /dev/null; then
	echo "pip3 exists..."
else
	echo "pip3 does not exist; installing..."
	sudo apt-get -qq -y update
	sudo apt-get -qq -y install python3-pip
fi


if [ $standalone = 'y' ]; then
  DBPASS=$(head -10 /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 32 | sort -r | head -n 1)
  if sudo dpkg -l | sudo grep postgresql 2>&1 > /dev/null; then
    echo "postpgres exists..."
  else
    echo "postgres does not exist; installing..."
    sudo apt-get -qq -y update
    sudo apt-get -qq -y install postgresql postgresql-contrib postgresql-server-dev-all
    sudo service start postgresql
  fi

  echo "Configuring the database..."
  sudo -u postgres -s psql -c "SELECT datname FROM pg_catalog.pg_database WHERE datname='$DBNAME'" | grep -wq $DBNAME
  DB_EXISTS=$?

  if [[ "$DB_EXISTS" -eq 0 ]]; then
      echo "$DBNAME exists.. Leaving it as it is... If you want a fresh DB drop it manually and try again..."
      while true; do
      read -p "Do you want me to continue? (Y/n)?" yn
      case $yn in
          [Yy]* ) break;;
          [Nn]* ) exit;;
          * ) echo "Please answer yes or no.";;
      esac
    done

  else

    #Create Postgresql Pre-reqs
    sudo -u postgres -s <<EOF
psql -c "CREATE USER $DBUNAME WITH PASSWORD '$DBPASS' CREATEDB;"
createdb -O$DBUNAME -Eutf8 $DBNAME
echo "Postgres user '$DBUNAME' and database '$DBNAME' created."
EOF

  fi
  echo "Creating web server user $DBUNAME"
  sudo useradd -m $DBUNAME -s /bin/bash

  DBConnectionString="postgresql+psycopg2://$DBUNAME:$DBPASS@127.0.0.1:5432/$DBNAME"
  CTFdConnectionString="'DO_NOT_USE'"
else
  echo "NOTE: you will need to configure your connection string after this script, then run ./setup.py!"
  DBConnectionString='mysql+pymysql://'
  CTFdConnectionString="'mysql+pymysql://'"
fi



clone_repo() {
	sudo mkdir -p $APP_PATH
	#sudo chown $DBUNAME:$DBUNAME $APP_PATH
	sudo git clone $GIT_PATH $APP_PATH
}

if [ ! -d "$APP_PATH" ]; then
   echo "$APP_PATH does not exist - creating clone of git repo..."
   clone_repo
else
  while true; do
    read -p "$APP_PATH exists - do you want me to make a clean copy? (Y/n)?" yn
    case $yn in
        [Yy]* ) sudo rm -rf $APP_PATH;clone_repo; break;;
        [Nn]* ) break;;
        * ) echo "Please answer yes or no.";;
    esac
  done
    
fi

#Configure Application
echo "Writting application config '$APP_PATH'/HardwareCheckout/config.py - please configure your SSL certificate information if you want to run HTTPS"
sudo bash -c "cat << EOF > '$APP_PATH'/HardwareCheckout/config.py
#!/usr/bin/env python3
db_path = '$DBConnectionString'
db_ssl = {
  'ssl': 
    {
      'ca': ''
    }
  }
ctfd_db_path=$CTFdConnectionString
ssl_config = {
  'certfile':'',
  'keyfile':''
  }
EOF"

TDSK=$(head -10 /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 32 | sort -r | head -n 1)


sudo bash -c "echo $TDSK >> $APP_PATH/$COOKIEKEY"


#Generate run.sh for local runs
sudo bash -c "cat << EOF > '$APP_PATH'/run.sh
export TORNADO_SECRET_KEY=$TDSK
source $APP_PATH/venv/bin/activate
python3 -m HardwareCheckout --logging=info
EOF"

sudo chown -R $DBUNAME:$DBUNAME $APP_PATH
sudo -u $DBUNAME chmod a+x $APP_PATH/run.sh
sudo chmod 640 $APP_PATH/$COOKIEKEY


echo "Installing required application packages...(if needed)"

sudo pip3 install virtualenv

pushd $APP_PATH


sudo -u $DBUNAME -s <<EOF

if [ ! -d "$APP_PATH/venv" ]; then
  python3 -m virtualenv $APP_PATH/venv
fi

source $APP_PATH/venv/bin/activate
$APP_PATH/venv/bin/pip3 install -r $APP_PATH/requirements.txt
$APP_PATH/venv/bin/python3 $APP_PATH/setup.py -c
deactivate
EOF


echo ""
echo "Creating HardwareCheckout Service - to start or stop the service:"
echo "systemctl start|stop HardwareCheckout"
echo ""
sudo bash -c  "cat << EOF > /etc/systemd/system/HardwareCheckout.service
[Unit]
Description=Hardware Checkout Service
After=network.target

[Service]
User=$DBUNAME
Restart=on-failure
Environment=TORNADO_SECRET_KEY=$TDSK
WorkingDirectory=$APP_PATH
ExecStart=$APP_PATH/venv/bin/python3 -m HardwareCheckout
CapabilityBoundingSet=CAP_NET_BIND_SERVICE
AmbientCapabilities=CAP_NET_BIND_SERVICE

[Install]
WantedBy=multi-user.target
EOF"

echo "Enabling Service..."
sudo systemctl enable HardwareCheckout 
sudo systemctl daemon-reload
echo "Starting HardwareCheckout..."
sudo systemctl start HardwareCheckout 


echo ""
echo "Service running on http://127.0.0.1:8080"
echo "If you configure certfile and keyfile variables in $APP_PATH/HardwareCheckout/config.py server will run on https://127.0.0.1"
echo "Configure your firewall or your load balancer accordingly..."
echo ""
echo "Before you can get started make sure:"
echo "1. Create an admin account" 
echo "2. Create device types for queues"
echo "3. Process the device generated .ini files and provision devices"
echo "Core Install Done..."