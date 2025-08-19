# KnoWMATA

How well do you know WMATA? Try racing through the city using transit without maps, and see what you get! 

In order to use this app, **please run it yourself**. Nest is not giving my app SSL certs so its not usable other than a preview if i use GH pages :pf:

# Run it yourself

This assumes you have already cloned the repo and cded into the folder. First start by running main.py locally (python3 main.py) after cding into backend. If it errors, please check if you have dependencies missing. Next, check docs/game.html and docs/index.html at lines 44 and 27 respectively and change the links (line 44 in game.html should become 127.0.0.1 or whereever your backend server is hosted at, line 27 should become where your frontend stuff (docs/*) is hosted)
I personally use ths VSC live preview extension to develop/run locally. If something else works, you can also use that! :D
