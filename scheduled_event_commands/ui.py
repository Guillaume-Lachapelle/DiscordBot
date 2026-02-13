"""Scheduled event setup UI components."""

#region Imports

import datetime
from typing import Dict, List, Optional

import discord

from . import repository, service

#endregion


#region Helpers

def _parse_event_time(event_time_str: str) -> datetime.datetime:
    return datetime.datetime.fromisoformat(event_time_str)

#endregion


#region Modals

class ScheduledEventCreateModal(discord.ui.Modal):
    """Modal to create a scheduled event."""

    def __init__(self):
        super().__init__(title="Create scheduled event")
        now = datetime.datetime.now()
        self.title_input = discord.ui.TextInput(
            label="Title",
            placeholder="Event title",
            max_length=100,
        )
        self.date_input = discord.ui.TextInput(
            label="Date (YYYY-MM-DD)",
            placeholder=now.strftime("%Y-%m-%d"),
            max_length=10,
        )
        self.time_input = discord.ui.TextInput(
            label="Time (HH:MM, 24h)",
            placeholder="19:30",
            max_length=5,
        )
        self.message_input = discord.ui.TextInput(
            label="Description",
            placeholder="Optional description",
            required=False,
            max_length=1000,
        )
        self.channel_input = discord.ui.TextInput(
            label="Channel name (optional)",
            placeholder="#scheduled-events",
            required=False,
            max_length=100,
        )
        self.add_item(self.title_input)
        self.add_item(self.date_input)
        self.add_item(self.time_input)
        self.add_item(self.message_input)
        self.add_item(self.channel_input)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        try:
            await service.add_scheduled_event(
                interaction,
                str(self.date_input.value),
                str(self.time_input.value),
                str(self.title_input.value),
                str(self.message_input.value),
                str(self.channel_input.value) or None,
            )
        except Exception:
            await interaction.response.send_message(
                "Something went wrong while creating the event. Please try again.",
                ephemeral=True,
            )


class ScheduledEventEditModal(discord.ui.Modal):
    """Modal to edit a scheduled event."""

    def __init__(self, record: repository.ScheduledEventRecord):
        super().__init__(title="Edit scheduled event")
        event_time = _parse_event_time(record.start_time)
        self.record = record
        self.title_input = discord.ui.TextInput(
            label="Title",
            default=record.title,
            max_length=100,
        )
        self.date_input = discord.ui.TextInput(
            label="Date (YYYY-MM-DD)",
            default=event_time.strftime("%Y-%m-%d"),
            max_length=10,
        )
        self.time_input = discord.ui.TextInput(
            label="Time (HH:MM, 24h)",
            default=event_time.strftime("%H:%M"),
            max_length=5,
        )
        self.message_input = discord.ui.TextInput(
            label="Description",
            default=record.description,
            required=False,
            max_length=1000,
        )
        self.channel_input = discord.ui.TextInput(
            label="Channel name (optional)",
            placeholder="#scheduled-events",
            required=False,
            max_length=100,
        )
        self.add_item(self.title_input)
        self.add_item(self.date_input)
        self.add_item(self.time_input)
        self.add_item(self.message_input)
        self.add_item(self.channel_input)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        channel_name = str(self.channel_input.value).strip() or None
        try:
            if not interaction.response.is_done():
                await interaction.response.defer(ephemeral=True)
            await service.update_scheduled_event(
                interaction,
                self.record,
                str(self.date_input.value),
                str(self.time_input.value),
                str(self.title_input.value),
                str(self.message_input.value),
                channel_name,
            )
        except Exception:
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    "Something went wrong while updating the event. Please try again.",
                    ephemeral=True,
                )

#endregion


#region Views

class ScheduledEventSelect(discord.ui.Select):
    def __init__(self, view: "ScheduledEventSelectView"):
        super().__init__(placeholder="Select an event to edit", options=[])
        self.view_ref = view
        self.refresh_options()

    def refresh_options(self) -> None:
        options = []
        for record in self.view_ref.current_records:
            event_time = _parse_event_time(record.start_time)
            label = record.title[:100]
            description = event_time.strftime("%Y-%m-%d %H:%M")
            options.append(
                discord.SelectOption(
                    label=label,
                    description=description,
                    value=str(record.id),
                )
            )
        self.options = options

    async def callback(self, interaction: discord.Interaction) -> None:
        record_id = int(self.values[0])
        record = self.view_ref.record_lookup.get(record_id)
        if not record:
            await interaction.response.send_message("That event is no longer available.", ephemeral=True)
            return
        await interaction.response.send_modal(ScheduledEventEditModal(record))


class ScheduledEventSelectView(discord.ui.View):
    def __init__(self, records: List[repository.ScheduledEventRecord]):
        super().__init__(timeout=300)
        self.records = records
        self.record_lookup: Dict[int, repository.ScheduledEventRecord] = {
            record.id: record for record in records
        }
        self.page_size = 25
        self.page_index = 0
        self.message: Optional[discord.Message] = None
        self.select = ScheduledEventSelect(self)
        self.add_item(self.select)
        self._sync_buttons()

    @property
    def total_pages(self) -> int:
        if not self.records:
            return 1
        return (len(self.records) + self.page_size - 1) // self.page_size

    @property
    def current_records(self) -> List[repository.ScheduledEventRecord]:
        start = self.page_index * self.page_size
        end = start + self.page_size
        return self.records[start:end]

    def build_embed(self) -> discord.Embed:
        embed = discord.Embed(title="Select a scheduled event")
        if not self.records:
            embed.description = "No scheduled events found."
            return embed

        lines = []
        for index, record in enumerate(self.current_records, start=1 + self.page_index * self.page_size):
            event_time = _parse_event_time(record.start_time)
            lines.append(f"{index}. {event_time.strftime('%Y-%m-%d %H:%M')} - {record.title}")

        embed.description = "\n".join(lines)
        embed.set_footer(text=f"Page {self.page_index + 1}/{self.total_pages}")
        return embed

    def _sync_buttons(self) -> None:
        self.previous.disabled = self.page_index <= 0
        self.next.disabled = self.page_index >= self.total_pages - 1

    async def update_message(self, interaction: discord.Interaction) -> None:
        self.select.refresh_options()
        self._sync_buttons()
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    @discord.ui.button(label="Previous", style=discord.ButtonStyle.secondary)
    async def previous(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        if self.page_index > 0:
            self.page_index -= 1
        await self.update_message(interaction)

    @discord.ui.button(label="Next", style=discord.ButtonStyle.secondary)
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        if self.page_index < self.total_pages - 1:
            self.page_index += 1
        await self.update_message(interaction)

    async def on_timeout(self) -> None:
        for item in self.children:
            item.disabled = True
        if self.message:
            await self.message.edit(view=self)

#endregion
