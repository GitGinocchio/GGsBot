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
from utils.exceptions import *

logger = getlogger()

txt2img_models = [
    "@cf/black-forest-labs/flux-1-schnell",
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

class ImageGeneration(commands.Cog):
    def __init__(self, bot : commands.Bot):
        self.dirfmt = './data/guilds/{guild_id}/commands.ai.ChatBot'
        self.bot = bot

    @slash_command('image', "Set of commands to manage and create Ai generated images")
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

            if not content['success']: raise CloudFlareAIException(code=content['errors'][0]['code'])

            b64image = content['result']['image']

            embed = Embed(
                title=f"Image generated by {interaction.user.name}",
                color=Color.green(),
                timestamp=datetime.now(timezone.utc)
            )
            embed.add_field(name="Model:", value=f"**{model}**", inline=True)
            embed.add_field(name="Diffusion Steps: ", value=steps, inline=True)
            embed.add_field(name="Prompt:", value=prompt[:1021] + '...' if len(prompt) > 1024 else prompt, inline=False)
            embed.set_footer(
                text=f"Generated by {self.bot.user.name} powered by Cloudflare Ai Workers", 
                icon_url="https://static-00.iconduck.com/assets.00/cloudflare-icon-512x512-c1lpcyo0.png"
            )
            embed.set_author(name=interaction.user.name,icon_url=interaction.user.avatar.url if interaction.user.avatar else interaction.user.default_avatar.url)

            await interaction.followup.send(embed=embed, file=File(io.BytesIO(base64.b64decode(b64image)), filename="image.png",description=f"Image generated by GGsBot", spoiler=spoiler))
        except CloudFlareAIException as e:
            await interaction.followup.send(embed=e.asEmbed())
            logger.error(e)
        except SlashCommandException as e:
            if e.code == 'Interaction Expired':
                await interaction.channel.send(embed=e.asEmbed())

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
                       interaction  : Interaction,
                       image : Attachment = SlashOption(name="image", description="The image to be described"),
                       image_url : str = SlashOption(name="imageurl", description="The url of the image to be described", required=False),
                       model : str = SlashOption(description="Model to be used for generating the image",required=False,choices=img2txt_models,default=img2txt_models[0]),
                       ephemeral : bool = SlashOption(description="Whether the response should be ephemeral or not",required=False,default=True)
                       ):
        try:
            await interaction.response.defer(ephemeral=ephemeral)

        except AssertionError as e:
            logger.error(e)
    """


def setup(bot : commands.Bot) -> None:
    bot.add_cog(ImageGeneration(bot))