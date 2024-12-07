from nextcord import \
    Interaction,     \
    TextInputStyle,  \
    ButtonStyle,     \
    Embed,           \
    Member,          \
    WebhookMessage,  \
    PartialInteractionMessage, \
    File,            \
    Colour

from nextcord.ui import \
    Modal,              \
    View,               \
    TextInput,          \
    Button,             \
    button

from datetime import datetime, timezone, timedelta
from typing import Callable
import asyncio

from .ValorantQuizUtils import Levels, MapModes

class AnswerModal(Modal):
    def __init__(self, submit_callback : Callable[[Interaction, str], None]) -> None:
        Modal.__init__(self, "Valorant Quiz (Quess the map)")
        self.submit_callback = submit_callback

        self.user_input = TextInput(
            label="What is the map shown in the image?",
            placeholder="Type the map name here...",
            style=TextInputStyle.short,
            required=True
        )

        self.add_item(self.user_input)

    async def callback(self, interaction: Interaction):
        asyncio.create_task(self.submit_callback(interaction, self.user_input.value.strip().lower()))


class PreQuizView(View):
    def __init__(self, 
            on_cancel_callback : Callable[[Interaction], None], 
            on_leave_callback : Callable[[Interaction], None],
            on_join_callback : Callable[[Interaction], None],
            on_start_callback : Callable[[Interaction], None]
        ): 
        View.__init__(self, timeout=0)
        self.on_cancel_callback = on_cancel_callback
        self.on_leave_callback = on_leave_callback
        self.on_join_callback = on_join_callback
        self.on_start_callback = on_start_callback

    @button(label="Cancel", style=ButtonStyle.danger)
    async def cancel(self, button: Button, interaction : Interaction):
        await self.on_cancel_callback(interaction)

    @button(label="Leave", style=ButtonStyle.gray)
    async def leave(self, button: Button, interaction: Interaction):
        await self.on_leave_callback(interaction)

    @button(label="Join", style=ButtonStyle.secondary)
    async def join(self, button: Button, interaction: Interaction):
        await self.on_join_callback(interaction)

    @button(label="Start", style=ButtonStyle.primary)
    async def start(self, button: Button, interaction : Interaction):
        await self.on_start_callback(interaction)

class QuizView(View):
    def __init__(self, 
                 end_callback : Callable[[Interaction],None],
                 leave_callback : Callable[[Interaction],None],
                 skip_callback : Callable[[Interaction],None],
                 submit_callback : Callable[[Interaction, str], None]
        ) -> None:
        View.__init__(self, timeout=0)
        self.modal = AnswerModal(self.on_modal_submit)
        self.submit_callback = submit_callback
        self.end_callback = end_callback
        self.leave_callback = leave_callback
        self.skip_callback = skip_callback

    async def on_modal_submit(self, interaction : Interaction, answer : str):
        await self.submit_callback(interaction,answer)

    @button(label="End", style=ButtonStyle.red)
    async def end(self, button: Button, interaction: Interaction):
        await self.end_callback(interaction)

    @button(label="Leave", style=ButtonStyle.gray)
    async def leave(self, button: Button, interaction: Interaction):
        await self.leave_callback(interaction)

    @button(label="Skip", style=ButtonStyle.secondary)
    async def skip(self, button: Button, interaction: Interaction):
        await self.skip_callback(interaction)

    @button(label="Answer", style=ButtonStyle.primary)
    async def open_modal(self, button: Button, interaction: Interaction):
        await interaction.response.send_modal(self.modal)

class LeaderBoardView(View):
    def __init__(self, on_view_answers_callback : Callable[[Interaction],None]) -> None:
        View.__init__(self, timeout=0)
        self.on_view_answers_callback = on_view_answers_callback

    @button(label="View answers", style=ButtonStyle.primary)
    async def view_answers(self, button: Button, interaction: Interaction):
        await self.on_view_answers_callback(interaction)

class AllAnswersView(View):
    def __init__(self, 
                num_pages : int, 
                on_next_round_callback : Callable[[Interaction, int, WebhookMessage],None], 
                on_prev_round_callback : Callable[[Interaction, int, WebhookMessage],None]
            ) -> None:
        View.__init__(self, timeout=0)
        self.on_next_round_callback = on_next_round_callback
        self.on_prev_round_callback = on_prev_round_callback
        self.num_pages = num_pages
        self.message = None
        self.page = 1
    
    @button(label="Previous round", style=ButtonStyle.secondary)
    async def previous(self, button: Button, interaction: Interaction):
        if self.page > 1: 
            self.page -= 1
            await self.on_prev_round_callback(interaction, self.page, self.message)

    @button(label="Next round", style=ButtonStyle.secondary)
    async def next(self, button: Button, interaction: Interaction):
        if self.page < self.num_pages: 
            self.page += 1
            await self.on_next_round_callback(interaction, self.page, self.message)



class ErrorEmbed(Embed):
    def __init__(self, message : str):
        Embed.__init__(self, title="Error", description=message)
        self.colour = Colour.red()
        self.timestamp = datetime.now(timezone.utc)

class SuccessEmbed(Embed):
    def __init__(self, message : str):
        Embed.__init__(self, title="Success", description=message)
        self.colour = Colour.green()
        self.timestamp = datetime.now(timezone.utc)

class PreQuizEmbed(Embed):
    def __init__(self, author : Member, level : Levels, mode : MapModes, rounds : int, time_per_round : int):
        Embed.__init__(self)
        self.title = "Valorant Quiz (Guess the map)"
        self.description = "This quiz is designed to test your knowledge of Valorant maps. \n\n Please answer the questions as quickly and accurately as possible."
        self.color = Colour.green()

        self.set_author(name=author.display_name,icon_url=(author.avatar.url if author.avatar else author.default_avatar.url))

        self.add_field(name="Level", value=level, inline=True)

        self.add_field(name='Mode', value=mode, inline=True)

        self.add_field(name="Rounds", value=rounds, inline=True)

        minutes, seconds = divmod(timedelta(minutes=time_per_round).total_seconds(), 60)
        self.add_field(name='Time per round', value=f"{int(minutes):02}:{int(seconds):02}", inline=False)

        self.add_field(name="Participants", value="**No participants**", inline=False)

    def set_participants(self, participants : list[Member]):
        self.set_field_at(4, name="Participants", value=f"{','.join(participant.mention for participant in participants)}" if len(participants) > 0 else "**No participants**")

class QuizEmbed(Embed):
    def __init__(self, num_rounds : int):
        Embed.__init__(self)
        self.title = "Valorant Quiz (Guess the map)"
        self.description = "What is the map shown in the image?"
        self.timestamp = datetime.now(timezone.utc)
        self.colour = Colour.green()
        self.num_participants = 0
        self.num_answers = 0
        self.num_rounds = num_rounds
        self.round = 1

        self.start_time : datetime = datetime.now(timezone.utc)
        self.time_per_round = timedelta(minutes=0)

        self.add_field(name="Round", value=f'{self.round:03}/{self.num_rounds:03}', inline=True)

        self.add_field(name="Answers", value=f"000/000", inline=True)

        self.add_field(name='Time left', value=f"00:00", inline=True)

    def set_start_time(self):
        self.start_time = datetime.now(timezone.utc)

    def set_time_per_round(self, minutes : float):
        self.time_per_round = timedelta(minutes=minutes)

    def update_time_left(self):
        minutes, seconds = divmod((self.start_time + self.time_per_round - datetime.now(timezone.utc)).total_seconds(), 60)
        self.set_field_at(2, name="Time left", value=f"{int(minutes):02}:{int(seconds):02}")
        return minutes, seconds

    def set_round(self, round : int):
        self.round = round
        self.set_field_at(0, name=f"Round", value=f'{self.round:03}/{self.num_rounds:03}', inline=True)

    def set_num_participants(self, num : int):
        self.num_participants = num
        self.set_field_at(1,name="Answers",value=f"{self.num_answers:03}/{self.num_participants:03}")

    def set_num_answers(self, num : int):
        self.num_answers = num
        self.set_field_at(1,name="Answers",value=f"{num:03}/{self.num_participants:03}")

class LeaderBoardEmbed(Embed):
    def __init__(self, level : Levels, mode : MapModes, rounds : int, players : set, results : dict[int, dict]):
        Embed.__init__(self)
        self.title = "Valorant Quiz Leaderboard (Guess the map)"
        self.description = "Here is the leaderboard of the quiz on the maps of valorant, the results are ordered by the player who made the most correct answers"
        self.timestamp = datetime.now(timezone.utc)
        self.colour = Colour.green()

        self.add_field(name="Level", value=level, inline=True)
        self.add_field(name="Mode", value=mode, inline=True)
        self.add_field(name="Rounds", value=rounds, inline=True)

        player_scores : dict[Member, int] = {player:0 for player in players}

        for round_data in results.values():
            for player, answer in round_data.items():
                if player != "correct":
                    point = (1 if answer == round_data['correct'] else 0)

                    player_scores[player] += point
                    

        sorted_players = sorted(player_scores.items(), key=lambda x: x[1], reverse=True)

        leaderboard_str = "\n".join(f"{rank + 1}. {player.mention} - {score} points" for rank, (player, score) in enumerate(sorted_players))

        self.add_field(name="Leaderboard", value=leaderboard_str, inline=False)

class AllAnswersEmbed(Embed):
    def __init__(self, page : int, players : set,  results : dict[int, dict]):
        Embed.__init__(self)
        self.title = "Valorant Quiz Answers (Guess the map)"
        self.description = f"Here is a list of all the answers that users gave to the {page} round of Valorant map quiz"
        self.timestamp = datetime.now(timezone.utc)
        self.colour = Colour.green()

        self.add_field(name="Round", value=f'{page:03}/{len(results):03}', inline=True)

        value = results.get(page,{}).get('correct','**Not generated**')

        self.add_field(name=f"Correct Answer", value=value, inline=True)

        answers = '\n'.join(f'{n+1}. {player.mention} - {results.get(page,{}).get(player,"**No answer**")}' for n, player in enumerate(players))

        self.add_field(name=f"Players", value=answers,inline=False)

