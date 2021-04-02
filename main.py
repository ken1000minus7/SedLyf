import discord
from discord.ext import commands
import os
import random
from keep_alive import keep_alive


client=discord.Client()

""""
bot=commands.Bot(command_prefix="$")

@bot.command(name="test")

async def test(ctx,arg):
  await ctx.send(arg)
"""
  
#List of sed words


g=["sed","killme","sad","depress"]


#List of sed lines 


sed=["I am not alone vro, loneliness is always with me",
'Yes, I am studying but "stu" is silent',
'The only time I was wanted was when I was playing GTA',
'Life is a party and I am a pinata',
"My life isn't a joke. Jokes have meaning",
"You hate me? Yeah, I know. I hate me too.",
"The only time I’m funny is when I insult myself",
"I'm not totally useless. I can be used as a bad example",
"Give up on your dreams and die"]


#List of gifs


sorry=["https://tenor.com/view/sorry-gif-19656670",'https://tenor.com/view/sad-cry-anime-im-sorry-gif-16156193',"https://tenor.com/view/im-sorry-sad-cry-i-was-stupid-gif-16562519","https://tenor.com/view/anime-beg-sorry-apologize-please-gif-4987836","https://tenor.com/view/jasorry-jaanime-chuunibyou-gif-4621792"]

ok=["https://tenor.com/view/its-ok-not-fine-sad-anime-cry-gif-16956661","https://tenor.com/view/whatever-ok-sure-onepunchman-saitama-gif-9728487","https://tenor.com/view/izuku-midoriya-smile-concerned-my-hero-academia-deku-gif-16389809",""]


@client.event


async def on_ready():
  print("We have logged in as {0.user}".format(client))
  await client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name='how sed your lyf is'))


@client.event 


async def on_message(message):

  if message.author==client.user:
    return 
  
  #Sending sed lines based on command

  if message.content.startswith("$alone"):
    await message.channel.send("I am not alone vro, loneliness is always with me")

  if message.content.startswith("$studying"):
    await message.channel.send('Yes, I am studying but "stu" is silent')

  if message.content.startswith("$wanted"):
    await message.channel.send('The only time I was wanted was when I was playing GTA')

  if message.content.startswith("$life"):
    await message.channel.send('Life is a party and I am a pinata')

  if message.content.startswith("$sedlyf"):
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
  

  #Sending sed lines randomly


  if message.content.startswith("$sed") or any(word in message.content for word in g):
    sedword=random.choice(sed)
    await message.channel.send(sedword)


  #Sending gif based on command


  if any(word in message.content for word in ["sorry","Sorry","SORRY"]):
    await message.channel.send(random.choice(sorry))

  if any(word in message.content for word in ["ok","Ok","OK"]):
    await message.channel.send(random.choice(ok))  
  
  #Sending message when a user is tagged 



  """
  if any(word in message.content for word in ["check","Check"]):
    user=message.author
    await message.channel.send(message.clean_content)
  """


  #Sending message when someone unauthorized tags everyone


  if any(word in message.content for word in ["@everyone","@here"]) and message.mention_everyone==False:
    await message.add_reaction('<:weeb1:814435206797983745>')
    await message.channel.send("Vro you're not popular enough to tag everyone")


#Make the bot run continuosly


keep_alive()


#Get unique token


client.run(os.getenv("TOKEN"))