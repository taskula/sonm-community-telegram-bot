FROM python:3

WORKDIR /usr/src/app
COPY . .
RUN pip install python-telegram-bot seaborn pandas numpy scipy
RUN chmod +x init.sh
ENTRYPOINT ["./init.sh"]
