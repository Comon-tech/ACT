from bson import ObjectId
from odmantic import Field, Model


# -------------------------------------------------------------------------------------------------
# * Guild Settings
# -------------------------------------------------------------------------------------------------
class GuildSettings(Model):
    """Per-guild settings written by the web dashboard (see ../act-dashboard).

    Read-only from the bot's side: the dashboard owns this collection (in the main database), and
    ODMantic only round-trips fields declared here, so saving this model would strip the rest.
    Field names follow the dashboard's camelCase document keys via `key_name`.
    """

    model_config = {"collection": "guild_settings"}

    id: ObjectId = Field(primary_field=True, default_factory=ObjectId)
    guild_id: str = Field(key_name="guildId")
    auto_reply_enabled: bool | None = Field(default=None, key_name="autoReplyEnabled")
    auto_reply_chance: float | None = Field(
        default=None, ge=0, le=1, key_name="autoReplyChance"
    )
    initiative_enabled: bool | None = Field(default=None, key_name="initiativeEnabled")
