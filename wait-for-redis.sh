#!/bin/sh

HOST=$1
PORT=$2

echo "Start waiting for Redis fully start. Host '$HOST', '$PORT'..."
echo "Try ping Redis... "
PONG=`redis-cli -h $HOST -p $PORT -c ping| grep PONG`
while [ -z "$PONG" ]; do
    sleep 10
    echo "Retry Redis ping... "
    PONG=`redis-cli -h $HOST -p $PORT -c ping| grep PONG`
done
echo "Redis at host '$HOST', port '$PORT' fully started."
