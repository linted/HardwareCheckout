#!/usr/bin/env bash

export FLASK_APP=HardwareCheckout.main
DBKEY=cookie.key
SQLITEPATH=/opt/database
SQLITEDB=$SQLITEPATH/db.sqlite

generate_key() {
    echo "[*] Generating keys"
    export TORNADO_SECRET_KEY=$(head -10 /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 32 | sort -r | head -n 1)
    echo $TORNADO_SECRET_KEY > $DBKEY
    chown root:www-data $DBKEY
    chmod 640 ./$DBKEY

}

generate_db() {
    echo "[*] Generating database"
    if [ ! -d "$SQLITEPATH" ]; then
       mkdir $SQLITEPATH
    fi
    python3 ./setup.py -c
}

if [ ! -f $DBKEY ]; then
    read -p "[?] db.key not found. Create new database? [y/N] " -n 1 confirm
    echo
    if [[ $confirm =~ ^[Yy]$ ]]; then
        generate_key
        generate_db
    else
        echo "[!] Abort"
        exit
    fi
else
    export export TORNADO_SECRET_KEY=$(cat $DBKEY)
fi

if [ ! -f $SQLITEDB ]; then
    read -p "[?] Database not found. Create new database? [y/N] " -n 1 confirm
    echo
    if [[ $confirm =~ ^[Yy]$ ]]; then
        generate_db
        chown root:www-data $SQLITEPATH
        chmod 775 $SQLITEPATH
        chown root:www-data $SQLITEDB
        chmod 660 $SQLITEDB
    else
        echo "[!] Abort"
        exit
    fi
fi

python3 -m HardwareCheckout
