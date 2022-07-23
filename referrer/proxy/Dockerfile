FROM nginx:1.21.6-alpine
COPY conf-templates/nginx.conf /etc/nginx/templates/nginx.conf.template
ENV NGINX_ENVSUBST_OUTPUT_DIR=/etc/nginx
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
