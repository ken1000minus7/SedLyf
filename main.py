import discord
import os
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
      await message.channel.send('SED LYF <:Sad:652380607103500299>  <a:pepecri:805748915126140928> ')

client.run(os.getenv("TOKEN"))