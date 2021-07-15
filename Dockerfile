FROM python:3.7

COPY requirements.txt /opt/app/requirements.txt

WORKDIR /opt/app/

# Add credentials on build
RUN mkdir /root/.ssh/
ARG SSH_PRIVATE_KEY
RUN echo "${SSH_PRIVATE_KEY}" > /root/.ssh/id_rsa && chmod 600 /root/.ssh/id_rsa

# Make sure your domain is accepted
RUN touch /root/.ssh/known_hosts
ARG SSH_KNOWN_HOST
RUN ssh-keyscan ${SSH_KNOWN_HOST} >> /root/.ssh/known_hosts

ARG REPO_URL_CC_MODELS
ARG VERSION_CC_MODELS
RUN git clone --branch ${VERSION_CC_MODELS} ${REPO_URL_CC_MODELS} /opt/campus-shared-models/

ARG REPO_URL_CC_LIBS
ARG VERSION_CC_LIBS
RUN git clone --branch ${VERSION_CC_LIBS} ${REPO_URL_CC_LIBS} /opt/campus-libs/

RUN pip install -r requirements.txt

COPY . /opt/app

CMD ["sh", "-c", "python app.py --importer-id $importer_id"]