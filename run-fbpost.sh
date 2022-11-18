#!/usr/bin/env sh

#  Used by fbpost.service to start the web service 

cd $HOME/src/fbpost
source bin/activate
gunicorn --bind=192.168.1.20:8081 fbpost:app &
