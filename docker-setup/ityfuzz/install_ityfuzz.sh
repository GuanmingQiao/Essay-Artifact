#!/bin/bash

curl -L https://ity.fuzz.land/ | bash
export PATH="$PATH:/home/test/.ityfuzz/bin"
sudo apt-get install openssl
ityfuzzup
