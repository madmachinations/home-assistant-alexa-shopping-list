# Alexa Shopping List to Home Assistant Synchroniser

<a href="https://buymeacoffee.com/madmachinations" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/default-orange.png" alt="Buy Me A Coffee" height="41" width="174"></a>

This is a custom component for Home Assistant, which allows you to synchronise your Alexa Shopping List with the Home Assistant shopping list.

**This works even though they cut off third party access to the shopping lists in Summer 2024**

It is made of two main parts:

- **The Server** - This is a small Selenium based application, which accesses your shopping list on the Amazon Website.
- **The Component** - This is the part you add to your Home Assistant installation. It connects to the server to periodically sync the shopping lists in both places

## HASS OS

Generally this should run on most setups. However, I'm not sure about HASS OS.

Running this requires you are able to setup the server-side of this solution in some capacity. HASS OS is a purely containerised environment, and is technically capable of running third party containers. However this is generally discouraged apparantly.

You need to look into the documentation for HASS OS to configure your environment to run additional containers, if you want to keep using HASS OS and run this component.


## Step 1 -  Installing the server

The server runs as a headless background service.

The server runs on TCP port 4000. This does NOT need to be accessible to the outside world, but does need to be accessible to your local network in some form. If you have very restrictive rules setup on your rig, you might need to open this up. But most should be fine.

Once the server is installed and running in some form, you are ready to move onto the next step.

There are a few different ways to install the server:

### Pre-built container

You can find pre-built containers on docker hub here:

https://hub.docker.com/r/madmachinations/ha-alexa-shopping-list-sync

These have been built for x86_64 and arm64 environments, so should run fine on most rigs.

However I'm not sure about older raspberry pi's and such.

The container generally doesn't use much system resources, it peaks when it's using the sync, as this is when the headless browser is being loaded and used. But when it is not synchronising, it just idles waiting for a signal to do something.

### Build your own container image

1) Download this repository
2) `cd` into the `server` directory
3) Run your `docker build ...` command

### Non-containerised with systemd

You can run the server manually as a service within systemd.

First, download this repository and mv the `server` directory to wherever you want it to be installed within your file system.

Next, your system needs to have the following packages installed:

- chromium
- chromium-chromedriver
- python3
- pip3

Now let's install the python packages that are required:

- `cd /wherever/you/installed/the/server/`
- `sudo pip3 install -r requirements.txt`

Next, we need to setup a systemd service file:

To do this, create a new file called `alexa-shopping-list.service` within your `/etc/systemd/service/` directory, which contains the following:

```
[Unit]
Description=Alexa Shopping List
After=network.target

[Service]
ExecStart=/usr/bin/python3 /path/to/server/server.py

# If the script crashes, restart it automatically
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

After this file is saved, now run these commands:

- `sudo systemctl daemon-reload`
- `sudo systemctl enable alexa-shopping-list`
- `sudo systemctl start alexa-shopping-list`

You can check if it is running with `sudo systemctl status alexa-shopping-list`

## Step 2 - Configure the server

Before the server can do anything, it needs to be configured.

You can do this with the client script in this repository.

So, if you have not done so already, download this repository first.

Before we begin, you need to make sure your system has both `python3` and `pip3` installed.

If that is the case, `cd` into the `client` directory

If this is the first time using the client, install it's dependencies with something like:

`pip3 install --user -r requirements.txt`

Now we are ready to run the client and configure out server.

The client is opened like this:

`python3 client.py <IP_ADDRESS_OF_SERVER>`

So, let's assume the system you have installed the server onto has the IP address `192.168.0.200`; You would start the client like this:

`python3 client.py 192.168.0.200`

When the client starts it immediately tries to connect to the server. If it can connect, it checks to see if the server is configured.

If the server is _not_ yet configured, the configuration process will start:

1) The first thing it will ask, is what domain name do you access the amazon website through. The default value is `amazon.co.uk`, because I'm British, so... it is what it is. This has only been tested on amazon.co.uk so far.
2) Next it will check if the server is logged into your account on the amazon website, which it won't be. So it will immediately ask you to enter the email address and password you login to Amazon with.
3) If your account has MFA enabled, after a few moments it should ask you to enter your MFA code.
4) Assuming all of this went to plan, the server should now be authenticated with your account on the Amazon website.
5) You will now find yourself on the client command line, you can just type `quit` and press enter to close it, or press `ctrl + c`. If you have things on your alexa shopping list already, you can check if you can see them by typing `list` and pressing enter. After 5-10 seconds you should see your shopping list in the terminal.

As far as Amazon is concerned, this is you opened the website in chromium and using your account to use the shopping list.

Your actual login credentials, your email and password, are NOT stored anywhere. They are used to perform the login, and they are forgotten immediately after this.

Instead, all the cookies and values in the web browser session once logged in are saved by the server, and reloaded each time it has to do something.

If it is synchronising regularly, this session should just stay alive.

You should also be able to see it on your Amazon account as a place you are logged in.

I will list all the client commands in a different section below.


## Step 3 - Install the custom component

Now we're ready to add the custom component to Home Assistant.

This component connects to the server and uses it to keep your HA shopping list synchronised.

1) In your HA config directory, make sure there is a folder called `custom_components`. Create it if it does not exist.
2) Copy the `alexa_shopping_list` folder out of _this_ repository's `custom_components` folder and paste it into _your HA's_ `custom_components` folder.
3) Restart Home Assistant and wait for it to reload
4) In HA, go to Settings > Devices & Integrations and press Add integration. Find `Alexa Shopping List` and click on that to start the configuration process
5) The first config screen will ask you to enter the IP address and port number of the server we installed earlier. Enter your IP address, and the default portis 4000. Press next and the component will check if it can connect.
6) Once a successful connection is established to the server, it will ask you how frequently you want to synchronise the shopping list in minutes. I am running mine every 60 minutes. There is also a server which you can call at any time to force it to synchronise now. Choose a figure that is reasonable, don't spam it.
7) That's it! After a few moments, your HA shopping list should be replaced with whatever is on your alexa shopping list.


## Using the shopping list

This component expects you primarily access your shopping list via Home Assistant directly.

Each time it sychronises, it adds everything to your HA list which exists on your alexa list but not on your HA list.

If an item is ticked-off as "completed" on your HA list, it will be removed from your Alexa list.

If you added anything manually to your HA list, it will be added to your alexa list.

Generally I add most things to my alexa list via an echo device and voice commands, and then I just want to read the shopping list in my HA app when I'm actually going shopping.

## Client commands

| Command | Description | Example |
| --- | --- | --- |
| `quit` or `exit` | Close the client | N/A |
| `list` | Lists all items on your Alexa list | N/A |
| `add {item}` | Adds an item to your Alexa list | `add cake` |
| `update {old} {new}` | Updates an item on you Alexa list | `update cake "baked beans"` |
 `remove {item}` | Removes an item from your Alexa list | `remove "baked beans"` |


## Help and feedback

I would also appreciate any help from anyone for testing and further development on various fixes and improvements.

It was a fight to get the damn thing to work reliably, and I don't doubt it will require maintenance in the future.

If you like this thing and it works for you, and you have the means, then please consider buying me a coffee. Which if I'm honest I will definitely spend on beer and pizza. But sure let's call that "coffee".

<a href="https://buymeacoffee.com/madmachinations" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/default-orange.png" alt="Buy Me A Coffee" height="41" width="174"></a>
