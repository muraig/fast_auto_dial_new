echo "
grep -E '^\s\s\w+:\$' docker-compose.yml
# docker-compose up -d --build db pgadmin
docker-compose up -d --build redis rabbitmq postgres pgadmin
docker-compose stop redis rabbitmq postgres pgadmin
"
