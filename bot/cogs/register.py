from __future__ import annotations

import logging
import re
from collections.abc import Sequence
from typing import TYPE_CHECKING
from uuid import UUID

import discord
from discord import app_commands

from bot.kanidm import KanidmError

if TYPE_CHECKING:
    from bot.__main__ import Bot

log = logging.getLogger(__name__)

# Matches Kanidm's INAME_RE from server/lib/src/value.rs
INAME_RE = re.compile(r"^[a-z][a-z0-9\-_\.]{0,63}$")
# Matches Kanidm's root and dn=token from server/lib/src/value.rs
DISALLOWED_NAMES = frozenset({"root", "dn=token", "admin", "administrator", "system", "guest", "owner"})
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _is_valid_kanidm_name(name: str) -> bool:
    if not INAME_RE.match(name):
        return False
    try:
        UUID(name)
        return False
    except ValueError:
        pass
    return name not in DISALLOWED_NAMES


def _find_role(roles: Sequence[discord.Role], spec: str) -> discord.Role | None:
    """Look up a role by ID if `spec` is numeric, otherwise by name."""
    if spec.isdigit():
        return discord.utils.get(roles, id=int(spec))
    return discord.utils.get(roles, name=spec)


def _failure_message(exc: Exception) -> str:
    if isinstance(exc, KanidmError) and exc.status_code == 409:
        return "Registration failed: that username or email is already taken."
    return "Registration failed. Please try again later or contact an admin."


_registering: set[int] = set()


class RegisterModal(discord.ui.Modal, title="Register Account"):
    username = discord.ui.TextInput(
        label="Username",
        placeholder="jdoe",
        max_length=64,
    )
    email = discord.ui.TextInput(
        label="Email",
        placeholder="jdoe@example.com",
        max_length=254,
    )
    first_name = discord.ui.TextInput(
        label="First Name",
        placeholder="John",
        max_length=64,
    )
    last_name = discord.ui.TextInput(
        label="Last Name",
        placeholder="Doe",
        max_length=64,
    )

    async def on_submit(self, interaction: discord.Interaction[Bot]) -> None:
        await interaction.response.defer(ephemeral=True)

        bot = interaction.client
        settings = bot.settings
        kanidm = bot.kanidm
        usermap = bot.usermap
        user_id = interaction.user.id

        if await usermap.has(user_id):
            await interaction.followup.send(
                "You already have an account.",
                ephemeral=True,
            )
            return

        if user_id in _registering:
            await interaction.followup.send(
                "Registration already in progress.",
                ephemeral=True,
            )
            return

        username = str(self.username).strip().lower().replace(" ", "")
        email = str(self.email).strip().lower()
        display_name = f"{self.first_name} {self.last_name}".strip()

        if not _is_valid_kanidm_name(username):
            await interaction.followup.send(
                "Invalid username. Use lowercase letters, numbers, dots, hyphens, "
                "or underscores. Must start with a letter.",
                ephemeral=True,
            )
            return

        if not EMAIL_RE.match(email):
            await interaction.followup.send(
                "Invalid email address.",
                ephemeral=True,
            )
            return

        # The guard is held until the mapping is stored, so a second submission
        # can't slip in between account creation and usermap.set.
        _registering.add(user_id)
        uuid: str | None = None
        try:
            uuid = await kanidm.create_person(username, display_name, email)
            if settings.enable_posix:
                await kanidm.posix_enable_person(uuid)
            if settings.kanidm_group:
                await kanidm.add_to_group(settings.kanidm_group, uuid)
            token = await kanidm.create_credential_reset_token(uuid)
            await usermap.set(user_id, uuid)
        except Exception as exc:
            if isinstance(exc, KanidmError):
                log.error("Kanidm error during registration of %s: %s", username, exc)
            else:
                log.exception("Unexpected error during registration of %s", username)
            # Roll back so the user can retry with the same username.
            if uuid is not None:
                await kanidm.delete_person_quietly(uuid)
            await interaction.followup.send(_failure_message(exc), ephemeral=True)
            return
        finally:
            _registering.discard(user_id)

        try:
            await bot.update_status()
        except Exception:
            log.exception("Failed to update presence")

        reset_url = f"{settings.kanidm_url}/ui/reset?token={token}"
        if settings.enable_posix:
            reset_msg = f"Set your Passkey and UNIX Password here:\n{reset_url}"
        else:
            reset_msg = f"Set your Passkey here:\n{reset_url}"

        # Assign Discord role
        role_note = ""
        if settings.discord_role and interaction.guild and isinstance(interaction.user, discord.Member):
            try:
                role = _find_role(interaction.guild.roles, settings.discord_role)
                if role is None:
                    role_note = f"\n\n⚠ Could not find Discord role `{settings.discord_role}`."
                else:
                    await interaction.user.add_roles(role)
            except discord.HTTPException as exc:
                log.error("Failed to assign role to %s: %s", interaction.user, exc)
                role_note = (
                    "\n\n⚠ Account was created but Discord role assignment failed. "
                    "Please ask an admin to assign your role."
                )

        await interaction.followup.send(
            f"Account **{username}** created!\n\n{reset_msg}{role_note}",
            ephemeral=True,
        )


@app_commands.guild_only()
@app_commands.command(name="register", description="Register a new account")
async def register(interaction: discord.Interaction[Bot]) -> None:
    assert isinstance(interaction.user, discord.Member)
    if await interaction.client.usermap.has(interaction.user.id):
        await interaction.response.send_message(
            "You already have an account.",
            ephemeral=True,
        )
        return
    required = interaction.client.settings.discord_require_role
    if required:
        role = _find_role(interaction.user.roles, required)
        if role is None:
            role_label = f"<@&{required}>" if required.isdigit() else f"`{required}`"
            await interaction.response.send_message(
                f"You need the {role_label} role to register.",
                ephemeral=True,
            )
            return
    await interaction.response.send_modal(RegisterModal())
