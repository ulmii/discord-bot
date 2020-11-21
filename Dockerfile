FROM python:3.8-slim-buster

RUN pip3 install --upgrade pip

RUN pip3 install \
    discord.py \
    python-dotenv

ENTRYPOINT ["python3", "bot.py"]