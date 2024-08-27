from nextcord import Embed,Color,utils,channel,Permissions,Interaction
from nextcord.ext import commands
import nextcord
from langchain_ollama import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
import os

from utils.terminal import getlogger
from utils.jsonfile import JsonFile, _JsonDict

logger = getlogger()

templates = [template for template in os.listdir('./data/chatbot-templates')]

permissions = Permissions(
    administrator=True
)

class AiChatBot(commands.Cog):
    def __init__(self, bot : commands.Bot):
        self.dirfmt = './data/guilds/{guild_id}/' + AiChatBot.__name__
        self.bot = bot

    @nextcord.slash_command('aichatbot',"An AI chatbot developed with LLM (Large Language Model) by Ollama",default_member_permissions=permissions,dm_permission=False)
    async def aichatbot(self, interaction : nextcord.Interaction): pass

    @aichatbot.subcommand('setup',"Initialize GG'sBot Ai extension on this server")
    async def setup(self, 
                    interaction : nextcord.Interaction,
                    textchannel : nextcord.TextChannel = nextcord.SlashOption("textchannel","The text channel where the bot can be used and all public or private chats will be created",required=True),
                    delay : int = nextcord.SlashOption("delay","The number of seconds a user must wait after sending a message to the bot before sending another",required=True,default=0)
                ):
        await interaction.response.defer(ephemeral=True)
        workingdir = self.dirfmt.format(guild_id=interaction.guild.id)
        try:
            os.makedirs(workingdir,exist_ok=True)
        
            file = JsonFile(f'{workingdir}/config.json')
            file['aichatbot-text-channel'] = textchannel.id
            file['aichatbot-chat-delay'] = delay
            file['threads'] = _JsonDict({},file)
        
        except AssertionError as e:
            await interaction.followup.send(e)
        except OSError as e:
            await interaction.followup.send(f"Error occurred while creating directory: {e}", ephemeral=True)
        else:
            await interaction.followup.send('AiChatBot extension installed successfully')

    @aichatbot.subcommand('newchat',"Create a chat with GG'sBot Ai")
    async def newchat(self, 
                      interaction : nextcord.Interaction,
                      public : bool = nextcord.SlashOption('public','Whether the chat between you and the bot should be public or private',required=True,default=False),
                      aimodel : str = nextcord.SlashOption("aimodel","Choose the Artificial Intelligence model you want to use",required=True,choices=['llama3'],default='llama3'),
                      template : str | None = nextcord.SlashOption("template","Templates are used to get more specific answers for the type of context you want to get.",required=False,choices=templates,default=None)
                    ):
        await interaction.response.defer(ephemeral=True)
        workingdir = self.dirfmt.format(guild_id=interaction.guild.id)
        try:
            assert os.path.exists(f'{workingdir}/config.json'), "The AiChatBot extension is not configured on the server"
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
                "aimodel" : aimodel
                }
        except AssertionError as e:
            await interaction.followup.send(e)
        else:
            await interaction.followup.send("Chat created successfully")

    @aichatbot.subcommand('delchat',"Elimina una chat con GG'sBot Ai")
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
            workingdir = self.dirfmt.format(guild_id=message.guild.id)

            assert os.path.exists(f'{workingdir}/config.json')

            file = JsonFile(f'{workingdir}/config.json')
            assert str(message.channel.id) in file['threads']

            template = file['threads'][str(message.channel.id)]['template']
            model = file['threads'][str(message.channel.id)]['aimodel']

            with open(f'./data/chatbot-templates/{template}','r') as f:
                template_content = f.read()

            ollamaModel = OllamaLLM(model=model)
            chatPromptTemplate = ChatPromptTemplate.from_template(template_content)
            chain = chatPromptTemplate | ollamaModel
            
            context = []
            async for history_message in message.channel.history(limit=None):
                context_message = f"{history_message.created_at.isoformat()} {history_message.author.name}#{history_message.author.discriminator}: {history_message.clean_content}"
                context.append(context_message)
            context.reverse()

            response = await message.reply("Sto formulando una risposta...")

            developer = await self.bot.fetch_user(int(os.environ['DEVELOPER_ID']))

            result = chain.invoke({
                'name' : self.bot.user.name,
                'ai-discriminator' : self.bot.user.discriminator,
                'developer' : developer.name,
                'creator' : message.channel.owner.name,
                'tags' : "",
                'context' : '\n'.join(context), 
                'timestamp' : message.created_at.isoformat(),
                'username' : message.author.name,
                'discriminator' : message.author.discriminator,
                'question' : message.clean_content
            })

            result_sentences = result.split('\n')

            current_message = ''
            messages_sent = 0
            for sentence in result_sentences:
                if len(current_message) + len(sentence) + 1 <= 2000:  # +1 per il ritorno a capo
                    if current_message: current_message += '\n'
                    current_message += sentence
                else:
                    if messages_sent == 0:
                        await response.edit(current_message)
                    else:
                        await message.channel.send(current_message)
                    current_message = sentence
                    messages_sent+=1

            # Invia l'ultimo messaggio rimasto
            if messages_sent == 0 and current_message:
                await response.edit(current_message)
            elif current_message:
                await message.channel.send(current_message)

        except AssertionError as e:
            pass

def setup(bot: commands.Bot):
    bot.add_cog(AiChatBot(bot))