# LeagueDumpling
Raspberry Pi-based smart lamp that changes colour depending on the win/loss ratio of a League of Legends account

Python Dependencies:
requests, colour, RPI.GPIO, adafruit_blinka, rpi_ws281x, adafruit-cicuitpython-neopixel

Required Config:
You'll need to change the "apiKey" value in the config file to a valid Riot API key
Change the "summoner" value in the config file to match the account you want to track

Optional Config:
You can adjust the API endpoints in the config file if they change
You can configure the day/night brightness settings by changing the appropriate values in the config file

