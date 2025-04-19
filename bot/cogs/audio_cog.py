from asyncio import get_event_loop
from datetime import timedelta
from typing import Optional

from discord import (
    FFmpegPCMAudio,
    Guild,
    Interaction,
    Member,
    VoiceChannel,
    VoiceClient,
    VoiceState,
    app_commands,
)
from discord.ext.commands import GroupCog
from humanize import precisedelta

from bot.main import ActBot
from bot.ui.embed import EmbedX
from utils.audio import AudioManager, AudioQueue, AudioTrack
from utils.log import logger

log = logger(__name__)


# ----------------------------------------------------------------------------------------------------
# * Audio Player
# ----------------------------------------------------------------------------------------------------
class DiscordAudioPlayer:
    """Interface for Managing audio playback for discord guild."""

    def __init__(self, guild: Guild):
        self.guild = guild
        self.playback_queue: list[AudioTrack] = []
        self.played_tracks: list[AudioTrack] = []  # Tracks that have been played
        self.current_track: AudioTrack | None = None
        self.voice_client: VoiceClient | None = None
        self.playing: bool = False
        self.loop_queue: bool = False  # Configurable queue looping
        self.loop = get_event_loop()

    def add_tracks(self, queue: AudioQueue) -> None:
        """Add tracks from an AudioQueue to the playback queue."""
        self.playback_queue.extend(queue.tracks)
        log.debug(f"[{self.guild.name}] Added {len(queue.tracks)} tracks to queue.")

    async def play_next(self) -> bool:
        """Play the next track in the queue. Get True if played."""
        if not self.voice_client or (
            not self.playback_queue and not (self.loop_queue and self.played_tracks)
        ):
            self.playing = False
            self.current_track = None
            if self.voice_client and self.voice_client.is_connected():
                await self.disconnect()
                log.info(
                    f"[{self.guild.name}] Disconnected due to empty queue (looping: {self.loop_queue})."
                )
            return False

        # If queue is empty but looping is enabled, repopulate from played tracks
        if not self.playback_queue and self.loop_queue:
            self.playback_queue.extend(self.played_tracks)
            self.played_tracks.clear()
            log.debug(
                f"[{self.guild.name}] Looped {len(self.playback_queue)} tracks back to queue."
            )

        self.current_track = self.playback_queue.pop(0)
        self.playing = True

        if not self.current_track:  # Type checker safety
            self.playing = False
            return False

        # Store the current track in played_tracks for potential looping
        self.played_tracks.append(self.current_track)

        try:
            self.voice_client.play(
                source=FFmpegPCMAudio(
                    source=self.current_track.stream_url or self.current_track.url,
                    before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
                ),
                after=lambda e: self.loop.create_task(self._after_playback(e)),
            )
            log.info(
                f"[{self.guild.name}] 🔊 Playing track '{self.current_track.title}'."
            )
            return True
        except Exception as e:
            log.exception(
                f"[{self.guild.name}] Failed to play track '{self.current_track.title}'."
            )
            self.current_track = None
            self.playing = False
            return await self.play_next()

    async def _after_playback(self, e: Exception | None):
        """Handle playback completion or errors."""
        if e:
            log.exception(f"[{self.guild.name}] Playback error: {e}")
        await self.play_next()

    async def connect(self, channel) -> bool:
        """Connect to a voice channel."""
        if not isinstance(channel, VoiceChannel):
            log.warning(
                f"[{self.guild.name}] Cannot connect to {channel.name}: Stage channels are not supported."
            )
            return False
        try:
            perms = channel.permissions_for(self.guild.me)
            if not perms.connect or not perms.speak:
                log.warning(
                    f"[{self.guild.name}] Missing connect or speak permissions in {channel.name}."
                )
                return False

            if self.voice_client and self.voice_client.channel != channel:
                await self.voice_client.disconnect()
                self.voice_client = None
            if not self.voice_client:
                self.voice_client = await channel.connect()
                log.info(
                    f"[{self.guild.name}][{channel.name}] Connected to voice channel."
                )
            return True
        except Exception as e:
            log.exception(
                f"[{self.guild.name}][{channel.name}] Failed to connect to voice channel: {e}"
            )
            return False

    async def disconnect(self) -> None:
        """Disconnect from the voice channel."""
        if self.voice_client:
            await self.voice_client.disconnect()
            self.voice_client = None
            log.info(f"[{self.guild.name}] Disconnected from voice channel.")

    def stop(self) -> None:
        """Stop playback and clear the queue."""
        self.playback_queue.clear()
        self.played_tracks.clear()  # Clear played tracks to prevent looping
        self.current_track = None
        self.playing = False
        if self.voice_client and self.voice_client.is_playing():
            self.voice_client.stop()
        log.info(f"[{self.guild.name}] Playback stopped and queues cleared.")


# ----------------------------------------------------------------------------------------------------
# * Audio Cog
# ----------------------------------------------------------------------------------------------------
class AudioCog(
    GroupCog, group_name="audio", description="Provide audio playback interface."
):
    def __init__(self, bot: ActBot):
        self.bot = bot
        self.audio_manager = AudioManager()
        self.audio_players: dict[int, DiscordAudioPlayer] = {}  # guild_id: AudioPlayer

    def get_player(self, guild: Guild) -> DiscordAudioPlayer:
        """Get or create an AudioPlayer for the guild."""
        if guild.id not in self.audio_players:
            self.audio_players[guild.id] = DiscordAudioPlayer(guild)
        return self.audio_players[guild.id]

    # ----------------------------------------------------------------------------------------------------
    @GroupCog.listener()
    async def on_voice_state_update(
        self, member: Member, before: VoiceState, after: VoiceState
    ):
        log.info(
            f"[🔊 {before.channel} -> {after.channel}] 👤{member.name} voice state changed."
        )
        if member == self.bot.user and not after.channel:  # Bot was disconnected
            player = self.audio_players.get(member.guild.id)
            if player:
                player.stop()
                await player.disconnect()
                self.audio_players.pop(member.guild.id, None)
                log.info(
                    f"[{member.guild.name}] Cleared audio player due to disconnection."
                )

    # ----------------------------------------------------------------------------------------------------
    @app_commands.command(
        name="play", description="Play audio from a URL or search query"
    )
    @app_commands.describe(
        query="URL or search query", vc_channel="Voice channel to join (optional)"
    )
    async def play(
        self,
        interaction: Interaction,
        query: str,
        vc_channel: Optional[VoiceChannel] = None,
    ):
        await interaction.response.defer(ephemeral=True)

        # Ensure user is in a guild
        if not interaction.guild:
            await interaction.followup.send(
                embed=EmbedX.warning("This command can only be used in a server."),
                ephemeral=True,
            )
            return

        # Get player's voice channel
        player = self.get_player(interaction.guild)
        user = interaction.user

        # Determine voice channel
        target_channel = None
        if vc_channel:
            target_channel = vc_channel
        elif isinstance(user, Member) and user.voice and user.voice.channel:
            target_channel = user.voice.channel
        else:  # Pick a random voice channel
            voice_channels = [
                ch
                for ch in interaction.guild.voice_channels
                if ch.permissions_for(interaction.guild.me).connect
                and isinstance(ch, VoiceChannel)
            ]
            if voice_channels:
                target_channel = voice_channels[0]
            else:
                await interaction.followup.send(
                    embed=EmbedX.error("No accessible voice channels found."),
                    ephemeral=True,
                )
                return

        # Connect to voice channel
        if not await player.connect(target_channel):
            await interaction.followup.send(
                embed=EmbedX.error(f"Failed to connect to {target_channel.name}."),
                ephemeral=True,
            )
            return

        # Fetch audio data
        queue = await self.audio_manager.get_audio(query)
        if not queue:
            await interaction.followup.send(
                embed=EmbedX.error("Could not find audio for the provided query."),
                ephemeral=True,
            )
            return

        # Add tracks to queue & Start playback if not already playing
        player.add_tracks(queue)
        if not player.playing:
            if not await player.play_next():
                await interaction.followup.send(
                    embed=EmbedX.error("Could not play audio."),
                    ephemeral=True,
                )
                return

        # Send feedback
        embed = EmbedX.info(emoji="🎵", title="Audio Playback")
        track = queue.tracks[0]
        embed.add_field(
            name="Added",
            value=f"**🔊 [{track.title}]({track.url})**\n👤 {track.artist}\n⏲ {precisedelta(timedelta(seconds=track.duration or 0))}",
        )
        embed.add_field(
            name="Source",
            value=f"**💿 {queue.title}**\n🎙 {queue.source_name.capitalize()} {queue.source_type.capitalize()}\n🎼 {len(queue.tracks)} tracks",
        )
        await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="stop", description="Stop playback and clear queue")
    async def stop(self, interaction: Interaction):
        await interaction.response.defer(ephemeral=True)

        # Ensure user is in a guild
        if not interaction.guild:
            await interaction.followup.send(
                embed=EmbedX.warning("This command can only be used in a server."),
                ephemeral=True,
            )
            return

        player = self.get_player(interaction.guild)
        if not player.voice_client or not player.voice_client.is_connected():
            await interaction.followup.send(
                embed=EmbedX.warning("Not connected to a voice channel."),
                ephemeral=True,
            )
            return

        player.stop()
        await player.disconnect()

        embed = EmbedX.info(emoji="🛑", title="Playback Stopped")
        embed.add_field(
            name="Status",
            value="Playback stopped and queue cleared.",
            inline=False,
        )
        await interaction.followup.send(embed=embed, ephemeral=True)
        log.info(f"[{interaction.guild.name}] Stopped playback via command.")

    @app_commands.command(name="skip", description="Skip the current track")
    async def skip(self, interaction: Interaction):
        await interaction.response.defer(ephemeral=True)

        # Ensure user is in a guild
        if not interaction.guild:
            await interaction.followup.send(
                embed=EmbedX.warning("This command can only be used in a server."),
                ephemeral=True,
            )
            return

        player = self.get_player(interaction.guild)
        if not player.voice_client or not player.voice_client.is_connected():
            await interaction.followup.send(
                embed=EmbedX.warning("Not connected to a voice channel."),
                ephemeral=True,
            )
            return

        if not player.playing or not player.current_track:
            await interaction.followup.send(
                embed=EmbedX.warning("Nothing is playing."),
                ephemeral=True,
            )
            return

        skipped_track = player.current_track
        player.voice_client.stop()  # Stop current playback, triggering _after_playback

        embed = EmbedX.info(emoji="⏭", title="Audio Skip")
        embed.add_field(
            name="Skipped",
            value=f"**🔈 {skipped_track.title}**",
            inline=False,
        )
        if player.playback_queue:
            next_track = player.playback_queue[0]
            embed.add_field(
                name="Next Up",
                value=f"**🔊 {next_track.title}**\n👤 {next_track.artist}\n⏲ {precisedelta(timedelta(seconds=next_track.duration or 0))}",
                inline=False,
            )
        else:
            embed.add_field(
                name="Queue",
                value="No more tracks in queue.",
                inline=False,
            )
        await interaction.followup.send(embed=embed, ephemeral=True)
        log.info(f"[{interaction.guild.name}] Skipped track '{skipped_track.title}'.")

    @app_commands.command(name="queue", description="Show the current queue")
    async def queue(self, interaction: Interaction):
        await interaction.response.defer(ephemeral=True)

        # Ensure user is in a guild
        if not interaction.guild:
            await interaction.followup.send(
                embed=EmbedX.warning("This command can only be used in a server."),
                ephemeral=True,
            )
            return

        player = self.get_player(interaction.guild)
        if not player.current_track and not player.playback_queue:
            await interaction.followup.send(
                embed=EmbedX.warning("The queue is empty."),
                ephemeral=True,
            )
            return

        embed = EmbedX.info(emoji="🎶", title="Audio Queue")
        if player.current_track:
            embed.add_field(
                name="Now Playing",
                value=(
                    f"**🔊 [{player.current_track.title}]({player.current_track.url})**\n"
                    f"👤 {player.current_track.artist or 'Unknown'}\n"
                    f"⏲ {precisedelta(timedelta(seconds=player.current_track.duration or 0))}"
                ),
                inline=False,
            )

        if player.playback_queue:
            # Limit to 10 tracks to avoid embed field limits
            queue_str = ""
            for i, track in enumerate(player.playback_queue[:10], 1):
                queue_str += (
                    f"{i}. **{track.title}** "
                    f"({precisedelta(timedelta(seconds=track.duration or 0))})\n"
                )
            if len(player.playback_queue) > 10:
                queue_str += f"...and {len(player.playback_queue) - 10} more tracks."
            embed.add_field(
                name=f"Up Next ({len(player.playback_queue)} tracks)",
                value=queue_str or "No tracks queued.",
                inline=False,
            )
        else:
            embed.add_field(
                name="Up Next",
                value="No tracks queued.",
                inline=False,
            )

        await interaction.followup.send(embed=embed, ephemeral=True)
        log.info(f"[{interaction.guild.name}] Displayed audio queue.")

    @app_commands.command(
        name="settings", description="View or configure audio settings"
    )
    @app_commands.describe(loop="Enable or disable queue looping")
    async def settings(self, interaction: Interaction, loop: bool | None = None):
        await interaction.response.defer(ephemeral=True)

        # Ensure user is in a guild
        if not interaction.guild:
            await interaction.followup.send(
                embed=EmbedX.warning("This command can only be used in a server."),
                ephemeral=True,
            )
            return

        player = self.get_player(interaction.guild)

        if loop is not None:
            # Update loop setting
            player.loop_queue = loop
            embed = EmbedX.info(emoji="⚙️", title="Audio Settings Updated")
            embed.add_field(
                name="Queue Looping",
                value=f"{'Enabled' if player.loop_queue else 'Disabled'}",
                inline=False,
            )
            log.info(
                f"[{interaction.guild.name}] Queue looping set to {player.loop_queue}."
            )
        else:
            # Display current settings
            embed = EmbedX.info(emoji="⚙️", title="Audio Settings")
            embed.add_field(
                name="Queue Looping",
                value=f"{'Enabled' if player.loop_queue else 'Disabled'}",
                inline=False,
            )
            log.info(f"[{interaction.guild.name}] Displayed audio settings.")

        await interaction.followup.send(embed=embed, ephemeral=True)


# ----------------------------------------------------------------------------------------------------
