#!/bin/bash
cd ~/music-quiz-bot/
pipenv shell
pipenv install
cd bot
python3 app.py