#!/bin/bash

SOCK=$(echo $1 | sed -n 's,.*\(device[0-9]\).*,\1,p')
SOCK=/tmp/devices/$SOCK/$SOCK.sock

tmate -S $SOCK display -p "#{tmate_ssh}"
tmate -S $SOCK display -p "#{tmate_web}"
tmate -S $SOCK display -p "#{tmate_web_ro}"

