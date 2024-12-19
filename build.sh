#!/bin/bash
sudo docker build -t smartian-artifact -f Dockerfile .
sudo docker build -t ityfuzz-artifact -f Dockerfile_Ityfuzz .