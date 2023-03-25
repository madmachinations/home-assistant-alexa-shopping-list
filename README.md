# Todoist-shopping-list

A custom component for Home Assistant which uses Todoist to bridge your Alexa shopping lists with the Home Assistant shopping list.

Items you add to your shopping list with Alexa will show up on the shopping list in home assistant. Equally anything you add or change or tick-off in the Home Assistant shopping list will translate to your Alexa Shopping List.

# Things you will need

You will need a Todoist account, which you have linked with your Alexa account. You will have an "Alexa Shopping List" in your Todoist projects if this has been linked successfully.

Next, in Todoist, go to your account settings and to integrations. Select Developer. Copy the API token, you will need this shortly.

# Installation

Copy the `todoist_shopping_list` folder to your `custom_components` directory inside your Home Assistant config folder.

Reboot Home Assistant

In the Home Assistant UI go to add a new integration. Search for `Todoist Shopping List`.

You will be asked to enter your Todoist API key.

That is it! Your HA Shopping list will now be kept synchronised with your Alexa shopping list.

Anything you add or change or mark as completed in your HA shopping list will be updated immediately within Todoist and your Alexa shopping list.

Anything you add or change or mark as completed within your Alexa shopping list will show up in Home Assistant within 60 seconds. It checks for updates once every minute.