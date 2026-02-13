"""Reusable paginator helpers for interaction responses."""

#region Imports

from typing import List, Optional

import discord

#endregion


#region Helpers

def paginate_lines(lines: List[str], page_size: int, header: Optional[str] = None) -> List[str]:
    if page_size <= 0:
        page_size = 10

    pages: List[str] = []
    for start in range(0, len(lines), page_size):
        chunk = lines[start : start + page_size]
        content = "\n".join(chunk)
        if header:
            content = f"{header}\n\n{content}"
        pages.append(content)

    return pages or [header or "No items found."]


def paginate_text(text: str, max_length: int = 1900) -> List[str]:
    if max_length <= 0:
        max_length = 1900

    pages = [text[i : i + max_length] for i in range(0, len(text), max_length)]
    return pages or [""]

#endregion


#region View

class PaginatorView(discord.ui.View):
    def __init__(self, pages: List[str], author_id: int, timeout: float = 120.0):
        super().__init__(timeout=timeout)
        self.pages = pages
        self.author_id = author_id
        self.index = 0
        self.message: Optional[discord.Message] = None
        self._sync_buttons()

    def _format_page(self) -> str:
        total = len(self.pages)
        if total <= 1:
            return self.pages[0]
        return f"{self.pages[self.index]}\n\nPage {self.index + 1}/{total}"

    def _sync_buttons(self) -> None:
        total = len(self.pages)
        self.previous.disabled = total <= 1 or self.index == 0
        self.next.disabled = total <= 1 or self.index >= total - 1

    async def _update(self, interaction: discord.Interaction) -> None:
        self._sync_buttons()
        await interaction.response.edit_message(content=self._format_page(), view=self)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.author_id

    @discord.ui.button(label="Previous", style=discord.ButtonStyle.secondary)
    async def previous(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        if self.index > 0:
            self.index -= 1
        await self._update(interaction)

    @discord.ui.button(label="Next", style=discord.ButtonStyle.secondary)
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        if self.index < len(self.pages) - 1:
            self.index += 1
        await self._update(interaction)

    async def on_timeout(self) -> None:
        self._sync_buttons()
        for child in self.children:
            if isinstance(child, discord.ui.Button):
                child.disabled = True
        if self.message:
            await self.message.edit(view=self)

#endregion


#region Send Helper

async def send_paginated_message(
    ctx: discord.Interaction,
    pages: List[str],
    *,
    ephemeral: bool = False,
) -> None:
    view = PaginatorView(pages, author_id=ctx.user.id)
    content = view._format_page()

    if ctx.response.is_done():
        message = await ctx.followup.send(content, view=view, ephemeral=ephemeral)
    else:
        await ctx.response.send_message(content, view=view, ephemeral=ephemeral)
        message = await ctx.original_response()

    view.message = message

#endregion
