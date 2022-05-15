from replit import db
import discord
import asyncio
# from dotenv import load_dotenv
import random
from discord.ext import commands
from discord_slash import SlashCommand
import youtube_dl
import math
import functools
import itertools
from async_timeout import timeout
from difflib import get_close_matches
# from discord_slash.utils.manage_commands import create_choice, create_option
# import discord_components
# from discord_components import DiscordComponents, Button, ButtonStyle,InteractionEventType
# load_dotenv()
from dinteractions_Paginator import Paginator
import os
import random
import requests
import json
from keep_alive import keep_alive
import gspread
from GridBoard import GridSpoilerGame

gc=gspread.service_account(filename="sheetss.json")
sh=gc.open("ss sheet").sheet1
data=sh.get_all_records()

url = "https://mashape-community-urban-dictionary.p.rapidapi.com/define"


headers = {
    'x-rapidapi-host': "mashape-community-urban-dictionary.p.rapidapi.com",
    'x-rapidapi-key': os.getenv("apikey")
    }


youtube_dl.utils.bug_reports_message = lambda: ''


class VoiceError(Exception):
    pass


class YTDLError(Exception):
    pass


class YTDLSource(discord.PCMVolumeTransformer):
    YTDL_OPTIONS = {
        'format': 'bestaudio/best',
        'extractaudio': True,
        'audioformat': 'mp3',
        'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
        'restrictfilenames': True,
        'noplaylist': True,
        'nocheckcertificate': True,
        'ignoreerrors': False,
        'logtostderr': False,
        'quiet': True,
        'no_warnings': True,
        'default_search': 'auto',
        'source_address': '0.0.0.0',
    }

    FFMPEG_OPTIONS = {
        'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
        'options': '-vn',
    }

    ytdl = youtube_dl.YoutubeDL(YTDL_OPTIONS)

    def __init__(self, ctx: commands.Context, source: discord.FFmpegPCMAudio, *, data: dict, volume: float = 0.5):
        super().__init__(source, volume)

        self.requester = ctx.author
        self.channel = ctx.channel
        self.data = data

        self.uploader = data.get('uploader')
        self.uploader_url = data.get('uploader_url')
        date = data.get('upload_date')
        self.upload_date = date[6:8] + '.' + date[4:6] + '.' + date[0:4]
        self.title = data.get('title')
        self.thumbnail = data.get('thumbnail')
        self.description = data.get('description')
        self.duration = self.parse_duration(int(data.get('duration')))
        self.tags = data.get('tags')
        self.url = data.get('webpage_url')
        self.views = data.get('view_count')
        self.likes = data.get('like_count')
        self.dislikes = data.get('dislike_count')
        self.stream_url = data.get('url')

    def __str__(self):
        return '**{0.title}** by **{0.uploader}**'.format(self)

    @classmethod
    async def create_source(cls, ctx: commands.Context, search: str, *, loop: asyncio.BaseEventLoop = None):
        loop = loop or asyncio.get_event_loop()

        partial = functools.partial(cls.ytdl.extract_info, search, download=False, process=False)
        data = await loop.run_in_executor(None, partial)

        if data is None:
            raise YTDLError('Couldn\'t find anything that matches `{}`'.format(search))

        if 'entries' not in data:
            process_info = data
        else:
            process_info = None
            for entry in data['entries']:
                if entry:
                    process_info = entry
                    break

            if process_info is None:
                raise YTDLError('Couldn\'t find anything that matches `{}`'.format(search))

        webpage_url = process_info['webpage_url']
        partial = functools.partial(cls.ytdl.extract_info, webpage_url, download=False)
        processed_info = await loop.run_in_executor(None, partial)

        if processed_info is None:
            raise YTDLError('Couldn\'t fetch `{}`'.format(webpage_url))

        if 'entries' not in processed_info:
            info = processed_info
        else:
            info = None
            while info is None:
                try:
                    info = processed_info['entries'].pop(0)
                except IndexError:
                    raise YTDLError('Couldn\'t retrieve any matches for `{}`'.format(webpage_url))

        return cls(ctx, discord.FFmpegPCMAudio(info['url'], **cls.FFMPEG_OPTIONS), data=info)

    @staticmethod
    def parse_duration(duration: int):
        minutes, seconds = divmod(duration, 60)
        hours, minutes = divmod(minutes, 60)
        days, hours = divmod(hours, 24)

        duration = []
        if days > 0:
            duration.append('{} days'.format(days))
        if hours > 0:
            duration.append('{} hours'.format(hours))
        if minutes > 0:
            duration.append('{} minutes'.format(minutes))
        if seconds > 0:
            duration.append('{} seconds'.format(seconds))

        return ', '.join(duration)


class Song:
    __slots__ = ('source', 'requester')

    def __init__(self, source: YTDLSource):
        self.source = source
        self.requester = source.requester

    def create_embed(self):
        embed = (discord.Embed(title='Now playing',
                               description='```css\n{0.source.title}\n```'.format(self),
                               color=discord.Color.blurple())
                 .add_field(name='Duration', value=self.source.duration)
                 .add_field(name='Requested by', value=self.requester.mention)
                 .add_field(name='Uploader', value='[{0.source.uploader}]({0.source.uploader_url})'.format(self))
                 .add_field(name='URL', value='[Click]({0.source.url})'.format(self))
                 .set_thumbnail(url=self.source.thumbnail))

        return embed


class SongQueue(asyncio.Queue):
    def __getitem__(self, item):
        if isinstance(item, slice):
            return list(itertools.islice(self._queue, item.start, item.stop, item.step))
        else:
            return self._queue[item]

    def __iter__(self):
        return self._queue.__iter__()

    def __len__(self):
        return self.qsize()

    def clear(self):
        self._queue.clear()

    def shuffle(self):
        random.shuffle(self._queue)

    def remove(self, index: int):
        del self._queue[index]


class VoiceState:
    def __init__(self, bot: commands.Bot, ctx: commands.Context):
        self.bot = bot
        self._ctx = ctx

        self.current = None
        self.voice = None
        self.next = asyncio.Event()
        self.songs = SongQueue()

        self._loop = False
        self._volume = 0.5
        self.skip_votes = set()

        self.audio_player = bot.loop.create_task(self.audio_player_task())

    def __del__(self):
        self.audio_player.cancel()

    @property
    def loop(self):
        return self._loop

    @loop.setter
    def loop(self, value: bool):
        self._loop = value

    @property
    def volume(self):
        return self._volume

    @volume.setter
    def volume(self, value: float):
        self._volume = value

    @property
    def is_playing(self):
        return self.voice and self.current

    async def audio_player_task(self):
        while True:
            self.next.clear()

            if not self.loop:
                # Try to get the next song within 3 minutes.
                # If no song will be added to the queue in time,
                # the player will disconnect due to performance
                # reasons.
                try:
                    async with timeout(180):  # 3 minutes
                        self.current = await self.songs.get()
                except asyncio.TimeoutError:
                    self.bot.loop.create_task(self.stop())
                    return

            self.current.source.volume = self._volume
            self.voice.play(self.current.source, after=self.play_next_song)
            await self.current.source.channel.send(embed=self.current.create_embed())

            await self.next.wait()

    def play_next_song(self, error=None):
        if error:
            raise VoiceError(str(error))

        self.next.set()

    def skip(self):
        self.skip_votes.clear()

        if self.is_playing:
            self.voice.stop()

    async def stop(self):
        self.songs.clear()

        if self.voice:
            await self.voice.disconnect()
            self.voice = None


class Music(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.voice_states = {}

    def get_voice_state(self, ctx: commands.Context):
        state = self.voice_states.get(ctx.guild.id)
        if not state:
            state = VoiceState(self.bot, ctx)
            self.voice_states[ctx.guild.id] = state

        return state

    def cog_unload(self):
        for state in self.voice_states.values():
            self.bot.loop.create_task(state.stop())

    def cog_check(self, ctx: commands.Context):
        if not ctx.guild:
            raise commands.NoPrivateMessage('This command can\'t be used in DM channels.')

        return True

    async def cog_before_invoke(self, ctx: commands.Context):
        ctx.voice_state = self.get_voice_state(ctx)

    async def cog_command_error(self, ctx: commands.Context, error: commands.CommandError):
        await ctx.send('An error occurred: {}'.format(str(error)))

    @commands.command(name='join', invoke_without_subcommand=True)
    async def _join(self, ctx: commands.Context):
        """Joins a voice channel."""

        destination = ctx.author.voice.channel
        if ctx.voice_state.voice:
            await ctx.voice_state.voice.move_to(destination)
            return

        ctx.voice_state.voice = await destination.connect()

    @commands.command(name='summon')
    @commands.has_permissions(manage_guild=True)
    async def _summon(self, ctx: commands.Context, *, channel: discord.VoiceChannel = None):
        """Summons the bot to a voice channel.

        If no channel was specified, it joins your channel.
        """

        if not channel and not ctx.author.voice:
            raise VoiceError('You are neither connected to a voice channel nor specified a channel to join.')

        destination = channel or ctx.author.voice.channel
        if ctx.voice_state.voice:
            await ctx.voice_state.voice.move_to(destination)
            return

        ctx.voice_state.voice = await destination.connect()

    @commands.command(name='leave', aliases=['disconnect',"dc"])
    @commands.has_permissions(manage_guild=True)
    async def _leave(self, ctx: commands.Context):
        """Clears the queue and leaves the voice channel."""

        if not ctx.voice_state.voice:
            return await ctx.send('Not connected to any voice channel.')

        await ctx.voice_state.stop()
        del self.voice_states[ctx.guild.id]

    @commands.command(name='volume')
    async def _volume(self, ctx: commands.Context, *, volume: int):
        """Sets the volume of the player."""

        if not ctx.voice_state.is_playing:
            return await ctx.send('Nothing being played at the moment.')

        if 0 > volume > 100:
            return await ctx.send('Volume must be between 0 and 100')

        ctx.voice_state.volume = volume / 100
        await ctx.send('Volume of the player set to {}%'.format(volume))

    @commands.command(name='now', aliases=['current', 'playing',"np"])
    async def _now(self, ctx: commands.Context):
        """Displays the currently playing song."""

        await ctx.send(embed=ctx.voice_state.current.create_embed())

    @commands.command(name='pause')
    @commands.has_permissions(manage_guild=True)
    async def _pause(self, ctx: commands.Context):
        """Pauses the currently playing song."""

        if ctx.voice_state.is_playing and ctx.voice_state.voice.is_playing():
            ctx.voice_state.voice.pause()
            await ctx.message.add_reaction('⏯')

    @commands.command(name='resume')
    @commands.has_permissions(manage_guild=True)
    async def _resume(self, ctx: commands.Context):
        """Resumes a currently paused song."""

        if ctx.voice_state.is_playing and ctx.voice_state.voice.is_paused():
            ctx.voice_state.voice.resume()
            await ctx.message.add_reaction('⏯')

    @commands.command(name='stop')
    @commands.has_permissions(manage_guild=True)
    async def _stop(self, ctx: commands.Context):
        """Stops playing song and clears the queue."""

        ctx.voice_state.songs.clear()

        if ctx.voice_state.is_playing:
            ctx.voice_state.voice.stop()
            await ctx.message.add_reaction('⏹')

    @commands.command(name='skip')
    async def _skip(self, ctx: commands.Context):
        """Vote to skip a song. The requester can automatically skip.
        3 skip votes are needed for the song to be skipped.
        """

        if not ctx.voice_state.is_playing:
            return await ctx.send('Not playing any music right now...')

        voter = ctx.message.author
        if voter == ctx.voice_state.current.requester:
            await ctx.message.add_reaction('⏭')
            ctx.voice_state.skip()

        elif voter.id not in ctx.voice_state.skip_votes:
            ctx.voice_state.skip_votes.add(voter.id)
            total_votes = len(ctx.voice_state.skip_votes)

            if total_votes >= 3:
                await ctx.message.add_reaction('⏭')
                ctx.voice_state.skip()
            else:
                await ctx.send('Skip vote added, currently at **{}/3**'.format(total_votes))

        else:
            await ctx.send('You have already voted to skip this song.')

    @commands.command(name='queue',aliases=["q"])
    async def _queue(self, ctx: commands.Context, *, page: int = 1):
        """Shows the player's queue.

        You can optionally specify the page to show. Each page contains 10 elements.
        """

        if len(ctx.voice_state.songs) == 0:
            return await ctx.send('Empty queue.')

        items_per_page = 10
        pages = math.ceil(len(ctx.voice_state.songs) / items_per_page)

        start = (page - 1) * items_per_page
        end = start + items_per_page

        queue = ''
        for i, song in enumerate(ctx.voice_state.songs[start:end], start=start):
            queue += '`{0}.` [**{1.source.title}**]({1.source.url})\n'.format(i + 1, song)

        embed = (discord.Embed(description='**{} tracks:**\n\n{}'.format(len(ctx.voice_state.songs), queue))
                 .set_footer(text='Viewing page {}/{}'.format(page, pages)))
        await ctx.send(embed=embed)

    @commands.command(name='shuffle')
    async def _shuffle(self, ctx: commands.Context):
        """Shuffles the queue."""

        if len(ctx.voice_state.songs) == 0:
            return await ctx.send('Empty queue.')

        ctx.voice_state.songs.shuffle()
        await ctx.message.add_reaction('✅')

    @commands.command(name='remove')
    async def _remove(self, ctx: commands.Context, index: int):
        """Removes a song from the queue at a given index."""

        if len(ctx.voice_state.songs) == 0:
            return await ctx.send('Empty queue.')

        ctx.voice_state.songs.remove(index - 1)
        await ctx.message.add_reaction('✅')

    @commands.command(name='loop')
    async def _loop(self, ctx: commands.Context):
        """Loops the currently playing song.

        Invoke this command again to unloop the song.
        """

        if not ctx.voice_state.is_playing:
            return await ctx.send('Nothing being played at the moment.')

        # Inverse boolean value to loop and unloop.
        ctx.voice_state.loop = not ctx.voice_state.loop
        await ctx.message.add_reaction('✅')

    @commands.command(name='play',aliases=["p"])
    async def _play(self, ctx: commands.Context, *, search: str):
        """Plays a song.

        If there are songs in the queue, this will be queued until the
        other songs finished playing.

        This command automatically searches from various sites if no URL is provided.
        A list of these sites can be found here: https://rg3.github.io/youtube-dl/supportedsites.html
        """

        if not ctx.voice_state.voice:
            await ctx.invoke(self._join)

        async with ctx.typing():
            try:
                source = await YTDLSource.create_source(ctx, search, loop=self.bot.loop)
            except YTDLError as e:
                await ctx.send('An error occurred while processing this request: {}'.format(str(e)))
            else:
                song = Song(source)

                await ctx.voice_state.songs.put(song)
                await ctx.send('Enqueued {}'.format(str(source)))

    @_join.before_invoke
    @_play.before_invoke
    async def ensure_voice_state(self, ctx: commands.Context):
        if not ctx.author.voice or not ctx.author.voice.channel:
            raise commands.CommandError('You are not connected to any voice channel.')

        if ctx.voice_client:
            if ctx.voice_client.channel != ctx.author.voice.channel:
                raise commands.CommandError('Bot is already in a voice channel.')






# client=discord.Client()
intents=discord.Intents.all() 
bot = commands.Bot(command_prefix='$',intents=intents)
slash=SlashCommand(bot,sync_commands=True)



@bot.event

async def on_ready():
  print(f"Logged in as {bot.user.name}")
  await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name='how sed your lyf is'))

    

"""
sh2=gc.open("ss sheet").get_worksheet(1)
songs=sh2.get_all_records()
youtube_dl.utils.bug_reports_message = lambda: ''

ytdl_format_options = {
    'format': 'bestaudio/best',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0' # bind to ipv4 since ipv6 addresses cause issues sometimes
}

ffmpeg_options = {
    'options': '-vn'
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = ""

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]
        filename = data['title'] if stream else ytdl.prepare_filename(data)
        for file in os.listdir("./"):
          if file=="song.mp3":
            os.remove("song.mp3")
            break
        for file in os.listdir("./"):
          if file==filename:
            os.rename(file,"song.mp3")
            filename="song.mp3"
            break
        return filename

@bot.command()

async def song(ctx,command,name="",url=""):
  if command=="add":
    if name=="":
      await ctx.send("Tell the name of the song you want to add")
      return 
    if url=="":
      await ctx.send("Give the url of the song you want to add")
      return
    found=False
    for i in range(len(songs)):
      if songs[i]["NAME"]==name:
        found=True 
        break
    if found:
      await ctx.send("Song with this name already exists")
      return 
    sh2.insert_row([name,url],2)
    songs.append({"NAME":name,"URL":url})
    await ctx.send(f"The song named '{name}' has been successfully added")
  elif command=="delete":
    if ctx.author.id==428956244238270475 or ctx.author.id==760014394330841088:
      if name=="":
        await ctx.send("Tell the name of the song you want to delete")
        return 
      found=False
      d=sh2.get_all_records()
      for i in range(len(d)):
        if d[i]["NAME"]==name:
          found=True
          sh2.delete_row(i+2)
          d.pop(i)
          for i in range(len(songs)):
            if songs[i]["NAME"]==name:
              songs.pop(i)
              break
          await ctx.send("Song with name '"+name+"' successfully deleted")
          break
      if not found:
        await ctx.send("No song available with this name")
    else:
      await ctx.send("Shut up nab, you are not authorized to delete")
  elif command=="list":
    listpages=[]
    count=0
    page=discord.Embed(title="List of songs available",
    colour=discord.Colour.orange())
    sslist=""
    while count<len(songs):
      if (count%15==0 and count!=0 and sslist!="") or count==len(songs)-1:
        if count==len(songs)-1 and count%15!=0:
          sslist+=songs[count]["NAME"]+"\n"
          count+=1
        page.add_field(name="\u200b",inline=False,value=sslist)
        listpages.append(page)
        if count==len(songs)-1 and count%15==0:
          page=discord.Embed(title="List of songs available",  colour=discord.Colour.orange())
          page.add_field(name="\u200b",inline=False,value=songs[count]["NAME"])
          listpages.append(page)
          count+=1
        page=discord.Embed(title="List of songs available",  colour=discord.Colour.orange())
        sslist=""
      else:
        sslist+=songs[count]["NAME"]+"\n"
        count+=1
    await Paginator(bot=bot,ctx=ctx,pages=listpages,timeout=60).run()
          

@bot.command()
async def join(ctx):
  if ctx.author.voice:
    await ctx.author.voice.channel.connect()
  else:
    await ctx.send("Vro you are not in a voice channel")


@bot.command()
async def leave(ctx):
  if ctx.guild.voice_client:
    await ctx.guild.voice_client.disconnect()
  else:
    await ctx.send("I am not in a voice channel idiot")


@bot.command()
async def play(ctx,name=""):
    if ctx.author.voice :
      if name=="":
        ctx.send("I can't read your mind. Tell which song to play")
        return
      if not ctx.guild.voice_client:
        await ctx.author.voice.channel.connect()
      found=False
      url=""
      for i in range(len(songs)):
        if songs[i]["NAME"]==name:
          url=songs[i]["URL"]
          found=True
          break
      if not found:
        await ctx.send("There is no song with this name")
        return
      async with ctx.typing():
        filename = await YTDLSource.from_url(url, loop=bot.loop)
        ctx.guild.voice_client.play(discord.FFmpegPCMAudio(executable="ffmpeg.exe", source=filename))
      await ctx.send('**Now playing:** {}'.format(name))
    else:
        await ctx.send("Vro you are not in a voice channel")


@bot.command()
async def pause(ctx):
    voice_client = ctx.guild.voice_client
    if voice_client.is_playing():
        await voice_client.pause()
        ctx.send("Song paused")
    else:
        await ctx.send("What am I supposed to pause? No song is being played")
    
@bot.command()
async def resume(ctx):
    voice_client = ctx.guild.voice_client
    if voice_client.is_paused():
        await voice_client.resume()
        ctx.send("Song resumed")
    else:
        await ctx.send("I can't resume something if it is not paused")

@bot.command()
async def stop(ctx):
    voice_client = ctx.guild.voice_client
    if voice_client.is_playing():
        await voice_client.stop()
        await ctx.send("Song stopped")
    else:
        await ctx.send("You need to stop sending meaningless commands. There is no song playing right now")
"""




#Function for converting normal text to cool text - contributed by ishwar

letters = {
    'a':'<a:mra:838794840049188995>',
    'b':'<a:mrb:838794853466898454>',
    'c':'<a:mrc:838856566231924787>',
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
    'x':'<a:mrx:838855265604075530>',
    'y':'<a:mry:838795049382051881>',
    'z':'<a:mrz:838840987610382366>'
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

#Function for searching name of ss, contributed by ishwar

def levenshtein_distance(word1: str, word2: str) -> int: 
	'''
	Gives the minimum number of single-character edits (insertions, deletions or substitutions) required to change word1 into word2.
	'''
	n, m = len(word1), len(word2)
	
	# Base-Cases
	if (m == 0): return n
	if (n == 0): return m

	#making dp array
	dp = [[0 for i in range(n + 1)]for j in range(m + 1)]
	for j in range(n + 1):
		dp[0][j] = j
	for i in range(m + 1):
		dp[i][0] = i

	# when word-1 and 2 has only one character
	if (word1[0] == word2[0]): 
		dp[0][0] = 0
	else:
		dp[0][1] = 1

	#when word-1 and 2 has more than 1 characters
	for i in range(1, n + 1):
		for j in range(1, m + 1):
			if (word1[i - 1] == word2[j - 1]):
				dp[j][i] = dp[j - 1][i - 1]
			else:
				dp[j][i] = min(dp[j - 1][i - 1], dp[j][i - 1], dp[j - 1][i]) + 1

	return dp[m][n]


def appropriate_number(a: str, b:str) -> int:
    return abs(len(b) - len(a)) + 2


def is_good(key: str, target: str) -> bool:
    max_diff = appropriate_number(key, target)
    distance = levenshtein_distance(key, target)

    if (distance <= max_diff):
        return True
    else:
        return False


def search(key: str, arr: list) -> list:
    search_result = []

    for name in arr:
        if is_good(key, name):
            search_result.append(name)

    return search_result

@bot.command(name="copy")
async def copy(ctx,*text):
  if len(text)==0:
    await ctx.send("Nab")
    return
  await ctx.message.delete()
  await ctx.send(' '.join(text))

@bot.command(name="ss")

async def ss(ctx,cmd="",name=""):
  if cmd=="list":
    listpages=[]
    count=0
    page=discord.Embed(title="List of SS available",
    colour=discord.Colour.orange())
    sslist=""
    while count<len(data):
      if (count%15==0 and count!=0 and sslist!="") or count==len(data)-1:
        if count==len(data)-1 and count%15!=0:
          sslist+=data[count]["NAME"]+"\n"
          count+=1
        page.add_field(name="\u200b",inline=False,value=sslist)
        listpages.append(page)
        if count==len(data)-1 and count%15==0:
          page=discord.Embed(title="List of SS available",  colour=discord.Colour.orange())
          page.add_field(name="\u200b",inline=False,value=data[count]["NAME"])
          listpages.append(page)
          count+=1
        page=discord.Embed(title="List of SS available",  colour=discord.Colour.orange())
        sslist=""
      else:
        sslist+=data[count]["NAME"]+"\n"
        count+=1
    await Paginator(bot=bot,ctx=ctx,pages=listpages,timeout=60).run()
  elif cmd=="search":
    if name=="":
      await ctx.send("Mention name of the ss you want to search")
      return
    listpages=[]
    count=0
    page=discord.Embed(title="List of SS with matching names",
    colour=discord.Colour.orange())
    matches=get_close_matches(name,[data[i]["NAME"] for i in range(len(data))])
    if matches==None or len(matches)==0:
      await ctx.send("No matching ss found with this name")
      return
    sslist=""
    while count<len(matches):
      if (count%15==0 and count!=0 and sslist!="") or count==len(matches)-1:
        if count==len(matches)-1 and count%15!=0:
          sslist+=matches[count]+"\n"
          count+=1
        page.add_field(name="\u200b",inline=False,value=sslist)
        listpages.append(page)
        if count==len(matches)-1 and count%15==0:
          page=discord.Embed(title="List of SS with matching names",  colour=discord.Colour.orange())
          page.add_field(name="\u200b",inline=False,value=matches[count])
          listpages.append(page)
          count+=1
        page=discord.Embed(title="List of SS with matching names",  colour=discord.Colour.orange())
        sslist=""
      else:
        sslist+=matches[count]+"\n"
        count+=1
    await Paginator(bot=bot,ctx=ctx,pages=listpages,timeout=60).run()

@bot.command(name="define")
async def define(ctx,*arg):
  if len(arg)==0:
    await ctx.send("Specify the word you want me to define")
    return
  term=' '.join(arg)
  querystring={"term":term}
  response = requests.request("GET",url,headers=headers,params=querystring)
  definitions=json.loads(response.text)
  li=definitions["list"]
  if len(li)==0:
    await ctx.send("No definitions found for this word")
    return
  listpages=[]
  for i in range(len(li)):
    page=discord.Embed(title=f"Definition of {term}     {(i+1)}/{len(li)}",colour=discord.Colour.orange())
    page.add_field(name="\u200b",value=li[i]["definition"],inline=False)
    page.add_field(name="\u200b",value=f"`{li[i]['example']}`",inline=False)
    listpages.append(page)
  await Paginator(bot=bot,ctx=ctx,pages=listpages,timeout=60).run()


@bot.command(name="gs",aliases=["gridspoiler","siprickroll","sr"])

async def gridspoiler(ctx, rickrolls = -1, sips = -1):
  grid = GridSpoilerGame(rickrolls, sips)
  await ctx.send(grid)

guild_ids=[798268746744594465]

@slash.slash(name="gridspoiler",description="Found out the puzzle pieces from the spoilers, beware of rickrolls")
async def _gridspoiler(ctx,rickrolls=2,sips=3):
  grid = GridSpoilerGame(rickrolls,sips)
  await ctx.send(grid)

@slash.slash(name="sssearch",description="Search for name of ss")
async def _sssearch(ctx,name):
  listpages=[]
  count=0
  page=discord.Embed(title="List of SS with matching names",
  colour=discord.Colour.orange())
  matches=get_close_matches(name,[data[i]["NAME"] for i in range(len(data))])
  if len(matches)==0:
    await ctx.send("No matching ss found with this name")
    return
  sslist=""
  while count<len(matches):
    if (count%15==0 and count!=0 and sslist!="") or count==len(matches)-1:
      if count==len(matches)-1 and count%15!=0:
        sslist+=matches[count]+"\n"
        count+=1
      page.add_field(name="\u200b",inline=False,value=sslist)
      listpages.append(page)
      if count==len(matches)-1 and count%15==0:
        page=discord.Embed(title="List of SS with matching names",  colour=discord.Colour.orange())
        page.add_field(name="\u200b",inline=False,value=matches[count])
        listpages.append(page)
        count+=1
      page=discord.Embed(title="List of SS with matching names",  colour=discord.Colour.orange())
      sslist=""
    else:
      sslist+=matches[count]+"\n"
      count+=1
  await Paginator(bot=bot,ctx=ctx,pages=listpages,timeout=60).run()

@slash.slash(name="sed",description="Send random sed lines")
async def __sed(ctx):
  sedword=random.choice(sed)
  await ctx.send(sedword)

@slash.slash(name="cool",description="Convert message to cool text")
async def __cool(ctx,text):
  m=text.lower()
  cool=convert(m)
  await ctx.send(cool)

@slash.slash(
  name="ss",description="Send ss"
  )
async def __ss(ctx,name):
  command=name
  found=False
  for i in range(len(data)):
    if command==data[i]["NAME"]:
      found=True 
      webhooks=await ctx.channel.webhooks()
      webhook=discord.utils.get(webhooks,name="SedLyf")
      if webhook is None:
        webhook = await ctx.channel.create_webhook(name="SedLyf")
      name=ctx.author.nick
      if name is None:
        name=ctx.author.name
          # await message.channel.send(data[i]["SSURL"])
      await webhook.send(data[i]["SSURL"], username=name ,avatar_url=ctx.author.avatar_url)
      await ctx.send("SS successfully sent",hidden=True)
      break  
  if not found:
    await ctx.send("No ss available with this name",hidden=True)
  
@slash.slash(name="sslist",description="List of all ss")

async def __sslist(ctx):
  listpages=[]
  count=0
  page=discord.Embed(title="List of SS available",
  colour=discord.Colour.orange())
  sslist=""
  while count<len(data):
    if (count%15==0 and count!=0 and sslist!="") or count==len(data)-1:
      if count==len(data)-1 and count%15!=0:
        sslist+=data[count]["NAME"]+"\n"
        count+=1
      page.add_field(name="\u200b",inline=False,value=sslist)
      listpages.append(page)
      if count==len(data)-1 and count%15==0:
        page=discord.Embed(title="List of SS available",  colour=discord.Colour.orange())
        page.add_field(name="\u200b",inline=False,value=data[count]["NAME"])
        listpages.append(page)
        count+=1
      page=discord.Embed(title="List of SS available",  colour=discord.Colour.orange())
      sslist=""
    else:
      sslist+=data[count]["NAME"]+"\n"
      count+=1
  await Paginator(bot=bot,ctx=ctx,pages=listpages,timeout=60).run()

@slash.slash(name="ssdelete",description="Delete ss")

async def __ssdelete(ctx,name):
  if ctx.author.id==428956244238270475 or ctx.author.id==760014394330841088:
    pass
  else:
    await ctx.send("Shut up nab. You're not authorized to delete")
    return
  found=False
  d=sh.get_all_records()
  for i in range(len(d)):
    if d[i]["NAME"]==name:
      found=True
      sh.delete_row(i+2)
      d.pop(i)
      for i in range(len(data)):
        if data[i]["NAME"]==name:
          data.pop(i)
          break
      await ctx.send("SS with name "+name+" successfully deleted")
      break
  if not found:
    await ctx.send("No ss available with this name")
# @client.event


# async def on_ready():
#   print("We have logged in as {0.user}".format(client))
#   # DiscordComponents(client,change_discord_methods=True)
#   await client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name='how sed your lyf is'))
@slash.slash(name="define",description="Get the definition of a word")

async def _define(ctx,word):
  querystring={"term":word}
  response = requests.request("GET",url,headers=headers,params=querystring)
  definitions=json.loads(response.text)
  li=definitions["list"]
  if len(li)==0:
    await ctx.send("No definitions found for this word")
    return
  listpages=[]
  for i in range(len(li)):
    page=discord.Embed(title=f"Definition of {word}     {(i+1)}/{len(li)}",colour=discord.Colour.orange())
    page.add_field(name="\u200b",value=li[i]["definition"],inline=False)
    page.add_field(name="\u200b",value=f"`{li[i]['example']}`",inline=False)
    listpages.append(page)
  await Paginator(bot=bot,ctx=ctx,pages=listpages,timeout=60).run()


@bot.listen("on_message")


async def on_message(message):

  if message.author==bot.user:
    return 
  
  
  
  
  if message.content.startswith("$sedlyf") and message.author.id==731204368593846312:
    await message.channel.send("Shut up meandeep")
    return
  if message.content.startswith("$sedlyf") and (message.author.id==706350907461337119 or message.author.id==556140685858963458):
    await message.channel.send("I am not a spammer. You are")
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


  if message.content.startswith("$sed"):
    sedword=random.choice(sed)
    await message.channel.send(sedword)
    


  #Sending gif based on command


  if message.content.startswith("$sorry"):
    await message.channel.send(random.choice(sorry))

  if message.content.startswith("$ok"):
    await message.channel.send(random.choice(ok))  
  



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
  
  if message.content.startswith("$fine"):
    await message.channel.send("https://cdn.discordapp.com/attachments/798458622836867094/861846938491551774/744496273976983622.png")

  if message.content.startswith("$ss"):
    command=message.content[4:]
    if(command.startswith("add")):
      if(len(command)<5 or command[4]==" "):
        await message.channel.send("Give a name to the ss")
      elif(len(message.attachments)):
        found=False
        for i in range(len(data)):
          if command[4:]==data[i]["NAME"]:
            found=True 
            break  
        if found:
          await message.channel.send("SS with this name already exists")
          return

        sh.insert_row([command[4:],message.attachments[0].url],2)
        data.append({"NAME":command[4:],"SSURL":message.attachments[0].url})
        await message.channel.send("The following ss has been successfully added with name "+command[4:]+"\n"+message.attachments[0].url)
      else:
        await message.channel.send("Add some attachment with your message")
    # elif command.startswith("list"):
    #   await Paginator(bot=bot,ctx=message.channel,pages=listpages,timeout=60).run()
      # msg="```List of ss available\n\n"
      # for i in range(len(data)):
      #   msg+=data[i]["NAME"]+"\n"
      # msg+="```"
      # await message.channel.send(msg)
      # pageno=0
      # await message.channel.send(embed=listpages[pageno],components=[
      #   [
      #     Button(
      #       label="Prev",
      #       id="prev",
      #       style=ButtonStyle.red
      #     ),
      #     Button(
      #       label="Next",
      #       id="next",
      #       style=ButtonStyle.red
      #     )
      #   ]
      # ])
      # while True:
      #   try:
      #     interaction=await client.wait_for("button_click",check=lambda i: i.component.id in ["prev","next"],timeout=20.0)
      #     if interaction.component.id=="prev":
      #       if pageno==0:
      #         pageno=len(listpages)-1
      #       else:
      #         pageno-=1
      #     elif interaction.component.id=="next":
      #       if pageno==len(listpages)-1:
      #         pageno=0
      #       else:
      #         pageno+=1
      #     await interaction.respond(
      #       type=InteractionType.UpdateMessage,
      #       embed=listpages[pageno],
      #       components=[
      #       [
      #         Button(
      #           label="Prev",
      #           id="prev",
      #           style=ButtonStyle.red
      #         ),
      #         Button(
      #           label="Next",
      #           id="next",
      #           style=ButtonStyle.red
      #         )
      #       ]
      #     ])
          # await message.edit(embed=listpages[pageno],
          # components=[
          #   [
          #     Button(
          #       label="Prev",
          #       id="prev",
          #       style=ButtonStyle.red
          #     ),
          #     Button(
          #       label="Next",
          #       id="next",
          #       style=ButtonStyle.red
          #     )
          #   ]
          # ])
        # except asyncio.TimeoutError:
          # await message.edit(
          #   components=[
          #   [
          #     Button(
          #       label="Prev",
          #       id="prev",
          #       style=ButtonStyle.red,
          #       disabled=True
          #     ),
          #     Button(
          #       label="Next",
          #       id="next",
          #       style=ButtonStyle.red,
          #       disabled=True
          #     )
          #   ]
          # ])
          # break


         
    elif command.startswith("delete") and (message.author.id==428956244238270475 or message.author.id==760014394330841088):
      if(len(command)<8 or command[7]==" "):
        await message.channel.send("Mention the name of the ss you want to delete")
      else:
        found=False
        d=sh.get_all_records()
        for i in range(len(d)):
          if d[i]["NAME"]==command[7:]:
            found=True
            sh.delete_row(i+2)
            d.pop(i)
            for i in range(len(data)):
              if data[i]["NAME"]==command[7:]:
                data.pop(i)
                break
            await message.channel.send("SS with name "+command[7:]+" successfully deleted")
            break
        if not found:
          await message.channel.send("No ss available with this name")
    elif command.startswith("delete") and message.author.id!=428956244238270475:
      await message.channel.send("Shut up nab. You're not authorized to delete")
  if(message.content.startswith(";") and message.content.endswith(";")):
    command=message.content
    if(len(command)<3 or command[1]==" "):
      await message.channel.send("Mention name of the ss")
    else:
      found=False
      for i in range(len(data)):
        if command[1:len(command)-1]==data[i]["NAME"]:
          found=True 
          webhooks=await message.channel.webhooks()
          webhook=discord.utils.get(webhooks,name="SedLyf")
          if webhook is None:
            webhook = await message.channel.create_webhook(name="SedLyf")
          name=message.author.nick
          if name is None:
            name=message.author.name
          # await message.channel.send(data[i]["SSURL"])
          await webhook.send(data[i]["SSURL"], username=name ,avatar_url=message.author.avatar_url)
          await message.delete()
          break  
      if not found:
        await message.channel.send("No ss available with this name")
        

    
    
bot.add_cog(Music(bot))

#Make the bot run continuosly


keep_alive()


#Get unique token

bot.run(os.getenv("TOKEN"))
# client.run(os.getenv("TOKEN"))
