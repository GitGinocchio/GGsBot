from nextcord import \
    Interaction,     \
    TextInputStyle,  \
    ButtonStyle,     \
    Embed,           \
    Member,          \
    WebhookMessage,  \
    Colour,          \
    File

from nextcord.ui import \
    Modal,              \
    View,               \
    TextInput,          \
    Button,             \
    button

from uuid import uuid4
from io import BytesIO
from PIL import Image
import traceback
import asyncio
import random

from .ValorantQuizUtils import \
    Levels,                    \
    MapModes,                  \
    ImageTypes,                \
    asyncget,                  \
    transform_coordinates
from .ValorantQuizUi import \
    AllAnswersEmbed,        \
    AllAnswersView,         \
    LeaderBoardEmbed,       \
    LeaderBoardView,        \
    ErrorEmbed,             \
    SuccessEmbed,           \
    PreQuizEmbed,           \
    PreQuizView,            \
    QuizEmbed,              \
    QuizView                \

class QuizSession(object): pass

class MapQuizSession(QuizSession):
    def __init__(self, level : Levels, mode : MapModes, num_rounds : int, time_per_round : float, deathmatch_maps: bool, cache : dict, interaction : Interaction) -> None:
        QuizSession.__init__(self)
        self.interaction = interaction
        self.owner = interaction.user
        self.cache = cache
        self.level = level
        self.mode = mode
        self.id = uuid4()

        self.players = set()
        self.time_per_round = time_per_round
        self.deathmatch_maps = deathmatch_maps

        if deathmatch_maps:
            self.maps = [(num, map) for num, map in enumerate(self.cache['maps'])] 
        else:
            self.maps = [(num, map) for num, map in enumerate(self.cache['maps']) if map['displayName'].lower() not in ['kasbah','district','drift','piazza','glitch']]

        if self.level == Levels.PRO:
            filtered_maps = [num for (num, map) in self.maps if (map['callouts'] if self.mode == MapModes.FRAGMENT else True) and map['displayIcon']]
            if num_rounds <= len(filtered_maps):
                self.maps : list[int] = random.sample([num for num in filtered_maps],k=num_rounds)
                self.num_rounds = num_rounds
            else:
                self.maps : list[int] = random.choices([num for num in filtered_maps],k=num_rounds)
                self.num_rounds = num_rounds
        else:
            self.num_rounds = num_rounds if num_rounds <= (len_maps:=len(self.maps)) else len_maps
            self.maps : list[int] = random.sample([num for num, map in self.maps],k=self.num_rounds)

        self.current_round : int = 0
        self.num_submits : int = 0

        self.results : dict[int, dict] = {}

        self.preQuizView = PreQuizView(self.on_cancel_quiz,self.on_leave_quiz,self.on_player_joined,self.on_start_quiz)
        self.preQuizEmbed = PreQuizEmbed(author=self.owner, level=self.level, mode=self.mode, rounds=self.num_rounds, time_per_round=time_per_round)
    
        self.quizView = QuizView(self.on_end_quiz, self.on_leave_during_quiz, self.on_skip_map, self.on_player_submit)
        self.quizEmbed = QuizEmbed(self.num_rounds)
        self.time_left_task : asyncio.Task = None

        self.leaderboardView = LeaderBoardView(self.on_view_answers)

    # --- pre quiz ---

    async def on_cancel_quiz(self, interaction : Interaction):
        if interaction.user.id != self.owner.id:
            await interaction.response.send_message(embed=ErrorEmbed("Only the **owner** of the quiz can cancel it"), delete_after=5, ephemeral=True)
            return

        await self.interaction.delete_original_message()

    async def on_leave_quiz(self, interaction : Interaction):
        if interaction.user not in self.players:
            await interaction.response.send_message(embed=ErrorEmbed("You cannot quit a quiz you are not part of."), delete_after=5, ephemeral=True)
            return
        
        self.players.discard(interaction.user)
        self.preQuizEmbed.set_participants(self.players)

        await self.interaction.edit_original_message(embed=self.preQuizEmbed)

    async def on_player_joined(self, interaction : Interaction):
        if interaction.user in self.players:
            await interaction.response.send_message(embed=ErrorEmbed("You are already in the quiz!"), delete_after=5, ephemeral=True)
            return

        self.players.add(interaction.user)
        self.preQuizEmbed.set_participants(self.players)

        await self.interaction.edit_original_message(embed=self.preQuizEmbed)

    async def on_start_quiz(self, interaction : Interaction):
        if len(self.players) == 0:
            await interaction.response.send_message(embed=ErrorEmbed("You can't start a quiz without participants"), delete_after=5, ephemeral=True)
            return
        elif interaction.user.id != self.owner.id:
            await interaction.response.send_message(embed=ErrorEmbed("Only the **owner** of the quiz can start it"), delete_after=5, ephemeral=True)
            return
        
        await self._next_round()

    # --- quiz ---

    async def _next_round(self):
        try:
            if self.current_round >= self.num_rounds or len(self.players) == 0:
                await self._end_quiz()
                return
            
            image_types = list(ImageTypes)
            self.current_round += 1
            self.num_submits = 0

            self.results[self.current_round] = {'correct' : self.cache['maps'][self.maps[self.current_round-1]]['displayName'].lower()}

            if self.level == Levels.RANDOM:
                key : ImageTypes = random.choice(image_types)
            else:
                key = ImageTypes[self.level.name]

            img_url = self.cache['maps'][self.maps[self.current_round-1]][key.value]
            callouts = self.cache['maps'][self.maps[self.current_round-1]]['callouts']
            
            
            if key == ImageTypes.PRO and self.mode == MapModes.FRAGMENT and callouts and img_url:
                img_data = await asyncget(img_url, mimetype='image/png')
                ImageBytesIO = BytesIO(img_data)

                callout = random.choice(callouts)
                xCallout = callout['location']['x']
                yCallout = callout['location']['y']
                xMultiplier = self.cache['maps'][self.maps[self.current_round-1]]['xMultiplier']
                yMultiplier = self.cache['maps'][self.maps[self.current_round-1]]['yMultiplier']
                xScalar = self.cache['maps'][self.maps[self.current_round-1]]['xScalarToAdd']
                yScalar = self.cache['maps'][self.maps[self.current_round-1]]['yScalarToAdd']

                x, y = transform_coordinates(xCallout,yCallout,xMultiplier,yMultiplier,xScalar,yScalar)
                
                box = (x,y, 500, 500)
                cropped = Image.open(ImageBytesIO).crop(box)
                ImageBytesIO = BytesIO()
                cropped.save(ImageBytesIO, format='PNG')
                ImageBytesIO.seek(0)

                img_file = File(ImageBytesIO, filename="map.png", force_close=True)
                self.quizEmbed.set_image(url='attachment://map.png')
            elif img_url is None:
                image_types.remove(ImageTypes.PRO)
                key : ImageTypes = random.choice(image_types)
                img_url = self.cache['maps'][self.maps[self.current_round-1]][key.value]
                self.quizEmbed.set_image(url=img_url)
                img_file = None
            else:
                self.quizEmbed.set_image(url=img_url)
                img_file = None

            self.quizEmbed.set_num_participants(len(self.players))
            self.quizEmbed.set_num_answers(0)

            self.quizEmbed.set_start_time()
            self.quizEmbed.set_time_per_round(self.time_per_round)

            self.quizEmbed.set_round(self.current_round)

            if img_file:
                await self.interaction.edit_original_message(embed=self.quizEmbed, view=self.quizView, file=img_file, attachments=[])
            else:
                await self.interaction.edit_original_message(embed=self.quizEmbed, view=self.quizView, attachments=[])

            if self.time_left_task: self.time_left_task.cancel()

            self.time_left_task = asyncio.create_task(self._update_time_left_task())
        except Exception as e:
            print('\n'.join(traceback.format_exception(e)))

    async def _end_quiz(self):
        self.time_left_task.cancel()

        await self.interaction.edit_original_message(embed=LeaderBoardEmbed(self.level,self.mode,self.num_rounds, self.players, self.owner, self.results), view=self.leaderboardView, attachments=[])

    async def _update_time_left_task(self):
        minutes, seconds = self.quizEmbed.update_time_left()

        while (minutes >= 0 and seconds >= 0) and self.num_submits < (len_players:=len(self.players)) and len_players > 0:
            await self.interaction.edit_original_message(embed=self.quizEmbed, view=self.quizView)
        
            await asyncio.sleep(0.7)
            
            minutes, seconds = self.quizEmbed.update_time_left()

        # Tempo terminato o tutti hanno risposto
        await self._next_round()

    async def on_end_quiz(self, interaction : Interaction):
        if interaction.user.id != self.owner.id:
            await interaction.response.send_message(embed=ErrorEmbed("Only the **owner** of the quiz can end it"), delete_after=5, ephemeral=True)
            return
        
        await self._end_quiz()

    async def on_leave_during_quiz(self, interaction : Interaction):
        if interaction.user not in self.players:
            await interaction.response.send_message(embed=ErrorEmbed("You cannot leave a quiz you are not part of."), delete_after=5, ephemeral=True)
            return
        
        self.players.discard(interaction.user)
        self.preQuizEmbed.set_participants(self.players)

        await self.interaction.edit_original_message(embed=self.preQuizEmbed)

    async def on_skip_map(self, interaction : Interaction):
        if interaction.user in self.results[self.current_round]:
            await interaction.followup.send(embed=ErrorEmbed("You have already skipped this map or submitted an answer"), delete_after=5, ephemeral=True)
            return
        elif interaction.user not in self.players:
            await interaction.followup.send(embed=ErrorEmbed("You are not part of this quiz"), delete_after=5, ephemeral=True)
            return
        
        self.results[self.current_round][interaction.user] = "**Skipped**"

        self.quizEmbed.set_num_answers(len(self.results[self.current_round]) - 1)

        await self.interaction.edit_original_message(embed=self.quizEmbed, view=self.quizView)

        self.num_submits += 1

    async def on_player_submit(self, interaction : Interaction, answer : str):
        if interaction.user in self.results[self.current_round]:
            await interaction.followup.send(embed=ErrorEmbed("You have already skipped this map or submitted an answer"), delete_after=5, ephemeral=True)
            return
        elif interaction.user not in self.players:
            await interaction.followup.send(embed=ErrorEmbed("You are not part of this quiz"), delete_after=5, ephemeral=True)
            return
        
        self.results[self.current_round][interaction.user] = answer

        self.quizEmbed.set_num_answers(len(self.results[self.current_round]) - 1)

        await self.interaction.edit_original_message(embed=self.quizEmbed, view=self.quizView)

        self.num_submits += 1

        #await interaction.followup.send(embed=SuccessEmbed(f"{interaction.user.mention} you have submitted your answer!"), delete_after=5, ephemeral=True)

    # --- after quiz ---

    async def on_view_answers(self, interaction : Interaction):
        view = AllAnswersView(self.num_rounds, self.on_next_round, self.on_prev_round)
        message = await interaction.response.send_message(embed=AllAnswersEmbed(1, self.players, self.results), view=view, ephemeral=True)
        view.message = message

    async def on_next_round(self, interaction : Interaction, page : int, message : WebhookMessage):
        await message.edit(embed=AllAnswersEmbed(page, self.players, self.results))

    async def on_prev_round(self, interaction : Interaction, page : int, message : WebhookMessage):
        await message.edit(embed=AllAnswersEmbed(page, self.players ,self.results))

    # --- hook ---

    async def start(self) -> tuple[Embed, View]:
        return self.preQuizEmbed, self.preQuizView