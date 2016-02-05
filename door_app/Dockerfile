FROM stuartmarsden/docker-twisted
MAINTAINER Embedded CTF ectf@mitre.org

RUN apt-get update

VOLUME /src/pythonlistener/data

COPY server.py /src/pythonlistener/

EXPOSE 9500

CMD ["python", "/src/pythonlistener/server.py"]
