from odmantic import Field, Model


# ----------------------------------------------------------------------------------------------------
# * Rank
# ----------------------------------------------------------------------------------------------------
class Rank(Model):
    model_config = {"collection": "ranks"}

    id: int = Field(primary_field=True)
    name: str
    description: str = ""
    emoji: str = ""
    alt_emoji: str = "🎖"
    icon_url: str = ""
