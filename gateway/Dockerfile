FROM nginx:alpine

RUN rm /etc/nginx/conf.d/default.conf

COPY ./gateway/nginx.conf /etc/nginx/conf.d/default.conf

COPY ./frontend /usr/share/nginx/html

EXPOSE 80
