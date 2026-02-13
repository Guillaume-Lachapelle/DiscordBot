"""Poll setup UI components."""

#region Imports

import discord
from typing import List, Optional

from .commands import MAX_POLL_OPTIONS, DURATION_OPTIONS, create_poll

#endregion


class PollDurationSelect(discord.ui.Select):
    """Dropdown to select poll duration."""

    def __init__(self, view: "PollSetupView"):
        options = []
        for label in DURATION_OPTIONS:
            options.append(
                discord.SelectOption(
                    label=label,
                    value=label,
                    default=DURATION_OPTIONS[label] == view.duration_hours,
                )
            )
        super().__init__(placeholder="Select duration", options=options)
        self.view_ref = view

    async def callback(self, interaction: discord.Interaction) -> None:
        selected = self.values[0]
        self.view_ref.duration_hours = DURATION_OPTIONS[selected]
        await interaction.response.defer(ephemeral=True)
        await self.view_ref.update_message(interaction)


class AddOptionModal(discord.ui.Modal):
    """Modal to add a single poll option."""

    def __init__(self, view: "PollSetupView"):
        super().__init__(title="Add poll option")
        self.view_ref = view
        self.option_input = discord.ui.TextInput(
            label="Option",
            placeholder="Enter an option",
            max_length=100,
        )
        self.add_item(self.option_input)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        option = str(self.option_input.value).strip()
        if not option:
            await interaction.response.send_message("Please enter a non-empty option.", ephemeral=True)
            return
        if len(self.view_ref.options) >= MAX_POLL_OPTIONS:
            await interaction.response.send_message("You already have 10 options.", ephemeral=True)
            return

        self.view_ref.options.append(option)
        await interaction.response.defer(ephemeral=True)
        await self.view_ref.update_message(interaction)


class PollCreateModal(discord.ui.Modal):
    """Initial poll creation modal."""

    def __init__(self):
        super().__init__(title="Create poll")
        self.question_input = discord.ui.TextInput(
            label="Question",
            placeholder="What is the question?",
            max_length=256,
        )
        self.add_item(self.question_input)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        question = str(self.question_input.value).strip()

        if not question:
            await interaction.response.send_message("Please provide a poll question.", ephemeral=True)
            return

        view = PollSetupView(question=question, options=[])
        embed = view.build_embed()
        await interaction.response.send_message(
            "Add options using the button below.",
            embed=embed,
            view=view,
            ephemeral=True,
        )
        view.message = await interaction.original_response()


class PollSetupView(discord.ui.View):
    """Interactive poll setup view."""

    def __init__(
        self,
        question: str,
        options: List[str],
        allow_multiselect: bool = False,
        duration_hours: int = 24,
    ) -> None:
        super().__init__(timeout=600)
        self.question = question
        self.options = options
        self.allow_multiselect = allow_multiselect
        self.duration_hours = duration_hours
        self.message: Optional[discord.Message] = None
        self.add_option_button = discord.ui.Button(
            label="Add option",
            style=discord.ButtonStyle.primary,
        )
        self.add_option_button.callback = self.add_option_callback
        self.toggle_button = discord.ui.Button(
            label="Toggle multiselect",
            style=discord.ButtonStyle.secondary,
        )
        self.toggle_button.callback = self.toggle_multiselect_callback
        self.create_button = discord.ui.Button(
            label="Create poll",
            style=discord.ButtonStyle.success,
        )
        self.create_button.callback = self.create_poll_callback
        self.cancel_button = discord.ui.Button(
            label="Cancel",
            style=discord.ButtonStyle.danger,
        )
        self.cancel_button.callback = self.cancel_callback
        self.refresh_items()

    def build_embed(self) -> discord.Embed:
        option_lines = [f"{idx + 1}. {option}" for idx, option in enumerate(self.options)]
        description = "\n".join(option_lines) if option_lines else "No options yet."
        embed = discord.Embed(title=self.question, description=description)
        embed.add_field(
            name="Duration",
            value=f"{self.duration_hours} hours",
            inline=True,
        )
        embed.add_field(
            name="Multiselect",
            value="On" if self.allow_multiselect else "Off",
            inline=True,
        )
        return embed

    def refresh_items(self) -> None:
        self.clear_items()
        self.add_item(PollDurationSelect(self))
        self.add_item(self.add_option_button)
        self.add_item(self.toggle_button)
        if len(self.options) >= 2:
            self.add_item(self.create_button)
        self.add_item(self.cancel_button)

    async def update_message(self, interaction: discord.Interaction) -> None:
        self.refresh_items()
        embed = self.build_embed()
        if self.message:
            await self.message.edit(embed=embed, view=self)
        elif interaction.message:
            await interaction.message.edit(embed=embed, view=self)

    async def on_timeout(self) -> None:
        for item in self.children:
            item.disabled = True
        if self.message:
            await self.message.edit(view=self)

    async def add_option_callback(self, interaction: discord.Interaction) -> None:
        if len(self.options) >= MAX_POLL_OPTIONS:
            await interaction.response.send_message("You already have 10 options.", ephemeral=True)
            return
        await interaction.response.send_modal(AddOptionModal(self))

    async def toggle_multiselect_callback(self, interaction: discord.Interaction) -> None:
        self.allow_multiselect = not self.allow_multiselect
        await interaction.response.defer(ephemeral=True)
        await self.update_message(interaction)

    async def create_poll_callback(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer(ephemeral=True)
        await create_poll(
            interaction,
            self.question,
            self.options,
            allow_multiselect=self.allow_multiselect,
            duration_hours=self.duration_hours,
            defer_response=False,
        )
        self.stop()
        if self.message:
            await self.message.edit(content="Poll created.", embed=None, view=None)

    async def cancel_callback(self, interaction: discord.Interaction) -> None:
        self.stop()
        await interaction.response.edit_message(content="Poll setup canceled.", embed=None, view=None)
