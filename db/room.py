from odmantic import Field, Model


# -------------------------------------------------------------------------------------------------
# * Room
# -------------------------------------------------------------------------------------------------
class Room(Model):
    model_config = {"collection": "rooms"}

    id: str = Field(primary_field=True)
    channel_id: int
    channel_name: str = ""
    channel_is_voice: bool = False
