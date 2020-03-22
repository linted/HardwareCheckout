#!/usr/bin/env bash

export FLASK_APP=HardwareCheckout.main

generate_key() {
    echo "[*] Generating keys"
    export KEY=$(head -10 /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 32 | sort -r | head -n 1)
    echo $KEY > db.key
    chmod 600 db.key
}

generate_db() {
    echo "[*] Generating database"
    python3 ./setup.py
}

if [ ! -f db.key ]; then
    read -p "[?] db.key not found. Create new database? [y/N] " -n 1 confirm
    echo
    if [[ $confirm =~ ^[Yy]$ ]]; then
        rm -f HardwareCheckout/db.sqlite
        generate_key
        generate_db
    else
        echo "[!] Abort"
        exit
    fi
else
    export KEY=$(cat db.key)
fi

if [ ! -f HardwareCheckout/db.sqlite ]; then
    read -p "[?] Database not found. Create new database? [y/N] " -n 1 confirm
    echo
    if [[ $confirm =~ ^[Yy]$ ]]; then
        generate_db
    else
        echo "[!] Abort"
        exit
    fi
fi

flask run
