from nextcord.ext import commands
from nextcord import (
    ChannelType,
    TextChannel,
    SlashOption,
    Interaction,
    NotFound,
    Forbidden,
    HTTPException,
    Message,
    PartialEmoji,
    ButtonStyle,
    TextInputStyle,
    SelectOption,
    Embed,
    Colour,
    slash_command,
    message_command
)
from nextcord.ui import (
    View,
    Button, 
    Modal,
    TextInput,
    Select,
    button
)
from nextcord.abc import GuildChannel
from datetime import datetime, timezone
import traceback
import nextcord
import uuid

from utils.exceptions import GGsBotException
from utils.terminal import getlogger
from utils.commons import GLOBAL_INTEGRATION

logger = getlogger()

class EditContent(Modal):
    def __init__(self, editor: 'EmbedsEditor'):
        super().__init__(title="Edit Message Content", timeout=180)
        self.editor = editor
        self.content_input = TextInput(
            label="Content",
            placeholder="Enter the new message content (Markdown syntax is supported!)",
            style=TextInputStyle.paragraph,
            default_value=self.editor.message.content if self.editor.message else '',
            required=False
        )
        self.add_item(self.content_input)

    async def callback(self, interaction: Interaction):
        self.editor.message.content = self.content_input.value or ''
        self.stop()

class EditTitleDescription(Modal):
    def __init__(self, editor: 'EmbedsEditor', embed: Embed = None):
        super().__init__(title="Edit Title & Description", timeout=180)
        self.editor = editor
        self.embed = embed if embed else Embed()

        self.title_input = TextInput(
            label="Title",
            placeholder="Enter embed title",
            default_value=self.embed.title or "",
            required=False
        )
        self.desc_input = TextInput(
            label="Description",
            placeholder="Enter embed description (Markdown syntax is supported!)",
            style=TextInputStyle.paragraph,
            default_value=self.embed.description or "",
            required=False
        )

        self.add_item(self.title_input)
        self.add_item(self.desc_input)

    async def callback(self, interaction: Interaction):
        self.embed.title = self.title_input.value
        self.embed.description = self.desc_input.value

        await interaction.response.edit_message(embeds=[self.embed], view=self.editor)
        self.stop()

class EditImages(Modal):
    def __init__(self, editor: 'EmbedsEditor', embed: Embed):
        super().__init__(title="Edit Images", timeout=180)
        self.editor = editor
        self.embed = embed

        self.image_url = TextInput(
            label="Image URL",
            placeholder="URL for the main image",
            default_value=embed.image.url if embed.image else "",
            required=False
        )
        self.thumb_url = TextInput(
            label="Thumbnail URL",
            placeholder="URL for the thumbnail",
            default_value=embed.thumbnail.url if embed.thumbnail else "",
            required=False
        )

        self.add_item(self.image_url)
        self.add_item(self.thumb_url)

    async def callback(self, interaction: Interaction):
        self.embed.set_image(url=self.image_url.value or None)
        self.embed.set_thumbnail(url=self.thumb_url.value or None)

        await interaction.response.edit_message(embeds=[self.embed], view=self.editor)
        self.stop()

class EditAuthor(Modal):
    def __init__(self, editor: 'EmbedsEditor', embed: Embed):
        super().__init__(title="Edit Author", timeout=180)
        self.editor = editor
        self.embed = embed

        self.author_name = TextInput(
            label="Author Name",
            placeholder="The name of the author",
            default_value=embed.author.name if embed.author and embed.author.name else "",
            required=False
        )
        self.author_icon = TextInput(
            label="Author Icon URL",
            placeholder="The URL of the author icon",
            default_value=embed.author.icon_url if embed.author and embed.author.icon_url else "",
            required=False
        )

        self.add_item(self.author_name)
        self.add_item(self.author_icon)

    async def callback(self, interaction: Interaction):
        if self.author_name.value or self.author_icon.value:
            self.embed.set_author(
                name=self.author_name.value or None,
                icon_url=self.author_icon.value or None
            )
        else:
            self.embed.remove_author()

        await interaction.response.edit_message(embeds=[self.embed], view=self.editor)
        self.stop()

class EditFooter(Modal):
    def __init__(self, editor: 'EmbedsEditor', embed: Embed):
        super().__init__(title="Edit Footer", timeout=180)
        self.editor = editor
        self.embed = embed

        self.footer_text = TextInput(
            label="Footer Text",
            placeholder="The footer text",
            default_value=embed.footer.text if embed.footer and embed.footer.text else "",
            required=False
        )
        self.footer_icon = TextInput(
            label="Footer Icon URL",
            placeholder="The URL of the footer icon",
            default_value=embed.footer.icon_url if embed.footer and embed.footer.icon_url else "",
            required=False
        )

        self.add_item(self.footer_text)
        self.add_item(self.footer_icon)

    async def callback(self, interaction: Interaction):
        self.embed.set_footer(
            text=self.footer_text.value or None,
            icon_url=self.footer_icon.value or None
        )

        await interaction.response.edit_message(embeds=[self.embed])
        self.stop()

class EditColor(Modal):
    def __init__(self, editor: 'EmbedsEditor', embed: Embed):
        super().__init__(title="Edit Embed Color", timeout=180)
        self.editor = editor
        self.embed = embed

        self.color_input = TextInput(
            label="Hex Color (#RRGGBB)",
            placeholder="#7289DA",
            default_value=f"#{embed.color.value:06X}" if embed.color else "",
            required=False
        )

        self.add_item(self.color_input)

    async def callback(self, interaction: Interaction):
        value = self.color_input.value.strip()
        if value.startswith("#"):
            try:
                hex_value = int(value[1:], 16)
                self.embed.color = Colour(hex_value)
            except ValueError:
                self.embed.color = Colour.default()

        self.stop()

class EditEmbed(Modal):
    def __init__(self, editor: 'EmbedsEditor', embed: Embed = None):
        super().__init__(title="Edit Embed", timeout=180)
        self.editor = editor
        self.embed = embed if embed else Embed()

        # Campi della modale
        self.title_input = TextInput(
            label="Title",
            placeholder="The title of the embed",
            default_value=self.embed.title or "",
            required=False
        )
        self.desc_input = TextInput(
            label="Description",
            placeholder="The description of the embed",
            style=TextInputStyle.paragraph,
            default_value=self.embed.description or "",
            required=False
        )
        self.color_input = TextInput(
            label="Hex Color (#RRGGBB)",
            placeholder="The color hex value of the embed",
            default_value=f"#{self.embed.color.value:06X}" if self.embed.color else "",
            required=False
        )
        self.image_input = TextInput(
            label="URL Image",
            placeholder="The image URL of the embed",
            default_value=self.embed.image.url if self.embed.image else "",
            required=False
        )
        self.thumb_input = TextInput(
            label="URL Thumbnail",
            placeholder="The thumbnail URL of the embed",
            default_value=self.embed.thumbnail.url if self.embed.thumbnail else "",
            required=False
        )
        self.footer_text = TextInput(
            label="Footer Text",
            placeholder="The footer text",
            default_value=self.embed.footer.text if self.embed.footer and self.embed.footer.text else "",
            required=False
        )
        self.footer_icon = TextInput(
            label="Footer Icon URL",
            placeholder="The URL of the footer icon",
            default_value=self.embed.footer.icon_url if self.embed.footer and self.embed.footer.icon_url else "",
            required=False
        )
        self.author_name = TextInput(
            label="Author Name",
            placeholder="The name of the author",
            default_value=self.embed.author.name if self.embed.author and self.embed.author.name else "",
            required=False
        )
        self.author_icon = TextInput(
            label="Author Icon URL",
            placeholder="The URL of the author icon",
            default_value=self.embed.author.icon_url if self.embed.author and self.embed.author.icon_url else "",
            required=False
        )
        self.timestamp_input = TextInput(
            label="Add timestamp? (yes/no)",
            placeholder="Type 'yes' to include current time",
            default_value="yes" if self.embed.timestamp else "no",
            required=False
        )

        # Aggiungi tutti i campi
        for item in [
            self.title_input, self.desc_input, self.color_input,
            self.image_input, self.thumb_input,
            self.footer_text, self.footer_icon,
            self.author_name, self.author_icon,
            self.timestamp_input
        ]:
            self.add_item(item)

    async def callback(self, interaction: Interaction):
        self.embed.title = self.title_input.value
        self.embed.description = self.desc_input.value

        # Color
        if self.color_input.value.startswith("#"):
            try:
                hex_value = int(self.color_input.value[1:], 16)
                self.embed.color = Colour(hex_value)
            except ValueError:
                pass

        # Image & thumbnail
        self.embed.set_image(url=self.image_input.value or None)
        self.embed.set_thumbnail(url=self.thumb_input.value or None)

        # Footer
        if self.footer_text.value or self.footer_icon.value:
            self.embed.set_footer(text=self.footer_text.value or None, icon_url=self.footer_icon.value or None)
        else:
            self.embed.set_footer(text=None)

        # Author
        if self.author_name.value or self.author_icon.value:
            self.embed.set_author(name=self.author_name.value or None, icon_url=self.author_icon.value or None)
        else:
            self.embed.remove_author()

        # Timestamp
        if self.timestamp_input.value.lower() == "yes":
            from datetime import datetime
            self.embed.timestamp = datetime.utcnow()
        else:
            self.embed.timestamp = None

        await interaction.response.edit_message(embeds=[self.embed])
        self.stop()

class EmbedIndex(Select):
    def __init__(self, editor : 'EmbedsEditor'):
        self.buddy_select = SelectOption(label="No Embed", value="None", description="Create an embed first", default=True)
        Select.__init__(self, 
            placeholder="Select the embed you want to modify or delete",
            options=[self.buddy_select],
            row=0
        )
        self.editor = editor
        self.embed = None

    async def callback(self, interaction : Interaction):
        self.embed = self.values[0] if len(self.values) else None

        for option in self.options:
            if option.value == self.embed:
                option.default = True
            else:
                option.default = False

        await self.editor.update()

class EmbedsEditor(View):
    def __init__(self):
        View.__init__(self, timeout=None)
        self.embeds: dict[str, Embed] = {}
        self.message: Message | None = None

        self.embed_select = EmbedIndex(self)
        self.add_item(self.embed_select)

        # Edit Commands
        self.sc_button = Button(style=ButtonStyle.grey, label="Edit Content", row=1)
        self.sc_button.callback = self.edit_content
        self.add_item(self.sc_button)
    
        self.etd_button = Button(style=ButtonStyle.grey, disabled=True, label="Edit title & description", row=1)
        self.etd_button.callback = self.edit_td
        self.add_item(self.etd_button)

        self.ei_button = Button(style=ButtonStyle.grey, disabled=True, label="Edit images", row=1)
        self.ei_button.callback = self.edit_images
        self.add_item(self.ei_button)

        self.ea_button = Button(style=ButtonStyle.grey, disabled=True, label="Edit author", row=2)
        self.ea_button.callback = self.edit_author
        self.add_item(self.ea_button)

        self.ef_button = Button(style=ButtonStyle.grey, disabled=True, label="Edit footer", row=2)
        self.ef_button.callback = self.edit_footer
        self.add_item(self.ef_button)

        self.ec_button = Button(style=ButtonStyle.grey, disabled=True, label="Edit Color", row=2)
        self.ec_button.callback = self.edit_color
        self.add_item(self.ec_button)

        # Add / Remove / Send
        
        self.add_button = Button(style=ButtonStyle.green, label="Add Embed", row=3)
        self.add_button.callback = self.add_embed
        self.add_item(self.add_button)

        self.del_button = Button(style=ButtonStyle.danger, disabled=True, label="Remove Embed", row=3)
        self.del_button.callback = self.del_embed
        self.add_item(self.del_button)

        self.send_button = Button(style=ButtonStyle.primary, label="Send", row=3)
        self.send_button.callback = self.send
        self.add_item(self.send_button)

    async def from_existing_message(self, message : Message):
        if len(message.embeds) > 0:
            self.embed_select.options.clear()

        for embed in message.embeds:
            embed_id = uuid.uuid4().hex
            self.embeds[embed_id] = embed

            self.embed_select.add_option(
                label=embed.title if embed.title else "Embed without title",
                description=embed.description[:100] if embed.description else None,
                value=embed_id, 
                default=False
            )

        for input in [self.etd_button, self.ei_button, self.ea_button, self.ef_button,self.ec_button, self.del_button]:
            input.disabled = False

        if len(self.embed_select.options) > 0:
            self.embed_select.options[-1].default = True
            self.embed_select.embed = self.embed_select.options[-1].value

        self.message.content = message.content

        await self.update()

    # Edit fields

    async def edit_content(self, interaction : Interaction):
        try:
            edit_modal = EditContent(self)
            await interaction.response.send_modal(edit_modal)
            await edit_modal.wait()

            await self.update()
        except GGsBotException as e:
            await interaction.response.send_message(embed=e.asEmbed(), ephemeral=True, delete_after=5)

    async def edit_td(self, interaction : Interaction):
        try:
            if len(self.embed_select.options) == 1 and self.embed_select.embed == "None":
                raise GGsBotException(title="There are no embeds", description="Your message has no embeds")
            elif self.embed_select.embed == "None" or self.embed_select.embed == None:
                raise GGsBotException(title="Embed not selected", description="You must select an embed first")

            edit_modal = EditTitleDescription(self, self.embeds[self.embed_select.embed])
            await interaction.response.send_modal(edit_modal)
            await edit_modal.wait()

            await self.update()
        except GGsBotException as e:
            await interaction.response.send_message(embed=e.asEmbed(), ephemeral=True, delete_after=5)

    async def edit_images(self, interaction : Interaction):
        try:
            if len(self.embed_select.options) == 1 and self.embed_select.embed == "None":
                raise GGsBotException(title="There are no embeds", description="Your message has no embeds")
            elif self.embed_select.embed == "None" or self.embed_select.embed == None:
                raise GGsBotException(title="Embed not selected", description="You must select an embed first")

            edit_modal = EditImages(self, self.embeds[self.embed_select.embed])
            await interaction.response.send_modal(edit_modal)
            await edit_modal.wait()

            await self.update()
        except GGsBotException as e:
            await interaction.response.send_message(embed=e.asEmbed(), ephemeral=True, delete_after=5)

    async def edit_author(self, interaction : Interaction):
        try:
            if len(self.embed_select.options) == 1 and self.embed_select.embed == "None":
                raise GGsBotException(title="There are no embeds", description="Your message has no embeds")
            elif self.embed_select.embed == "None" or self.embed_select.embed == None:
                raise GGsBotException(title="Embed not selected", description="You must select an embed first")

            edit_modal = EditAuthor(self, self.embeds[self.embed_select.embed])
            await interaction.response.send_modal(edit_modal)
            await edit_modal.wait()

            await self.update()
        except GGsBotException as e:
            await interaction.response.send_message(embed=e.asEmbed(), ephemeral=True, delete_after=5)

    async def edit_footer(self, interaction : Interaction):
        try:
            if len(self.embed_select.options) == 1 and self.embed_select.embed == "None":
                raise GGsBotException(title="There are no embeds", description="Your message has no embeds")
            elif self.embed_select.embed == "None" or self.embed_select.embed == None:
                raise GGsBotException(title="Embed not selected", description="You must select an embed first")

            edit_modal = EditFooter(self, self.embeds[self.embed_select.embed])
            await interaction.response.send_modal(edit_modal)
            await edit_modal.wait()

            await self.update()
        except GGsBotException as e:
            await interaction.response.send_message(embed=e.asEmbed(), ephemeral=True, delete_after=5)

    async def edit_color(self, interaction : Interaction):
        try:
            if len(self.embed_select.options) == 1 and self.embed_select.embed == "None":
                raise GGsBotException(title="There are no embeds", description="Your message has no embeds")
            elif self.embed_select.embed == "None" or self.embed_select.embed == None:
                raise GGsBotException(title="Embed not selected", description="You must select an embed first")

            edit_modal = EditColor(self, self.embeds[self.embed_select.embed])
            await interaction.response.send_modal(edit_modal)
            await edit_modal.wait()

            await self.update()
        except GGsBotException as e:
            await interaction.response.send_message(embed=e.asEmbed(), ephemeral=True, delete_after=5)   

    # Add / Delete / Send

    async def add_embed(self, interaction : Interaction):
        try:
            if len(self.embeds) >= 10:
                raise GGsBotException(
                    title="Max number of embeds reached",
                    description="You reach the limit of 10 embeds in a single message",
                    suggestions="Remove some embeds or create another message and try again"
                )
            
            modal = EditTitleDescription(self)
            await interaction.response.send_modal(modal)
            await modal.wait()

            option_id = uuid.uuid4().hex
            self.embeds[option_id] = modal.embed

            if self.embed_select.buddy_select in self.embed_select.options:
                self.embed_select.options.remove(self.embed_select.buddy_select)

            for option in self.embed_select.options:
                option.default = False

            self.embed_select.add_option(
                label=modal.embed.title if modal.embed.title else "Embed without title",
                description=modal.embed.description[:100] if modal.embed.description else None,
                value=option_id, 
                default=True
            )

            for input in [self.etd_button, self.ei_button, self.ea_button, self.ef_button,self.ec_button, self.del_button]:
                input.disabled = False

            self.embed_select.embed = option_id

            await self.update()
        except GGsBotException as e:
            await interaction.response.send_message(embed=e.asEmbed(), ephemeral=True, delete_after=5)

    async def del_embed(self, interaction : Interaction):
        try:
            if len(self.embed_select.options) == 1 and self.embed_select.embed == "None":
                raise GGsBotException(title="There are no embeds", description="Your message has no embeds")
            elif self.embed_select.embed == "None" or self.embed_select.embed == None:
                raise GGsBotException(title="Embed not selected", description="You must select an embed first")
            
            for option in self.embed_select.options:
                if option.value == self.embed_select.embed:
                    self.embed_select.options.remove(option)
                    self.embeds.pop(self.embed_select.embed)
                    break

            if len(self.embed_select.options) == 0:
                for input in [self.etd_button, self.ei_button, self.ea_button, self.ef_button,self.ec_button, self.del_button]:
                    input.disabled = True

                self.embed_select.buddy_select.default = True
                self.embed_select.options.append(self.embed_select.buddy_select)
                self.embed_select.embed = 'None'
            else:
                self.embed_select.options[0].default = True
                self.embed_select.embed = self.embed_select.options[0].value

            await self.update()
        except GGsBotException as e:
            await interaction.response.send_message(embed=e.asEmbed(), ephemeral=True, delete_after=5)

    async def send(self, interaction : Interaction):
        try:
            avatar = interaction.user.avatar if interaction.user.avatar else interaction.user.default_avatar
            webhook = await interaction.channel.create_webhook(
                name=interaction.user.display_name,
                avatar=avatar,
                reason="A user requested the bot to send a message as if it were him"
            )

            await webhook.send(
                content=self.message.content,
                embeds=self.embeds.values(),
                username=interaction.user.display_name,
                avatar_url=avatar.url,
            )

            await webhook.delete()

            await self.message.delete()
        except Exception as e:
            logger.error(traceback.format_exc())
        except GGsBotException as e:
            await interaction.response.send_message(embed=e.asEmbed(), ephemeral=True, delete_after=5)

    # Start / Update

    async def start(self, interaction: Interaction):
        self.message = await interaction.followup.send(
            content="-# Add embeds, fields, contents, attachments with the buttons below",
            embeds=self.embeds,
            view=self,
            ephemeral=True
        )

    async def update(self):
        if not self.message:
            return
        
        #self.refresh(self.to_components())
        await self.message.edit(
            content=self.message.content,
            embeds=self.embeds.values(), 
            view=self
        )



class Messages(commands.Cog):
    def __init__(self, bot : commands.Bot):
        commands.Cog.__init__(self)
        self.bot = bot

    @message_command(name="edit", integration_types=GLOBAL_INTEGRATION)
    async def edit(self, interaction : Interaction, message  : nextcord.Message):
        try:
            await interaction.response.defer(ephemeral=True)

            editor = EmbedsEditor()
            await editor.start(interaction)
            await editor.from_existing_message(message)
        except Exception as e:
            logger.error(traceback.format_exc())

    @slash_command(description="Set of commands to manage messages")
    async def message(self, interaction: Interaction): pass

    @message.subcommand(description="Create a new message with embeds, fields and attachments.")
    async def new(self, interaction : Interaction):
        try:
            await interaction.response.defer(ephemeral=True)

            editor = EmbedsEditor()
            await editor.start(interaction)

        except Exception as e:
            logger.error(traceback.format_exc())
    
    @message.subcommand(description="Clone a message with its embeds and file attachments.")
    async def copy(self, 
            interaction : Interaction,
            message_id : str = SlashOption(description="The ID of the message you want to copy.", required=True, max_length=20, min_length=1),
            channel : GuildChannel = SlashOption(
                description="The text channel containing the message to copy.",
                channel_types=[ChannelType.forum, ChannelType.group, ChannelType.news, ChannelType.private, 
                               ChannelType.private_thread, ChannelType.public_thread, ChannelType.text],
                default=None
            )
        ):
        try:
            await interaction.response.defer(ephemeral=True)

            if not message_id.isnumeric():
                raise GGsBotException(
                    title="Invalid message id",
                    description="You must pass a valid message id",
                    suggestions="Pass a valid message id and try again"
                )

            if not channel: channel = interaction.channel

            message : Message = await channel.fetch_message(message_id)

            editor = EmbedsEditor()
            await editor.start(interaction)
            await editor.from_existing_message(message)

        except GGsBotException as e:
            await interaction.followup.send(embed=e.asEmbed(), ephemeral=True)
        except HTTPException as e:
            await interaction.followup.send(embed=GGsBotException(
                title=f"An unexpected error occurred",
                description=e.text,
                suggestions="try again or contact a moderator."
            ).asEmbed(), ephemeral=True)
        except Forbidden as e:
            await interaction.followup.send(embed=GGsBotException(
                title="Missing permissions",
                description="You do not have the permissions required to get a message",
                suggestions="Make sure to have the permissions required and try again."
            ).asEmbed(), ephemeral=True)
        except NotFound as e:
            await interaction.followup.send(embed=GGsBotException(
                title="Message not found",
                description="The specified message was not found.",
                suggestions="Make sure to copy an existing message and try again."
            ).asEmbed(), ephemeral=True)
        except Exception as e:
            logger.error(traceback.format_exc())

def setup(bot : commands.Bot):
    bot.add_cog(Messages(bot))