app=cf_ddns
docker stop $app
docker rm $app
docker image rm $app
docker build -t $app .
docker-compose up -d $app
docker-compose start $app
docker logs $app -f
