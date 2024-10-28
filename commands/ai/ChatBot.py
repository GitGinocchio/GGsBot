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
        Message, \
        Attachment, \
        AttachmentFlags, \
        File
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
from utils.jsonfile import JsonFile, _JsonDict

logger = getlogger()

templates = [template for template in os.listdir('./data/chatbot-templates')]

txt2txt_models = [
    '@cf/meta/llama-3-8b-instruct',
    '@hf/thebloke/llama-2-13b-chat-awq',
    '@cf/mistral/mistral-7b-instruct-v0.1',
    '@hf/google/gemma-7b-it',
    '@hf/nexusflow/starling-lm-7b-beta',
    '@cf/tinyllama/tinyllama-1.1b-chat-v1.0',
]

txt2img_models = [
    #"@cf/runwayml/stable-diffusion-v1-5-inpainting",
    "@cf/black-forest-labs/flux-1-schnell",
    #"@cf/bytedance/stable-diffusion-xl-lightning",
    #"@cf/lykon/dreamshaper-8-lcm",
    #"@cf/stabilityai/stable-diffusion-xl-base-1.0",
    #"@cf/runwayml/stable-diffusion-v1-5-img2img"
]

img2img_models = [
    "@cf/runwayml/stable-diffusion-v1-5-inpainting",
    "@cf/runwayml/stable-diffusion-v1-5-img2img",
    "@cf/bytedance/stable-diffusion-xl-lightning",
    "@cf/stabilityai/stable-diffusion-xl-base-1.0"
]

img2txt_models = [
    "@cf/llava-hf/llava-1.5-7b-hf",
    "@cf/unum/uform-gen2-qwen-500m"
]

permissions = Permissions(
    use_slash_commands=True
    #administrator=True
)


class ChatBot(commands.Cog):
    def __init__(self, bot : commands.Bot):
        self.dirfmt = './data/guilds/{guild_id}/commands.ai.ChatBot'
        self.bot = bot

    @slash_command('ai',"An AI chatbot powered by LLMs (Large Language Models)",default_member_permissions=permissions,dm_permission=False)
    async def ai(self, interaction : Interaction): pass

    @ai.subcommand('chat',"Set of commands to manage Ai chats")
    async def chat(self, interaction : Interaction): pass

    @chat.subcommand('new',"Create a chat with GG'sBot Ai")
    async def newchat(self, 
                      interaction : Interaction,
                      public : bool = SlashOption('public','Whether the chat between you and the bot should be public or private',required=True,default=False),
                      aimodel : str = SlashOption("aimodel","Choose the Artificial Intelligence model you want to use",required=True,choices=txt2txt_models,default='@cf/meta/llama-3-8b-instruct'),
                      template : str | None = SlashOption("template","Templates are used to get more specific answers for the type of context you want to get.",required=False,choices=templates,default=None),
                      tags: str = SlashOption("tags","Write separated comma Tags used to get more specific answers",required=False,default=''),
                    ):
        await interaction.response.defer(ephemeral=True)
        workingdir = self.dirfmt.format(guild_id=interaction.guild.id)
        try:
            assert os.path.exists(f'{workingdir}/config.json'), "The ChatBot extension is not configured on the server"
            file = JsonFile(f'{workingdir}/config.json')

            assert interaction.channel.id == int(file['aichatbot-text-channel']), f"You can create an Ai chat only in the channel <@{file['aichatbot-text-channel']}>"

            thread : Thread = await interaction.channel.create_thread(
                                                            name="New Chat",
                                                            reason=f'<@{interaction.user.id}> creates a GG\'Bot AI chat',
                                                            type=ChannelType.public_thread if public else ChannelType.private_thread
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

    @chat.subcommand('del',"Delete a chat with GG'sBot Ai")
    async def delchat(self, interaction : Interaction):
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

    @ai.subcommand('ask',description="Ask a question to GG'sBot AI")
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
            assert content['success'], f"An error occurred in cloudflare API (code:{content['errors'][0]['code']}): {content['errors'][0]['message']}"
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
        except AssertionError as e:
            logger.error(e)

    @ai.subcommand('image', "Set of commands to manage and create Ai generated images")
    async def image(self, interaction : Interaction): pass

    @image.subcommand('fromtext', "Generate an image from a prompt")
    async def fromtext(self, 
                       interaction : Interaction,
                       prompt : str =  SlashOption(description="A text description of the image you want to generate",required=True,min_length=1),
                       model : str = SlashOption(description="Model to be used for generating the image",required=False,choices=txt2img_models,default=txt2img_models[0]),
                       steps : int = SlashOption(description="Number of diffusion steps, higher values can improve quality but take longer (min: 1 max: 8 def:4)",required=False,default=4, min_value=1, max_value=8),
                       ephemeral : bool = SlashOption(description="Whether the response should be ephemeral or not",required=False,default=True),
                       spoiler : bool = SlashOption(description="Whether the generated image should be a spoiler or not",required=False,default=False),
                       ):
        try:
            await interaction.response.defer(ephemeral=ephemeral)

            url = f"https://api.cloudflare.com/client/v4/accounts/{os.environ['CLOUDFLARE_ACCOUNT_ID']}/ai/run/{model}"
            headers = { "Authorization": f"Bearer {os.environ['CLOUDFLARE_API_KEY']}", 'Content-Type': 'application/json' }
            data = { "prompt" : prompt, "steps" : steps}

            content = requests.post(url, headers=headers, json=data).json()
            assert content['success'], f"An error occurred in cloudflare API (code:{content['errors'][0]['code']}): {content['errors'][0]['message']}"
            b64image = content['result']['image']

            embed = Embed(
                title=f"Image generated by {interaction.user.name}",
                color=Color.green(),
                timestamp=datetime.now(timezone.utc)
            )
            embed.add_field(name="Model:", value=f"**{model}**", inline=True)
            embed.add_field(name="Diffusion Steps: ", value=steps, inline=True)
            embed.add_field(name="Prompt:", value=prompt, inline=False)
            embed.set_footer(
                text=f"Generated by {self.bot.user.name} powered by Cloudflare Ai Workers", 
                icon_url="https://static-00.iconduck.com/assets.00/cloudflare-icon-512x512-c1lpcyo0.png"
            )
            embed.set_author(name=interaction.user.name,icon_url=interaction.user.avatar.url if interaction.user.avatar else interaction.user.default_avatar.url)

            await interaction.followup.send(embed=embed, file=File(io.BytesIO(base64.b64decode(b64image)), filename="image.png",description=f"Image generated by GGsBot", spoiler=spoiler))
        except AssertionError as e:
            logger.error(e)

    """
    @image.subcommand('fromimage', "Generate an image from another image and/or from a prompt")
    async def fromimage(self,
                       interaction : Interaction,
                       image : Attachment = SlashOption("image",description="The image to be used as a base for the generated image",required=True),
                       prompt : str =  SlashOption(description="A text description of the image you want to generate",required=True,min_length=1),
                       negativeprompt : str = SlashOption(description="Text describing elements to avoid in the generated image",required=False),
                       height : int = SlashOption(description="Height of the generated image. Default is 512",required=False,default=512, min_value=256, max_value=2048),
                       width : int = SlashOption(description="Width of the generated image. Default is 512",required=False,default=512,min_value=256,max_value=2048),
                       steps : int = SlashOption(description="The number of diffusion steps; higher values can improve quality but take longer",required=False,default=20, min_value=1, max_value=20),
                       guidance : float = SlashOption(description="Controls how closely the generated image should adhere to the prompt",required=False,default=7.5, min_value=0.0,max_value=10),
                       seed : int = SlashOption(description="Random seed for reproducibility of the image generation",required=False, default=None),
                       model : str = SlashOption(description="The model to be used for generating the image",required=False,choices=img2img_models,default=img2img_models[0]),
                       ephemeral : bool = SlashOption(description="Whether the response should be ephemeral or not",required=False,default=True),
                       ):
        try:
            await interaction.response.defer(ephemeral=ephemeral)

            print(image.content_type)
            assert image.content_type == 'image/png', "Image must be a png image"

            image_bytes = await image.read()
            PIL_image = Image.open(io.BytesIO(image_bytes))

            mask_array = []
            image_array = []

            url = f"https://api.cloudflare.com/client/v4/accounts/{os.environ['CLOUDFLARE_ACCOUNT_ID']}/ai/run/{model}"
            headers = {
                "Authorization": f"Bearer {os.environ['CLOUDFLARE_API_KEY']}",
                'Content-Type': 'application/json'
            }

            data = {
                "prompt": prompt,
                #"guidance": guidance,
                #"num_steps": steps,
                "mask" : mask_array,
                "image" : image_array,
                "image_b64": base64.b64encode(image_bytes).decode(),
                "width": width,
                "height": height
            }
            if negativeprompt: data["negative_prompt"] = negativeprompt
            if seed: data['seed'] = seed

            print(data.keys())

            content = requests.post(url, headers=headers, json=data).json()
            assert content['success'], f"An error occurred in cloudflare API (code:{content['errors'][0]['code']}): {content['errors'][0]['message']}"

            b64image = content['result']['image']

            await interaction.followup.send(content=f"{prompt}:",file=File(io.BytesIO(base64.b64decode(b64image)),'image.png',description=f"Image generated by GGsBot"))

        except AssertionError as e:
            logger.error(e)
    """

    """
    @image.subcommand('describe', "Describes an image")
    async def describe(self, 
                       interaction  : Interaction
                       ):
        try:
            await interaction.response.defer(ephemeral=ephemeral)
        except AssertionError as e:
            logger.error(e)
    """

    @commands.Cog.listener()
    async def on_message(self, message : Message):
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

def setup(bot: commands.Bot):
    bot.add_cog(ChatBot(bot))