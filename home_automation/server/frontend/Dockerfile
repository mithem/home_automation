FROM nginx:alpine

RUN mkdir /usr/home_automation_frontend
COPY . /usr/home_automation_frontend
WORKDIR /usr/home_automation_frontend

ARG home_automation_version="N/A (missing `home_automation_version` build arg when building image)"
ARG heimdall_url

ENV HOME_AUTOMATION_VERSION=$home_automation_version
ENV HEIMDALL_URL=$heimdall_url
RUN envsubst < src/constants.ts.template > src/constants.ts

RUN apk add nodejs yarn
RUN yarn
RUN yarn build

RUN mkdir -p /var/www/html
RUN cp -r build/* /var/www/html/
COPY nginx.conf.template /etc/nginx/nginx.conf.template

CMD ["/bin/sh", "-c",  "envsubst < /etc/nginx/nginx.conf.template > /etc/nginx/nginx.conf && nginx -g 'daemon off;'"]
