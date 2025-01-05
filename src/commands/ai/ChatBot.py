from nextcord import \
        Embed,\
        Color,\
        utils,\
        Thread, \
        Permissions,\
        Interaction, \
        SlashOption, \
        slash_command, \
        ChannelType, \
        Message
from jinja2 import Environment, FileSystemLoader
from datetime import datetime, timezone
from nextcord.ext import commands
#from PIL import Image
import numpy as np
import requests
import nextcord
import base64
import struct
import json
import os
import io

from utils.terminal import getlogger
from utils.commons import \
    Extensions,           \
    USER_INTEGRATION,     \
    GUILD_INTEGRATION,    \
    GLOBAL_INTEGRATION
from utils.db import Database
from utils.exceptions import *
from utils.config import config

logger = getlogger()

templates = [template for template in os.listdir(config["paths"]["chatbot_templates"])]

txt2txt_models = [
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
        self.db = Database()
        self.bot = bot

    @slash_command('chat',"An AI chatbot powered by LLMs (Large Language Models)",default_member_permissions=permissions,integration_types=GUILD_INTEGRATION)
    async def chat(self, interaction : Interaction): pass

    @slash_command('ask',description="Ask a question to GG'sBot AI",default_member_permissions=permissions,integration_types=GLOBAL_INTEGRATION)
    async def ask(self,
                  interaction : Interaction,
                  prompt : str = SlashOption("prompt","The question you want to ask",required=True),
                  model : str = SlashOption("aimodel","Choose the Artificial Intelligence model you want to use",required=False,choices=txt2txt_models,default=txt2txt_models[0]),
                  #template : str | None = SlashOption("template","Templates are used to get more specific answers for the type of context you want to get.",required=False,choices=templates,default=None),
                  #tags: str = SlashOption("tags","Write separated comma Tags used to get more specific answers",required=False,default=''),
                  ephemeral : bool = SlashOption(description="Whether the response should be ephemeral or not",required=False,default=True),
                ):
        try:
            await interaction.response.defer(ephemeral=ephemeral)
            url = f"https://gateway.ai.cloudflare.com/v1/{os.environ['CLOUDFLARE_ACCOUNT_ID']}/ggsbot-ai"
            headers = { 'Content-Type': 'application/json' }
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
                            { "role" : "system", "content" : "The user will ask you a question, answer in the same language, give your opinion on the topic discussed, you must be concise" },
                            { "role": "user", "content": prompt }
                        ]
                    }
                }
            ]

            content = requests.get(url, headers=headers, data=json.dumps(data)).json()

            if not content['success']: raise CloudFlareAIException(code=content['errors'][0]['code'])
            result : str = content['result']['response']

            max_length = 1000
            message = f"\n\n**[Create a chat to have answers longer than {max_length} characters]**"

            if len(result) > max_length:
                text_limit = max_length - len(message)
                result = result[:text_limit] + message

            embed = Embed(
                title=f"{prompt}",
                description=f"{result}",
                color=Color.green(),
                timestamp=datetime.now(timezone.utc)
            )
            embed.add_field(name="Model:", value=f"**{model}**", inline=True)
            embed.set_footer(
                text=f"Generated by {self.bot.user.name} powered by Cloudflare Ai Workers", 
                icon_url="https://static-00.iconduck.com/assets.00/cloudflare-icon-512x512-c1lpcyo0.png"
            )
            embed.set_author(name=interaction.user.name,icon_url=interaction.user.avatar.url if interaction.user.avatar else interaction.user.default_avatar.url)

            await interaction.followup.send(embed=embed)
        except CloudFlareAIException as e:
            await interaction.followup.send(embed=e.asEmbed())
            logger.error(e)

    @chat.subcommand('new',"Create a chat with GG'sBot Ai")
    async def newchat(self, 
                      interaction : Interaction,
                      public : bool = SlashOption('public','Whether the chat between you and the bot should be public or private',required=True,default=False),
                      aimodel : str = SlashOption("aimodel","Choose the Artificial Intelligence model you want to use",required=True,choices=txt2txt_models,default=txt2txt_models[0]),
                      template : str | None = SlashOption("template","Templates are used to get more specific answers for the type of context you want to get.",required=False,choices=templates,default=None),
                      tags: str = SlashOption("tags","Write separated comma Tags used to get more specific answers",required=False,default=''),
                    ):
        await interaction.response.defer(ephemeral=True)

        try:

            async with self.db:
                config = await self.db.getExtensionConfig(interaction.guild, Extensions.AICHATBOT)

            if not interaction.channel.id == int(config['text-channel']): raise SlashCommandException("Invalid Channel")

            thread : Thread = await interaction.channel.create_thread(
                                                            name="New Chat",
                                                            reason=f'<@{interaction.user.id}> creates a GG\'Bot AI chat',
                                                            type=ChannelType.public_thread if public else ChannelType.private_thread
                                                            )
            await thread.edit(slowmode_delay=config['chat-delay'])
            await thread.add_user(interaction.user)

            config['threads'][str(thread.id)] = {
                'template' : template,
                'aimodel' : aimodel,
                'creator' : interaction.user.name,
                'creator-mention' : interaction.user.mention,
                'tags' : tags
            }

            async with self.db:
                await self.db.editExtensionConfig(interaction.guild, Extensions.AICHATBOT, config)
        except (ExtensionException, SlashCommandException) as e:
            await interaction.followup.send(embed=e.asEmbed())
        except DatabaseException as e:
            logger.error(str(e))
        else:
            await interaction.followup.send("Chat created successfully")

    @chat.subcommand('del',"Delete a chat with GG'sBot Ai")
    async def delchat(self, interaction : Interaction):
        try:
            await interaction.response.defer(ephemeral=True)

            async with self.db:
                config = await self.db.getExtensionConfig(interaction.guild,Extensions.AICHATBOT)

            if not str(interaction.channel.id) in config['threads']: raise SlashCommandException("Invalid Channel")

            await interaction.channel.delete()
            config['threads'].pop(str(interaction.channel.id))

            async with self.db:
                await self.db.editExtensionConfig(interaction.guild, Extensions.AICHATBOT, config)

        except (SlashCommandException, ExtensionException) as e:
            await interaction.followup.send(embed=e.asEmbed())
            logger.error(e)

    @commands.Cog.listener()
    async def on_message(self, message : Message):
        try:
            assert message.author != self.bot.user
            assert self.bot.user.mentioned_in(message) or any(role.name == self.bot.user.name for role in message.role_mentions)

            async with self.db:
                config = await self.db.getExtensionConfig(message.guild,Extensions.AICHATBOT)

            assert str(message.channel.id) in config['threads']

            template_name = config['threads'][str(message.channel.id)]['template']
            creator = config['threads'][str(message.channel.id)]['creator']
            creator_mention = config['threads'][str(message.channel.id)]['creator-mention']
            model = config['threads'][str(message.channel.id)]['aimodel']
            tags = config['threads'][str(message.channel.id)]['tags']

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
                        ]
                    }
                }
            ]

            if template_name:
                developer = await self.bot.fetch_user(os.environ['DEVELOPER_ID'])

                jinjaenv = Environment(loader=FileSystemLoader('data/chatbot-templates'),variable_start_string='{',variable_end_string='}')
                template = jinjaenv.get_template(template_name)
                template_content = template.render({
                    'name' : self.bot.user.name,
                    'discriminator' : self.bot.user.discriminator,
                    'developer' : developer.mention,
                    'creator_mention' : creator_mention,
                    'creator' : creator,
                    'tags' : tags,
                })

                data[0]['query']['messages'].append(
                    {
                        "role":  "system",
                        "content": template_content
                    }
                )

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

            assert content['success'], f"An error occurred in cloudflare API (code:{content['errors'][0]['code']}): {content['errors'][0]['message']}"

            result : str = content['result']['response']

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

        except AssertionError as e: pass
        except Exception as e:
            logger.error(e)

def setup(bot: commands.Bot):
    bot.add_cog(ChatBot(bot))