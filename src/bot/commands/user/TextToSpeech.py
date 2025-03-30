from nextcord.ext import commands
from nextcord import        \
    Member,                 \
    VoiceState,             \
    VoiceChannel,           \
    Colour,                 \
    Guild,                  \
    Interaction,            \
    Message,                \
    SlashOption,            \
    PCMVolumeTransformer,   \
    File,                   \
    slash_command
from cachetools import TTLCache
from os import path
import traceback
from gtts import gTTS
#import pyttsx3
import io

from utils.db import Database
from utils.config import config
from utils.system import OS, ARCH
from utils.terminal import getlogger
from utils.classes import BytesIOFFmpegPCMAudio
from utils.exceptions import GGsBotException
from utils.abc import Page

logger = getlogger()

languages = {
    "Afrikaans": "af",
    "Amharic": "am",
    "Arabic": "ar",
    "Bulgarian": "bg",
    "Bengali": "bn",
    "Bosnian": "bs",
    "Catalan": "ca",
    "Czech": "cs",
    "Welsh": "cy",
    "Danish": "da",
    "German": "de",
    "Greek": "el",
    "English": "en",
    "Spanish": "es",
    "Estonian": "et",
    "Basque": "eu",
    "Finnish": "fi",
    "French": "fr",
    "French (Canada)": "fr-CA",
    "Galician": "gl",
    "Gujarati": "gu",
    "Hausa": "ha",
    "Hindi": "hi",
    "Croatian": "hr",
    "Hungarian": "hu",
    "Indonesian": "id",
    "Icelandic": "is",
    "Italian": "it",
    "Hebrew": "iw",
    "Japanese": "ja",
    "Javanese": "jw",
    "Khmer": "km",
    "Kannada": "kn",
    "Korean": "ko",
    "Latin": "la",
    "Lithuanian": "lt",
    "Latvian": "lv",
    "Malayalam": "ml",
    "Marathi": "mr",
    "Malay": "ms",
    "Myanmar (Burmese)": "my",
    "Nepali": "ne",
    "Dutch": "nl",
    "Norwegian": "no",
    "Punjabi (Gurmukhi)": "pa",
    "Polish": "pl",
    "Portuguese (Brazil)": "pt",
    "Portuguese (Portugal)": "pt-PT",
    "Romanian": "ro",
    "Russian": "ru",
    "Sinhala": "si",
    "Slovak": "sk",
    "Albanian": "sq",
    "Serbian": "sr",
    "Sundanese": "su",
    "Swedish": "sv",
    "Swahili": "sw",
    "Tamil": "ta",
    "Telugu": "te",
    "Thai": "th",
    "Filipino": "tl",
    "Turkish": "tr",
    "Ukrainian": "uk",
    "Urdu": "ur",
    "Vietnamese": "vi",
    "Cantonese": "yue",
    "Chinese (Simplified)": "zh-CN",
    "Chinese (Mandarin/Taiwan)": "zh-TW",
    "Chinese (Mandarin)": "zh",
}

accents = {
    "Standard": "com",
    "Andorra": "ad",
    "United Arab Emirates": "ae",
    "Afghanistan": "com.af",
    "Antigua and Barbuda": "com.ag",
    "Anguilla": "com.ai",
    "Argentina": "com.ar",
    "American Samoa": "as",
    "Austria": "at",
    "Australia": "com.au",
    "Azerbaijan": "az",
    "Bosnia and Herzegovina": "ba",
    "Bangladesh": "com.bd",
    "Belgium": "be",
    "Burkina Faso": "bf",
    "Bulgaria": "bg",
    "Benin": "bj",
    "Brazil": "com.br",
    "Bahamas": "bs",
    "Bhutan": "bt",
    "Botswana": "co.bw",
    "Belarus": "by",
    "Belize": "com.bz",
    "Canada": "ca",
    "Democratic Republic of the Congo": "cd",
    "Switzerland": "ch",
    "Ivory Coast": "ci",
    "Cook Islands": "co.ck",
    "Chile": "cl",
    "Cameroon": "cm",
    "China": "cn",
    "Colombia": "com.co",
    "Costa Rica": "co.cr",
    "Cape Verde": "cv",
    "Djibouti": "dj",
    "Dominica": "dm",
    "Dominican Republic": "com.do",
    "Algeria": "dz",
    "Ecuador": "com.ec",
    "Estonia": "ee",
    "Egypt": "com.eg",
    "Spain": "es",
    "Ethiopia": "et",
    "Finland": "fi",
    "Fiji": "com.fj",
    "Micronesia": "fm",
    "France": "fr",
    "Gabon": "ga",
    "Georgia": "ge",
    "Guernsey": "gg",
    "Ghana": "com.gh",
    "Gibraltar": "com.gi",
    "Greenland": "gl",
    "Gambia": "gm",
    "Greece": "gr",
    "Guatemala": "com.gt",
    "Guyana": "gy",
    "Hong Kong": "com.hk",
    "Honduras": "hn",
    "Haiti": "ht",
    "Croatia": "hr",
    "Hungary": "hu",
    "Indonesia": "co.id",
    "Ireland": "ie",
    "Israel": "co.il",
    "Isle of Man": "im",
    "India": "co.in",
    "Iraq": "iq",
    "Iceland": "is",
    "Italy": "it",
    "Israel (Hebrew)": "iw",
    "Jersey": "je",
    "Jordan": "jo",
    "Japan": "co.jp",
    "Kenya": "co.ke",
    "Cambodia": "com.kh",
    "Kiribati": "ki",
    "Kyrgyzstan": "kg",
    "South Korea": "co.kr",
    "Kuwait": "com.kw",
    "Kazakhstan": "kz",
    "Laos": "la",
    "Lebanon": "com.lb",
    "Liechtenstein": "li",
    "Sri Lanka": "lk",
    "Lesotho": "co.ls",
    "Lithuania": "lt",
    "Luxembourg": "lu",
    "Latvia": "lv",
    "Libya": "com.ly",
    "Morocco": "com.ma",
    "Moldova": "md",
    "Montenegro": "me",
    "Madagascar": "mg",
    "North Macedonia": "mk",
    "Mali": "ml",
    "Myanmar": "mm",
    "Mongolia": "mn",
    "Montserrat": "ms",
    "Malta": "com.mt",
    "Mauritius": "mu",
    "Maldives": "mv",
    "Malawi": "mw",
    "Mexico": "com.mx",
    "Malaysia": "com.my",
    "Mozambique": "co.mz",
    "Namibia": "na",
    "Nigeria": "ng",
    "Nicaragua": "ni",
    "Niger": "ne",
    "Netherlands": "nl",
    "Norway": "no",
    "Nepal": "com.np",
    "Nauru": "nr",
    "Niue": "nu",
    "New Zealand": "co.nz",
    "Oman": "com.om",
    "Panama": "pa",
    "Peru": "pe",
    "Papua New Guinea": "pg",
    "Philippines": "ph",
    "Pakistan": "pk",
    "Poland": "pl",
    "Pitcairn Islands": "pn",
    "Puerto Rico": "com.pr",
    "Palestine": "ps",
    "Portugal": "pt",
    "Paraguay": "com.py",
    "Qatar": "com.qa",
    "Romania": "ro",
    "Russia": "ru",
    "Rwanda": "rw",
    "Saudi Arabia": "com.sa",
    "Solomon Islands": "com.sb",
    "Seychelles": "sc",
    "Sweden": "se",
    "Singapore": "com.sg",
    "Saint Helena": "sh",
    "Slovenia": "si",
    "Slovakia": "sk",
    "Sierra Leone": "com.sl",
    "Senegal": "sn",
    "Somalia": "so",
    "San Marino": "sm",
    "Suriname": "sr",
    "São Tomé and Príncipe": "st",
    "El Salvador": "com.sv",
    "Chad": "td",
    "Togo": "tg",
    "Thailand": "co.th",
    "Tajikistan": "com.tj",
    "Timor-Leste": "tl",
    "Turkmenistan": "tm",
    "Tunisia": "tn",
    "Tonga": "to",
    "Turkey": "com.tr",
    "Trinidad and Tobago": "tt",
    "Taiwan": "com.tw",
    "Tanzania": "co.tz",
    "Ukraine": "com.ua",
    "Uganda": "co.ug",
    "United Kingdom": "co.uk",
    "Uruguay": "com.uy",
    "Uzbekistan": "co.uz",
    "Saint Vincent and the Grenadines": "com.vc",
    "Venezuela": "co.ve",
    "British Virgin Islands": "vg",
    "U.S. Virgin Islands": "co.vi",
    "Vietnam": "com.vn",
    "Vanuatu": "vu",
    "Samoa": "ws",
    "Serbia": "rs",
    "South Africa": "co.za",
    "Zambia": "co.zm",
    "Zimbabwe": "co.zw",
    "Catalan Language & Culture": "cat"
}



class TextToSpeech(commands.Cog):
    def __init__(self, bot : commands.Bot):
        commands.Cog.__init__(self)
        self.db = Database()
        self.sessions : dict[int, dict] = TTLCache(maxsize=1000, ttl=3600)
        self.bot = bot

        self.tts_enabled_page : Page = None
        
        self.tts_disabled_page : Page = None

    @commands.Cog.listener()
    async def on_ready(self):
        self.tts_enabled_page = Page(
            colour=Colour.green(),
            title="TTS Enabled for this Voice Channel",
            description="Send a message in this channel and the bot will convert it to speech."
        )
        
        self.tts_disabled_page = Page(
            colour=Colour.red(),
            title="TTS Disabled for this Voice Channel",
            description="If you want to re-enable the TTS use the `/tts join`, you can also set the `/tts set autojoin` feature if you want the bot to automatically join the voice channel you joined.",
        )

    @slash_command('tts', 'Write your message and the bot will convert it to speech.')
    async def tts(self, interaction : Interaction): pass

    # Set commands

    @tts.subcommand('set', "Set of commands to configure the tts extension for each user.")
    async def set(self, interaction : Interaction): pass

    @set.subcommand('autojoin', 'Automatically join the voice channel you joined.')
    async def autojoin(self, 
            interaction : Interaction,
            active : bool = SlashOption('active', 'Whether to enable or disable automatic joining.', required=True)
        ):
        try: 
            await interaction.response.defer(ephemeral=True)
            
            async with self.db:
                user_config = await self.db.getUserConfig(interaction.user)

                previous_autojoin = user_config.get('tts', {}).get('autojoin', None)

                if previous_autojoin and previous_autojoin == active:
                    raise GGsBotException(
                        title="Error",
                        description=f"You have already set the autojoin option to **{previous_autojoin}**.",
                    )
                
                if 'tts' not in user_config: user_config["tts"] = {}

                user_config['tts']['autojoin'] = active

                self.sessions[interaction.user.id] = user_config['tts']

                await self.db.editUserConfig(interaction.user, user_config)

            page = Page(
                colour=Colour.green(),
                title="Autojoin Set Successfully",
                description=f"Autojoin feature has been set from **{'enabled' if previous_autojoin else 'disabled'}**  to **{'enabled' if active else 'disabled'}**.",
            )

            await interaction.followup.send(embed=page, ephemeral=True)
        except GGsBotException as e:
            await interaction.followup.send(embed=e.asEmbed(), delete_after=5, ephemeral=True)

    @set.subcommand('language', 'Set the language for speech generation.')
    async def language(self, 
            interaction : Interaction,
            language : str = SlashOption('language', 'The language to use for speech generation.', required=True)
        ):
        try: 
            await interaction.response.defer(ephemeral=True)

            if not (lang_code:=languages.get(language)):
                raise GGsBotException(
                    title="Invalid language.",
                    description="Please select a valid language from the list of available languages.",
                )
            
            async with self.db:
                user_config = await self.db.getUserConfig(interaction.user)

                previous_lang = user_config.get('tts', {}).get('language', None)

                if 'tts' not in user_config: user_config["tts"] = {}

                user_config['tts']['language'] = language

                self.sessions[interaction.user.id] = user_config['tts']

                await self.db.editUserConfig(interaction.user, user_config)

            page = Page(
                colour=Colour.green(),
                title="Language Set Successfully",
                description=f"Your language has been set from **{str(previous_lang)}**  to **{language}**.",
            )

            await interaction.followup.send(embed=page, ephemeral=True)
        except GGsBotException as e:
            await interaction.followup.send(embed=e.asEmbed(), delete_after=5, ephemeral=True)

    @set.subcommand('accent', 'Set the accent for speech generation.')
    async def accent(self,
            interaction : Interaction,
            accent : str = SlashOption('accent', 'The accent to use for speech generation.', required=True)
        ):
        try: 
            await interaction.response.defer(ephemeral=True)

            if not (accent_code:=accents.get(accent)):
                raise GGsBotException(
                    title="Invalid accent.",
                    description="Please select a valid accent from the list of available accents.",
                )
            
            async with self.db:
                user_config = await self.db.getUserConfig(interaction.user)

                previous_accent = user_config.get('tts', {}).get('accent', None)

                if 'tts' not in user_config: user_config["tts"] = {}

                user_config['tts']['accent'] = accent

                self.sessions[interaction.user.id] = user_config['tts']

                await self.db.editUserConfig(interaction.user, user_config)

            page = Page(
                colour=Colour.green(),
                title="Accent Set Successfully",
                description=f"Your accent has been set from **{str(previous_accent)}**  to **{accent}**.",
            )

            await interaction.followup.send(embed=page, ephemeral=True)
        except GGsBotException as e:
            await interaction.followup.send(embed=e.asEmbed(), delete_after=5, ephemeral=True)

    # Get commands

    @tts.subcommand('languages', 'List all available languages for speech generation.')
    async def languages(self, interaction : Interaction):
        try: 
            await interaction.response.defer(ephemeral=True)

            page = Page(
                colour=Colour.green(),
                title="Available Languages",
                description="Here is a list of all available languages for speech generation.",
            )

            page.add_field(
                name="Available Languages",
                value=", ".join(f'**{language}**' for language in languages.keys())
            )

            await interaction.followup.send(embed=page)
        except Exception as e:
            logger.error(traceback.format_exc())

    @tts.subcommand('accents', 'List all available accents for speech generation.')
    async def accents(self, interaction : Interaction):
        try: 
            await interaction.response.defer(ephemeral=True)

            page = Page(
                colour=Colour.green(),
                title="Available Accents",
                description="Here is a list of all available accents for speech generation.",
            )

            i = 0
            accents_list = list(accents.keys())
            while True:
                text = ''

                while len(text) + len(accents_list[i]) < 1020:
                    if text != '':
                        text = ','.join((text, f'**{accents_list[i]}**'))
                    else:
                        text = f'**{accents_list[i]}**'
                    i += 1

                    if len(accents_list) <= i: break

                page.add_field(name="Available Accents",value=text, inline=False)

                if len(accents_list) <= i: break

            await interaction.followup.send(embed=page)
        except Exception as e:
            logger.error(traceback.format_exc())

    # Speech commands

    @tts.subcommand('join', 'Join your voice channel to start speech generation. (not the same as `/music join`)')
    async def join(self, interaction : Interaction):
        try:
            await interaction.response.defer(ephemeral=True)

            if not interaction.user.voice:
                raise GGsBotException(
                    title="Not Connected",
                    description="You are not connected to a voice channel."
                )
            elif interaction.user.guild.voice_client and interaction.user.guild.voice_client.is_connected():
                raise GGsBotException(
                    title="Already Connected",
                    description="GGsBot is already connected to a voice channel. ",
                )
            
            if interaction.user.id not in self.sessions:
                async with self.db:
                    user_config = await self.db.getUserConfig(interaction.user)

                self.sessions[interaction.user.id] = user_config.get('tts', {})

            await interaction.user.voice.channel.connect()
            await interaction.guild.voice_client.channel.send(embed=self.tts_enabled_page)

            page = Page(
                colour=Colour.green(),
                title="Successfully joined your voice channel",
                description="GGsBot is now connected to the voice channel and can start speaking."
            )

        except GGsBotException as e:
            await interaction.followup.send(embed=e.asEmbed(), ephemeral=True, delete_after=5)
        except Exception as e:
            logger.error(traceback.format_exc())
        else:
            await interaction.followup.send(embed=page)

    @tts.subcommand('leave', 'Leave your voice channel to stop speech generation. (not the same as `/music leave`)')
    async def leave(self, interaction : Interaction):
        try:
            await interaction.response.defer(ephemeral=True)

            if not interaction.guild.voice_client or not interaction.guild.voice_client.is_connected():
                raise GGsBotException(title="Not Connected", description="GGsBot is not connected to a voice channel.")

            await interaction.guild.voice_client.channel.send(embed=self.tts_disabled_page)
            await interaction.guild.voice_client.disconnect()
        except GGsBotException as e:
            await interaction.followup.send(embed=e.asEmbed(), ephemeral=True, delete_after=5)
        except Exception as e:
            logger.error(traceback.format_exc())

    @tts.subcommand('say', 'Write your message and the bot will convert it to speech in your voice channel or a file.')
    async def say(self, 
            interaction : Interaction,
            message : str = SlashOption(description="Write your message and the bot will convert it to speech in your voice channel or a file.", required=True),
            language : str = SlashOption(description="Set the language for the speech. es. English", required=False, default="English"),
            accent : str = SlashOption(description="Set the accent for the speech. es. Standard", required=False, default="Standard"),
            slow : bool = SlashOption(description="Use a slower speaking rate.", required=False, default=False),
            volume : float = SlashOption(description="Set the volume of the speech. (min: 0.0, max: 1.0, default: 0.8)", required=False, default=0.8, min_value=0.0, max_value=1.0),
            file : bool = SlashOption(description="Save the speech as a file. (default: False)", required=False, default=False)
        ):
        try:
            await interaction.response.defer(ephemeral=True)

            if not file and not interaction.user.voice:
                raise GGsBotException(
                    title="You must be in a voice channel to use this command.",
                    description="Please join a voice channel and try again.",
                )
            elif not (lang_code:=languages.get(language)):
                raise GGsBotException(
                    title="Invalid language.",
                    description="Please select a valid language from the list of available languages.",
                )
            elif not (accent_code:=accents.get(accent)):
                raise GGsBotException(
                    title="Invalid accent.",
                    description="Please select a valid accent from the list of available accents.",
                )

            engine = gTTS(message, lang=lang_code, tld=accent_code, slow=slow)

            filelike = io.BytesIO()
            engine.write_to_fp(filelike)
            filelike.seek(0)

            if file:
                ttsaudiofile = File(filelike, filename="ggsbotTTS.mp3", description="TTS Audio")
                await interaction.followup.send(content="Here is your TTS audio file. Click the link below to download it.", file=ttsaudiofile, ephemeral=True)
                return
            
            voice_client = interaction.guild.voice_client if interaction.guild.voice_client else await interaction.user.voice.channel.connect()

            ffmpeg_path = path.join(str(config['paths']['bin']).format(os=OS, arch=ARCH), 'ffmpeg') + '.exe' if OS == 'Windows' else ''

            source = BytesIOFFmpegPCMAudio(filelike.read(),pipe=True,executable=ffmpeg_path)

            if voice_client.is_playing(): voice_client.stop()
            scaled_source = PCMVolumeTransformer(source, volume=volume)

            voice_client.play(scaled_source, after=lambda e: logger.error(traceback.format_exc()) if e else None)
            voice_client.source = scaled_source
            voice_client.source.volume = volume
        
        except GGsBotException as e:
            await interaction.followup.send(embed=e.asEmbed(), delete_after=5)
        except Exception as e:
            logger.error(traceback.format_exc())

    # Events

    @commands.Cog.listener()
    async def on_voice_state_update(self, member : Member, before : VoiceState, after : VoiceState):
        try:
            voice_client = member.guild.voice_client

            if not after.channel and before.channel is not None:
                # Evento in cui l'utente ha abbandonato un canale vocale qualsiasi
                if voice_client and voice_client.channel.id == before.channel.id and len(before.channel.members) == 0:
                    # Evento in cui l'utente ha abbandonato il canale vocale e non c'e' nessun'altro
                    await before.channel.send(embed=self.tts_disabled_page)
                
                    voice_client.disconnect()

                if member.id in self.sessions: del self.sessions[member.id]
                return
            
            if after.channel and before.channel and after.channel.id == before.channel.id: return
            
            # Evento in cui il bot e' gia' connesso ad un canale oppure l'utente ha abbandonato un canale vocale
            if voice_client and voice_client.is_connected() and after.channel is None:
                return
            
            # Evento in cui il bot non e' connesso ad un canale vocale
            async with self.db:
                user_config = await self.db.getUserConfig(member)
                tts_config = user_config.get('tts', {})
                autojoin = bool(tts_config.get('autojoin', False))

            if not autojoin: return

            if not voice_client or not voice_client.is_connected():
                await after.channel.connect()
                await after.channel.send(embed=self.tts_enabled_page)

            self.sessions[member.id] = tts_config
        except Exception as e:
            logger.error(traceback.format_exc())

    @commands.Cog.listener()
    async def on_message(self, message: Message):
        try:
            if not message.guild: return
            if not message.guild.voice_client: return
            if message.author.id not in self.sessions: return
            if message.author.voice.channel.id != message.channel.id: return

            if not message.author.id in self.sessions:
                async with self.db:
                    tts_config = await self.db.getUserConfig(message.author).get('tts', {})
            else:
                tts_config = self.sessions[message.author.id]

            language = str(tts_config.get('language', 'English'))
            accent = str(tts_config.get('accent', 'Standard'))
            slow = bool(tts_config.get('slow', False))
            volume = float(tts_config.get('volume', 0.8))

            engine = gTTS(message.clean_content, lang=languages.get(language), tld=accents.get(accent), slow=slow)

            filelike = io.BytesIO()
            engine.write_to_fp(filelike)
            filelike.seek(0)

            ffmpeg_path = path.abspath(path.join(str(config['paths']['bin']).format(os=OS, arch=ARCH), 'ffmpeg') + '.exe' if OS == 'Windows' else '')
            source = BytesIOFFmpegPCMAudio(filelike.read(),pipe=True,executable=ffmpeg_path)

            voice_client = message.guild.voice_client

            if voice_client.is_playing(): voice_client.stop()
            scaled_source = PCMVolumeTransformer(source, volume=volume)

            voice_client.play(scaled_source, after=lambda e: logger.error(traceback.format_exc()) if e else None)
            voice_client.source = scaled_source
            voice_client.source.volume = volume
        except Exception as e:
            logger.error(traceback.format_exc())

def setup(bot : commands.Bot):
    bot.add_cog(TextToSpeech(bot))