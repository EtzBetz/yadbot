FROM python

WORKDIR /usr/src/app
COPY . .
RUN pip install discord.py bs4 lxml
RUN python -V
CMD [ "python", "main.py" ]