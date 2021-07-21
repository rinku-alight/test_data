FROM python:3.9.2
LABEL maintainer="Clayton Corrello (clayton.corrello@alight.com)"

RUN export http_proxy=http://proxyuser:proxypass@proxycachest.hewitt.com:3228 && \
    export https_proxy=http://proxyuser:proxypass@proxycachest.hewitt.com:3228

RUN apt-get -y update

RUN apt-get -y upgrade && \
    apt-get clean

COPY requirements.txt ./
RUN pip install --proxy http://proxyuser:proxypass@proxycachest.hewitt.com:3228 --no-cache-dir --upgrade pip
RUN pip install --proxy http://proxyuser:proxypass@proxycachest.hewitt.com:3228 --no-cache-dir -r requirements.txt

RUN apt-get -y install bash

# switch to non-root user
RUN useradd --create-home appuser
WORKDIR /home/appuser

# initializatiion as root
COPY setup.sh /home/appuser/setup.sh
RUN chmod +x /home/appuser/setup.sh
COPY run.sh /home/appuser/run.sh
RUN chmod +x /home/appuser/run.sh
COPY run.sh /home/appuser/test.sh
RUN chmod +x /home/appuser/test.sh

# switch user
USER appuser
RUN /home/appuser/setup.sh

# copy python scripts
COPY *.py /home/appuser/


ENTRYPOINT [ "bash" ]

