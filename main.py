import discord
from discord.ext import commands
import os
import random
from keep_alive import keep_alive


client=discord.Client()

# intents = discord.Intents.default()
# intents.members = True
# bot=commands.Bot(command_prefix="$",intents=intents)

# @bot.command()

# async def test(ctx,arg):
#   await ctx.send(arg)

#Function for converting normal text to cool text - contributed by ishwar

letters = {
    'a':'<a:mra:838794840049188995>',
    'b':'<a:mrb:838794853466898454>',
    'c':'<a:mrc:695498871656415242>', #yet to fix
    'd':'<a:mrd:838794871618797609>',
    'e':'<a:mre:838794883124166676>',
    'f':'<a:mrf:838794896487219211>',
    'g':'<a:mrg:838794906456686652>',
    'h':'<a:mrh:838794914191900742>',
    'i':'<a:mri:838794920847605780>',
    'j':'<a:mrj:838794927600959549>',
    'k':'<a:mrk:838794941265084446>',
    'l':'<a:mrl:838794949729320970>',
    'm':'<a:mrm:838794955794546689>',
    'n':'<a:mrn:838794964355383307>',
    'o':'<a:mro:838794972190081024>',
    'p':'<a:mrp:838794979052093480>',
    'q':'<a:mrq:838794986375217212>',
    'r':'<a:mrr:838794994147131423>',
    's':'<a:mrs:838795001168527401>',
    't':'<a:mrt:838795007624216638>',
    'u':'<a:mru:838795015392067625>',
    'v':'<a:mrv:838795023906373653>',
    'w':'<a:mrw:838795029899378809>',
    'x':'<a:mrx:838795043069493299>',
    'y':'<a:mry:838795049382051881>',
    'z':'<a:mrz:695510969950142534>'  #yet to fix
}

def one(char, d):
    if char not in d:
      return char
    return d[char]
def convert(a):
    s = ""
    space=0
    for i in range(len(a)):
      if a[i] not in letters:
        space+=1
      s += one(a[i], letters)
    if space==len(a):
      return "Vro give some argument, you can't expect me to read your mind."
    return s
  
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
  
  """
  if message.content.startswith("$check"):
    embeded=discord.Embed(color=0x7289DA)
    embeded.add_field(name="Let's check this",value="SedLyf op",inline=False)
    print(embeded)
  
  """
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

  #Converting someone message to cool text
  
  if message.content.startswith("$cool"):
    m=message.content.lower()
    if len(m)==5:
      await message.channel.send("Vro give some argument, you can't expect me to read your mind.")
    elif m[5]!=" " and m[5]!="\n":
      await message.channel.send("Vro add space between the command and your argument")
    else:
      cool=convert(m[6:])
      await message.channel.send(cool)


#Make the bot run continuosly


keep_alive()


#Get unique token


client.run(os.getenv("TOKEN"))