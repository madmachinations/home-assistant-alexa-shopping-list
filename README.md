# Alexa Shopping List to Home Assistant Synchroniser

<a href="https://buymeacoffee.com/madmachinations" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/default-orange.png" alt="Buy Me A Coffee" height="41" width="174"></a>

This is a custom component for Home Assistant, which allows you to synchronise your Alexa Shopping List with the Home Assistant shopping list.

**This works even though they cut off third party access to the shopping lists in Summer 2024**

There are three parts:

**The Server**

This is a small Selenium-based python application, which accesses your alexa shopping list via the Amazon Website. It can read what is on the list, add things to it and remove things from it.

Selenium allows you to essentially remote control a web browser and can browse websites, read content, click buttons, etc.

The server runs on your home assistant device, or a different server on your network.

**The Client**

In theory, you should rarely need to use the client. You need it to get the server set up. The client is like the remote control for the server.

The client runs on your desktop computer or laptop, so you can talk to the server more easily.

**The Custom Component**

This is the part you add to your Home Assistant installation. It talks with the server and the two work together to make sure your shopping lists on both HA and Alexa are kept in sync.


## Installation steps

You can find the installation guide on the wiki here:

https://github.com/madmachinations/home-assistant-alexa-shopping-list/wiki/Installation

## Setting up a development environment

You can find the development environment setup guide on the wiki here:

https://github.com/madmachinations/home-assistant-alexa-shopping-list/wiki/Development-environment

## Troubleshooting and help

If you get stuck or hit a problem, please read the troubleshooting steps first:

https://github.com/madmachinations/home-assistant-alexa-shopping-list/wiki/Troubleshooting-and-help


## Help out

I would appreciate any help from anyone for testing and further development on various fixes and improvements.

If you are not technical, there are other ways to help. Such as identifying duplicate issues, or helping other people in the community support discussion board here:

https://github.com/madmachinations/home-assistant-alexa-shopping-list/discussions/categories/community-support

If you like this thing and you have the means, then please consider buying me a coffee. Which if I'm honest I will definitely spend on beer and pizza. But sure let's call that "coffee".

<a href="https://buymeacoffee.com/madmachinations" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/default-orange.png" alt="Buy Me A Coffee" height="41" width="174"></a>
