from odmantic import Field, Model


# ----------------------------------------------------------------------------------------------------
# * Stat
# ----------------------------------------------------------------------------------------------------
class Stat(Model):
    model_config = {"collection": "stats"}

    id: str = Field(primary_field=True)
    name: str
    description: str = ""
    emoji: str = ""
    alt_emoji: str = "❔"
