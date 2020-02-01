FROM python

WORKDIR /usr/src/app
COPY . .
RUN pip install discord.py bs4 lxml
RUN python -V
RUN python main.py