from datetime import datetime, timedelta, timezone
from typing import ClassVar, Optional, Self

from odmantic import Model, Reference
from pydantic import NonNegativeFloat, NonNegativeInt, model_validator

from db.actor import Actor


# ----------------------------------------------------------------------------------------------------
# * Attack
# ----------------------------------------------------------------------------------------------------
class Attack(Model):
    """Representation of a single attack instance within a duel between two Actors."""

    model_config = {"collection": "attacks"}

    created_at: Optional[datetime] = datetime.now(timezone.utc)
    attacker: Actor = Reference()
    defender: Actor = Reference()

    is_fatal: bool = False  # attack results in a winner/loser (duel over)
    attacker_is_winner: bool = False
    defender_is_winner: bool = False
    attacker_is_loser: bool = False
    defender_is_loser: bool = False
    attacker_is_promoted: bool = False
    attacker_is_demoted: bool = False
    defender_is_promoted: bool = False
    defender_is_demoted: bool = False

    level_difference: float = 0
    gold_reward_modifier: float = 0
    gold_penalty_modifier: float = 0
    gold_reward: NonNegativeInt = 0
    gold_penalty: NonNegativeInt = 0

    ENERGY_COST: ClassVar[NonNegativeInt] = 1
    GOLD_REWARD_BASE: ClassVar[NonNegativeInt] = 40  # Win base gold reward
    GOLD_REWARD_PER_LEVEL: ClassVar[NonNegativeInt] = (
        8  # Extra gold per level (of loser)
    )
    LEVEL_DIFF_SCALE: ClassVar[NonNegativeFloat] = 15.0  # level diff impact
    GOLD_REWARD_ADVANTAGE_REDUCTION: ClassVar[NonNegativeFloat] = (
        0.7  # Max reduction (e.g., winner gets 1.0 - 0.7 = 30% reward if much higher)
    )
    GOLD_REWARD_UNDERDOG_BONUS: ClassVar[NonNegativeFloat] = (
        0.6  # Max bonus (e.g., winner gets 1.0 + 0.6 = 160% reward if much lower)
    )
    GOLD_PENALTY_ADVANTAGE_REDUCTION: ClassVar[NonNegativeFloat] = (
        0.5  # Max reduction (loser pays 1.0 - 0.5 = 50% penalty % if winner much higher)
    )
    GOLD_PENALTY_UNDERDOG_INCREASE: ClassVar[NonNegativeFloat] = (
        0.5  # Max increase (loser pays 1.0 + 0.5 = 150% penalty % if winner much lower)
    )
    GOLD_PENALTY_FACTOR_BASE: ClassVar[NonNegativeFloat] = (
        0.025  # Loser base loss: 2.5% of their current gold (slightly lowered base)
    )
    GOLD_PENALTY_MAX: ClassVar[NonNegativeInt] = (
        400  # Max gold loser can lose in one duel
    )
    REVIVE_COST_BASE: ClassVar[NonNegativeInt] = 75
    REVIVE_COST_PER_LEVEL: ClassVar[NonNegativeInt] = 15

    # ----------------------------------------------------------------------------------------------------

    @property
    def winner(self) -> Actor | None:
        return (
            self.attacker
            if self.attacker_is_winner
            else self.defender if self.defender_is_winner else None
        )

    @property
    def loser(self) -> Actor | None:
        return (
            self.attacker
            if self.attacker_is_loser
            else self.defender if self.defender_is_loser else None
        )

    @property
    def damage(self) -> int:
        return self.attacker.attack - self.defender.defense

    @property
    def effective_damage(self) -> NonNegativeInt:
        """Damage attacker deals to defender."""
        return self.damage if self.damage > 0 else 0

    @property
    def recoil_damage(self) -> NonNegativeInt:
        """Damage attacker receives back from defender."""
        return -self.damage if self.damage < 0 else 0

    # ----------------------------------------------------------------------------------------------------

    def perform(self):
        """Perform attack, determine winner/loser, and update players accordingly."""

        # Chek healths
        if self.attacker.health <= 0:
            return
        if self.defender.health <= 0:
            return

        # Consume energy
        if self.attacker.energy < self.ENERGY_COST:
            return
        self.attacker.energy = max(0, self.attacker.energy - self.ENERGY_COST)

        # Record attack datetime
        self.attacker.attacked_at = self.defender.defended_at = datetime.now(
            timezone.utc
        )

        # Apply damage
        if self.effective_damage > 0:
            self.defender.health = max(0, self.defender.health - self.effective_damage)
        if self.recoil_damage > 0:
            self.attacker.health = max(0, self.attacker.health - self.recoil_damage)

        # Determine winner
        winner: Actor | None = None
        loser: Actor | None = None
        if self.attacker.health > 0 and self.defender.health <= 0:
            winner = self.attacker
            loser = self.defender
            self.attacker_is_winner = True
            self.defender_is_loser = True
            self.is_fatal = True
        elif self.defender.health > 0 and self.attacker.health <= 0:
            winner = self.defender
            loser = self.attacker
            self.defender_is_winner = True
            self.attacker_is_loser = True
            self.is_fatal = True
        if not (winner and loser):
            return
        self.level_difference = float(winner.level - loser.level)

        # Calculate winner gold reward
        self.gold_reward_modifier = max(
            0,
            max(
                1.0 - self.GOLD_REWARD_ADVANTAGE_REDUCTION,
                min(
                    1.0 + self.GOLD_REWARD_UNDERDOG_BONUS,
                    (1.0 - (self.level_difference / self.LEVEL_DIFF_SCALE)),
                ),
            ),
        )  # Modifier decreases if winner level > loser level, increases otherwise
        self.gold_reward = int(
            (self.GOLD_REWARD_BASE + (loser.level * self.GOLD_REWARD_PER_LEVEL))
            * self.gold_reward_modifier
        )

        # Calculate Loser gold penalty
        self.gold_penalty_modifier = max(
            0,
            max(
                1.0 - self.GOLD_PENALTY_ADVANTAGE_REDUCTION,
                min(
                    1.0 + self.GOLD_PENALTY_UNDERDOG_INCREASE,
                    (1.0 - (self.level_difference / self.LEVEL_DIFF_SCALE)),
                ),
            ),
        )  # Modifier decreases if winner level > loser level, increases otherwise
        self.gold_penalty = int(
            min(
                (
                    loser.gold
                    * (self.GOLD_PENALTY_FACTOR_BASE * self.gold_penalty_modifier)
                ),
                self.GOLD_PENALTY_MAX,
            )
        )

        # Apply Gold Changes
        winner.gold += self.gold_reward
        loser.gold -= self.gold_penalty

        # Record duel
        winner.wins += 1
        loser.losses += 1
        winner.placement_duels = min(winner.duels, Actor.PLACEMENT_DUELS_MAX)
        loser.placement_duels = min(loser.duels, Actor.PLACEMENT_DUELS_MAX)

        # Remember rank before elo update
        attacker_pre_rank = self.attacker.rank
        defender_pre_rank = self.defender.rank

        # Update elo
        winner.elo += int(Actor.ELO_K_FACTOR * (1 - winner.expected_score(loser.elo)))
        loser.elo += int(Actor.ELO_K_FACTOR * (-loser.expected_score(winner.elo)))

        # Record elo change (rank promotion/demotion)
        if self.attacker.rank:
            attacker_rank_change = self.attacker.rank_change(attacker_pre_rank)
            self.attacker_is_promoted = attacker_rank_change > 0
            self.attacker_is_demoted = attacker_rank_change < 0
        if self.defender.rank:
            defender_rank_change = self.defender.rank_change(defender_pre_rank)
            self.defender_is_promoted = defender_rank_change > 0
            self.defender_is_demoted = defender_rank_change < 0

        # Done
        return
