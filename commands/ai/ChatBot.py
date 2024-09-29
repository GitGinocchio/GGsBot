from nextcord import Embed,Color,utils,channel,Permissions,Interaction
from nextcord.ext import commands
import nextcord
from jinja2 import Environment, FileSystemLoader
import requests
import json
import os

from utils.terminal import getlogger
from utils.jsonfile import JsonFile, _JsonDict

logger = getlogger()

templates = [template for template in os.listdir('./data/chatbot-templates')]
models = [
    '@cf/meta/llama-3-8b-instruct',
    '@hf/thebloke/llama-2-13b-chat-awq',
    '@cf/mistral/mistral-7b-instruct-v0.1',
    '@hf/google/gemma-7b-it',
    '@hf/nexusflow/starling-lm-7b-beta',
    '@cf/tinyllama/tinyllama-1.1b-chat-v1.0',
]

permissions = Permissions(
    use_slash_commands=True
    #administrator=True
)


class ChatBot(commands.Cog):
    def __init__(self, bot : commands.Bot):
        self.dirfmt = './data/guilds/{guild_id}/commands.ai.ChatBot'
        self.bot = bot

    @nextcord.slash_command('ai',"An AI chatbot powered by LLMs (Large Language Models)",default_member_permissions=permissions,dm_permission=False)
    async def ai(self, interaction : nextcord.Interaction): pass

    @ai.subcommand('newchat',"Create a chat with GG'sBot Ai")
    async def newchat(self, 
                      interaction : nextcord.Interaction,
                      public : bool = nextcord.SlashOption('public','Whether the chat between you and the bot should be public or private',required=True,default=False),
                      aimodel : str = nextcord.SlashOption("aimodel","Choose the Artificial Intelligence model you want to use",required=True,choices=models,default='@cf/meta/llama-3-8b-instruct'),
                      template : str | None = nextcord.SlashOption("template","Templates are used to get more specific answers for the type of context you want to get.",required=False,choices=templates,default=None),
                      tags: str = nextcord.SlashOption("tags","Write separated comma Tags used to get more specific answers",required=False,default=''),
                    ):
        await interaction.response.defer(ephemeral=True)
        workingdir = self.dirfmt.format(guild_id=interaction.guild.id)
        try:
            assert os.path.exists(f'{workingdir}/config.json'), "The ChatBot extension is not configured on the server"
            file = JsonFile(f'{workingdir}/config.json')

            assert interaction.channel.id == int(file['aichatbot-text-channel']), f"You can create an Ai chat only in the channel <@{file['aichatbot-text-channel']}>"

            thread : nextcord.Thread = await interaction.channel.create_thread(
                                                            name="New Chat",
                                                            reason=f'<@{interaction.user.id}> creates a GG\'Bot AI chat',
                                                            type=nextcord.ChannelType.public_thread if public else nextcord.ChannelType.private_thread
                                                            )
            await thread.edit(slowmode_delay=file['aichatbot-chat-delay'])
            await thread.add_user(interaction.user)

            file['threads'][str(thread.id)] = {
                "template" : template,
                "aimodel" : aimodel,
                "creator" : interaction.user.name,
                "creator-mention" : interaction.user.mention,
                "tags" : tags
                }
        except AssertionError as e:
            await interaction.followup.send(e)
        else:
            await interaction.followup.send("Chat created successfully")

    @ai.subcommand('ask',description="Ask a question to GG'sBot AI")
    async def ask(self): pass

    @ai.subcommand('delchat',"Delete a chat with GG'sBot Ai")
    async def delchat(self,interaction : nextcord.Interaction):
        try:
            await interaction.response.defer(ephemeral=True)
            workingdir = self.dirfmt.format(guild_id=interaction.guild.id)
            assert os.path.exists(f'{workingdir}/config.json'), "GG'sBot Ai extensions is not configured"
            
            file = JsonFile(f'{workingdir}/config.json')
            assert str(interaction.channel.id) in file['threads'], "You need to call this command in a GG'sBot Ai thread"

            await interaction.channel.delete()
            file['threads'].pop(str(interaction.channel.id))
        except AssertionError as e:
            await interaction.followup.send(e)

    @commands.Cog.listener()
    async def on_message(self, message : nextcord.Message):
        try:
            assert message.author != self.bot.user
            assert self.bot.user.mentioned_in(message) or any(role.name == self.bot.user.name for role in message.role_mentions)

            workingdir = self.dirfmt.format(guild_id=message.guild.id)

            assert os.path.exists(f'{workingdir}/config.json')

            file = JsonFile(f'{workingdir}/config.json')
            assert str(message.channel.id) in file['threads']

            template_name = file['threads'][str(message.channel.id)]['template']
            creator = file['threads'][str(message.channel.id)]['creator']
            creator_mention = file['threads'][str(message.channel.id)]['creator-mention']
            model = file['threads'][str(message.channel.id)]['aimodel']
            tags = file['threads'][str(message.channel.id)]['tags']

            jinjaenv = Environment(loader=FileSystemLoader('data/chatbot-templates'),variable_start_string='{',variable_end_string='}')

            developer = await self.bot.fetch_user(os.environ['DEVELOPER_ID'])

            template = jinjaenv.get_template(template_name)
            template_content = template.render({
                'name' : self.bot.user.name,
                'discriminator' : self.bot.user.discriminator,
                'developer' : developer.mention,
                'creator_mention' : creator_mention,
                'creator' : creator,
                'tags' : tags,
            })

            response = await message.reply("Sto formulando una risposta...")

            url = f"https://gateway.ai.cloudflare.com/v1/{os.environ['CLOUDFLARE_ACCOUNT_ID']}/ggsbot-ai"
            headers = {
                'Content-Type': 'application/json'
            }

            data = [
                {
                    "provider": "workers-ai",
                    "endpoint": model,
                    "headers": {
                        "Authorization": f"Bearer {os.environ['CLOUDFLARE_API_KEY']}",
                        "Content-Type": "application/json"
                    },
                    "query": {
                        "messages": [
                            {
                                "role":  "system",
                                "content": template_content
                            }
                        ]
                    }
                }
            ]

            async for history_message in message.channel.history(limit=None,oldest_first=True):
                if history_message.clean_content == '': continue
                data[0]['query']['messages'].append(
                    {
                        "role": "user" if history_message.author.name != self.bot.user.name else "assistant",
                        "content": history_message.clean_content
                    }
                )
            data[0]['query']['messages'].pop(-1)

            content = requests.get(url, headers=headers, data=json.dumps(data)).json()

            # Controllare prima se si ottiene la risposta o un errore

            result : str = content['result']['response']

            # Dividere le parti di codice in un messaggio singolo solo per quello
            # In caso se supera 2000 caratteri creare un messaggio separato

            current_text = ''
            sections = result.split('```')
            for n, section in enumerate(sections,0):
                for line in section.split('\n'):
                    if len(current_text + line + '\n') < 2000:
                        current_text += line + '\n'
                    else:
                        if n == 0: 
                            await response.edit(content=current_text)
                        elif n % 2 != 0:
                            await message.channel.send(content=f'```{current_text}```')
                        else:
                            if current_text:
                                await message.channel.send(content=current_text)
                        current_text = line + '\n'
                
                if current_text: 
                    if n == 0:
                        await response.edit(content=current_text)
                    elif n % 2 != 0:
                        await message.channel.send(content=f'```{current_text}```')
                    else:
                        await message.channel.send(content=current_text)
                    current_text = ''

            """
            lines = result.split('\n')
            current_text = lines[0]
            current_message = await response.edit(content=current_text)
            for line in lines[1::]:
                if len(current_text) + len(line) + 5 < 2000:
                    current_text += f'{line}\n'
                else:
                    if current_message:
                        current_message = await current_message.edit(content=current_text + (r'\n```' if current_text.count('```') % 2 != 0 else ''))
                        current_text = (r'\n```\n' if current_text.count('```') % 2 != 0 else '') + line + '\n'
                        current_message = None
                    else:
                        current_message = await message.channel.send(content=current_text + (r'\n```' if current_text.count('```') % 2 != 0 else ''))
            else:
                if current_text and current_message:
                    current_message = await current_message.edit(content=current_text)
                elif current_text:
                    current_message = await message.channel.send(content=current_text)
            """

        except AssertionError as e:
            pass

def setup(bot: commands.Bot):
    bot.add_cog(ChatBot(bot))