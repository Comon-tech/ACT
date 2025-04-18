import asyncio

from discord import (
    AudioSource,
    FFmpegPCMAudio,
    Guild,
    Interaction,
    Member,
    VoiceClient,
    app_commands,
    utils,
)
from discord.ext.commands import GroupCog

from bot.main import ActBot
from bot.ui.embed import EmbedX
from utils.audio import MediaSource, YouTubeSource
from utils.log import logger

log = logger(__name__)


# ----------------------------------------------------------------------------------------------------
# * Audio Player
# ----------------------------------------------------------------------------------------------------
class DiscordAudioPlayer:
    def __init__(self, guild: Guild):
        self.guild = guild
        self.queue: list[MediaSource] = []
        self.current: MediaSource | None = None
        self.playing = False
        self.loop = asyncio.get_event_loop()

    async def play_next(self, voice_client: VoiceClient) -> bool:
        if not self.queue or not voice_client:
            self.playing = False
            await voice_client.disconnect()
            return False

        self.current = self.queue.pop(0)
        self.playing = True

        try:
            source = FFmpegPCMAudio(
                self.current.url,
                before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
            )
            voice_client.play(
                source,
                after=lambda e: self.loop.create_task(self.play_next(voice_client)),
            )
            return True
        except Exception as e:
            log.error(f"Error playing audio: {e}")
            self.playing = False
            await self.play_next(voice_client)
            return False

    def add_to_queue(self, sources: list[MediaSource]):
        self.queue.extend(sources)

    def clear_queue(self):
        self.queue.clear()

    def stop(self):
        self.clear_queue()
        self.playing = False
        self.current = None


# ----------------------------------------------------------------------------------------------------
# * Audio Cog
# ----------------------------------------------------------------------------------------------------
class AudioCog(
    GroupCog, group_name="audio", description="Provide audio playback interface."
):

    def __init__(self, bot: ActBot):
        self.bot = bot
        self.queue: list[AudioSource] = []
        self.current: AudioSource | None = None
        self.playing = False
        self.loop = asyncio.get_event_loop()
        self.audio_players: dict[int, DiscordAudioPlayer] = {}
        self.source_providers = {
            "youtube": YouTubeSource,
            # Add more providers here (e.g., 'soundcloud': SoundCloudSource)
        }

    # ----------------------------------------------------------------------------------------------------

    @GroupCog.listener()
    async def on_voice_state_update(self, member: Member, before, after):
        if member == self.bot.user and not after.channel:  # Bot was disconnected
            audio_player = self.get_audio_player(member.guild)
            if audio_player:
                audio_player.stop()
                self.audio_players.pop(member.guild.id, None)

    # ----------------------------------------------------------------------------------------------------

    @app_commands.command(
        name="play", description="Play audio from a YouTube URL or search query"
    )
    @app_commands.describe(query="YouTube URL or search query")
    async def play(self, interaction: Interaction, query: str):
        await interaction.response.defer(ephemeral=True)

        voice_client = await self.ensure_voice(interaction)
        if not voice_client:
            return

        audio_player = self.get_audio_player(interaction.guild)
        if not audio_player:
            return

        # Determine source provider (default to YouTube)
        source_provider = self.source_providers["youtube"]

        # Extract sources
        sources = await source_provider.from_url(query, loop=self.bot.loop)

        if not sources:
            await interaction.followup.send("No audio sources found!", ephemeral=True)
            return

        audio_player.add_to_queue(sources)

        if not audio_player.playing:
            await audio_player.play_next(voice_client)

        await interaction.followup.send(
            f"Added {len(sources)} track(s) to queue. Now playing: {audio_player.current.title}"
            if audio_player.current
            else f"Added {len(sources)} track(s) to queue."
        )

    @app_commands.command(name="stop", description="Stop playback and clear queue")
    async def stop(self, interaction: Interaction):
        voice_client = await self.ensure_voice(interaction)
        if not voice_client:
            return

        audio_player = self.get_audio_player(interaction.guild)
        if audio_player:
            audio_player.stop()

        if voice_client.is_connected():
            await voice_client.disconnect()

        await interaction.response.send_message("Stopped playback and cleared queue.")

    @app_commands.command(name="skip", description="Skip the current track")
    async def skip(self, interaction: Interaction):
        voice_client = await self.ensure_voice(interaction)
        if not voice_client:
            return

        player = self.get_audio_player(interaction.guild)
        if not player.playing:
            await interaction.response.send_message(
                "Nothing is playing!", ephemeral=True
            )
            return

        voice_client.stop()
        await interaction.response.send_message("Skipped current track.")

    @app_commands.command(name="queue", description="Show the current queue")
    async def queue(self, interaction: Interaction):
        player = self.get_audio_player(interaction.guild)
        if not player.queue and not player.current:
            await interaction.response.send_message("Queue is empty!", ephemeral=True)
            return

        embed = EmbedX.info(title="Queue", color=discord.Color.blue())
        if player.current:
            # Truncate current track title to avoid exceeding field limits
            current_title = (
                player.current.title[:200] + "..."
                if len(player.current.title) > 200
                else player.current.title
            )
            embed.add_field(
                name="Now Playing",
                value=f"{current_title} ({player.current.url})",
                inline=False,
            )

        if player.queue:
            # Limit tracks per field to avoid exceeding 1024 chars
            max_field_length = 1024
            max_tracks_per_field = 5  # Adjust based on typical title lengths
            queue_chunks = [
                player.queue[i : i + max_tracks_per_field]
                for i in range(0, len(player.queue), max_tracks_per_field)
            ]

            for i, chunk in enumerate(
                queue_chunks[:2]
            ):  # Limit to 2 fields to stay within embed limits
                queue_str = ""
                for j, source in enumerate(chunk):
                    # Truncate title to avoid exceeding field limits
                    title = (
                        source.title[:100] + "..."
                        if len(source.title) > 100
                        else source.title
                    )
                    entry = (
                        f"{i * max_tracks_per_field + j + 1}. {title} ({source.url})\n"
                    )
                    if len(queue_str) + len(entry) > max_field_length:
                        break
                    queue_str += entry

                if queue_str:
                    embed.add_field(
                        name=f"Up Next (Part {i + 1})" if i > 0 else "Up Next",
                        value=queue_str,
                        inline=False,
                    )

            if len(player.queue) > max_tracks_per_field * 2:
                embed.set_footer(
                    text=f"And {len(player.queue) - max_tracks_per_field * 2} more tracks..."
                )

        await interaction.response.send_message(embed=embed)

    # ----------------------------------------------------------------------------------------------------

    def get_audio_player(self, guild: Guild | None) -> DiscordAudioPlayer | None:
        if not guild:
            return None
        if guild.id not in self.audio_players:
            self.audio_players[guild.id] = DiscordAudioPlayer(guild)
        return self.audio_players[guild.id]

    async def ensure_voice(self, interaction: Interaction) -> VoiceClient | None:
        if not interaction.user.voice:
            await interaction.followup.send(
                "You need to be in a voice channel!", ephemeral=True
            )
            return None

        voice_channel = interaction.user.voice.channel
        voice_client = utils.get(self.bot.voice_clients, guild=interaction.guild)

        if voice_client and voice_client.is_connected():
            if voice_client.channel != voice_channel:
                await voice_client.move_to(voice_channel)
        else:
            voice_client = await voice_channel.connect()

        return voice_client
