FROM nginx:1.21.4

LABEL maintainer="Julien CLEMENT <julien.clement@epita.fr>"

EXPOSE 80

COPY html /usr/share/nginx/html
