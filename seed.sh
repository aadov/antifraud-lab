#!/bin/sh

echo "Waiting for web..."
until curl -s http://web:8000/ > /dev/null 2>&1; do
  echo "Web not ready, retrying..."
  sleep 2
done
echo "Web is ready. Starting seeder."

send() {
  curl -s -X POST http://web:8000/login \
    -H "Content-Type: application/json" \
    -d "{
      \"user_id\":\"$1\",
      \"ip\":\"$2\",
      \"country\":\"$3\",
      \"device\":\"$4\",
      \"hour\":$5,
      \"failed_attempts\":$6
    }" > /dev/null
}

while true; do

  for i in $(seq 1 5); do
    send "attacker_1" "185.22.10.11" "RU" "new" 3 5
    sleep 1
  done

  send "client_001" "91.10.20.5" "KZ" "known" 14 0
  send "client_001" "45.33.10.9" "US" "new" 2 3
  send "client_001" "78.11.20.1" "CN" "new" 4 4

  for i in $(seq 1 3); do
    send "client_00$i" "10.10.10.$i" "KZ" "known" 12 0
    sleep 2
  done

  sleep 5

done
