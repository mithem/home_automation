FROM nginx:alpine

RUN mkdir /usr/home_automation_frontend
COPY . /usr/home_automation_frontend
WORKDIR /usr/home_automation_frontend

RUN apk add nodejs yarn
RUN yarn
RUN yarn build

RUN mkdir -p /var/www/html
RUN cp -r build/* /var/www/html/
COPY nginx.conf.template /etc/nginx/nginx.conf.template

CMD ["/bin/sh", "-c", "envsubst < /etc/nginx/nginx.conf.template > /etc/nginx/nginx.conf && envsubst < src/constants.ts.template > src/constants.ts &&  nginx -g 'daemon off;'"]
