pip3 install tox
touch .env
echo "EMAIL_ADDRESS=test@example.com\
    EMAIL_PADDWD=pass0rd1!\
    HASS_TOKEN=abcdefg\
    HASS_BASE_URL=http://homeassistant.local:8123\
    THINGS_SERVER_URL=http://192.168.10.2:8001\
    LOG_DIR=." | tee -a .env
