import discord
import os
from keep_alive import keep_alive
client=discord.Client()
@client.event
async def on_ready():
  print("We have logged in as {0.user}".format(client))
@client.event 
async def on_message(message):
  if message.author==client.user:
    return 
  if message.content.startswith("$alone"):
    await message.channel.send("I am not alone vro, loneliness is always with me")
  if message.content.startswith("$studying"):
    await message.channel.send('Yes, I am studying but "stu" is silent')
  if message.content.startswith("$wanted"):
    await message.channel.send('The only time I was wanted was when I was playing GTA')
  if message.content.startswith("$life"):
    await message.channel.send('Life is a party and I am a pinata')
  if message.content.startswith("$sed"):
    for i in range(10):
      await message.channel.send('SED LYF')
      await message.channel.send('<:weeb1:814435206797983745><:weeb2:814435207456489492> ')
  if message.content.startswith("$joke"):
    await message.channel.send("My life isn't a joke. Jokes have meaning")
  if message.content.startswith("$ihateu"):
    await message.channel.send("Yeah, I know. I hate me too.")
  if message.content.startswith("$funny"):
    await message.channel.send("The only time I’m funny is when I insult myself")
  if message.content.startswith("$useless"):
    await message.channel.send("I'm not totally useless. I can be used as a bad example")
  if message.content.startswith("$dreams"):
    await message.channel.send("Give up on your dreams and die")
keep_alive()
client.run(os.getenv("TOKEN"))