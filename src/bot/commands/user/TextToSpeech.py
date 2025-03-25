from nextcord.ext import commands
from nextcord import        \
    Colour,                 \
    Guild,                  \
    Interaction,            \
    Message,                \
    SlashOption,            \
    PCMVolumeTransformer,   \
    File,                   \
    slash_command
from os import path
import traceback
from gtts import gTTS
#import pyttsx3
import io

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
    "Brazil": "br",
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
        self.bot = bot

    @slash_command('tts', 'Write your message and the bot will convert it to speech.')
    async def tts(self, interaction : Interaction): pass

    @tts.subcommand('autojoin', 'Automatically join the voice channel you joined.')
    async def autojoin(self, interaction : Interaction):
        try:
            pass
        except Exception as e:
            pass

    @tts.subcommand('setlanguage', 'Set the language for speech generation.')
    async def setlanguage(self, 
            interaction : Interaction,
            language : str = SlashOption('language', 'The language to use for speech generation.', required=True)
        ):
        try: 
            pass
        except Exception as e:
            pass

    @tts.subcommand('setaccent', 'Set the accent for speech generation.')
    async def setaccent(self,
            interaction : Interaction,
            accent : str = SlashOption('accent', 'The accent to use for speech generation.', required=True)

        ):
        try: 
            pass
        except Exception as e:
            pass

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

    @tts.subcommand('say', 'Write your message and the bot will convert it to speech in your voice channel or a file.')
    async def say(self, 
            interaction : Interaction,
            message : str,
            language : str = SlashOption(description="Set the language for the speech. es. English", required=False, default="English"),
            accent : str = SlashOption(description="Set the accent for the speech. es. Standard", required=False, default="Standard"),
            slow : bool = SlashOption(description="Use a slower speaking rate.", required=False, default=False),
            volume : float = SlashOption(description="Set the volume of the speech. (min: 0.0, max: 1.0, default: 0.8)", required=False, default=0.8, min_value=0.0, max_value=1.0),
            file : bool = SlashOption(description="Save the speech as a file. (default: False)", required=False, default=False)
        ):
        try:
            await interaction.response.defer(ephemeral=True)

            if not interaction.user.voice or not interaction.user.voice.channel:
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

            ffmpeg_path = path.abspath(path.join(str(config['paths']['bin']).format(os=OS, arch=ARCH), 'ffmpeg') + '.exe' if OS == 'Windows' else '')

            source = BytesIOFFmpegPCMAudio(filelike.read(),pipe=True,executable=ffmpeg_path)

            if voice_client.is_playing(): voice_client.stop()
            scaled_source = PCMVolumeTransformer(source, volume=volume)

            voice_client.play(scaled_source, after=lambda e: logger.error(traceback.format_exc()) if e else None)
            voice_client.source = scaled_source
            voice_client.source.volume = volume
        
        except GGsBotException as e:
            await interaction.followup.send(embed=e.asEmbed(), delete_after=5)
        except Exception as e:
            print(traceback.format_exc())

    @commands.Cog.listener()
    async def on_message(self, message: Message):
        pass

def setup(bot : commands.Bot):
    bot.add_cog(TextToSpeech(bot))