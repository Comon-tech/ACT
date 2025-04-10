# RPG Guide

## Welcome to the ACT RPG! - Player Guide

Welcome, adventurer! This guide will walk you through the essential mechanics of our Discord RPG experience. Learn how to build your character, engage in combat, manage your resources, and rise through the ranks!

---

### **I. Your Character: Stats Explained**

Every member is an adventurer with unique statistics that determine their capabilities. You can view your current stats using `/profile status`. Understanding these is key to survival and success:

- ❤️ **Health:** Your current life force. If this drops to 0 or below from taking damage in a duel, you are **defeated**.
- ❤️ **Max Health:** The maximum amount of Health you can have. A higher Max Health means you can endure more damage before being defeated. Represents your overall toughness and resilience. _Increased by some Armor and Boots._
- ⚡ **Energy:** Your current stamina or focus. Performing actions like attacking consumes Energy. You cannot attack if your Energy is too low (likely 0 or less).
- ⚡ **Max Energy:** The maximum pool of Energy you possess. A higher Max Energy allows you to perform more attacks before needing to recover. Represents your total stamina or focus reserves. _Increased by some Weapons (Mace, Bow) and Footwear (Sandals)._
- ⚔️ **Attack:** Determines the power and potential damage of your offensive actions. Higher Attack means you hit harder, reducing your opponent's Health faster. _Increased primarily by Weapons._
- 🛡️ **Defense:** Reduces the amount of damage you take from incoming attacks. Higher Defense means you can block or mitigate more damage, improving your survivability. Represents your armor and blocking skill. _Increased by Armor, Shields, and Boots._
- 👟 **Speed:** Influences your agility in combat. Higher Speed **reduces the cooldown duration** required after performing an attack, allowing you to initiate your next attack sooner. _Increased by some Weapons (Dagger, Short Sword, Bow) and Footwear (Sandals, Shoes)._

_(Note: Stat bonuses mentioned are examples based on common item types; check specific items in the `/store`! You can recover lost Health and Energy using specific consumable items.)_

---

### **II. Progression: Level & Rank**

Your journey involves growing in two distinct ways: engagement and skill.

- **Level (XP):** Your Level reflects your **engagement and activity within the server**.
  - You earn Experience (XP) primarily by **chatting** in designated channels. XP gain considers message activity (length, attachments, embeds). Consistent, meaningful participation is rewarded.
  - When you accumulate enough XP, you automatically **Level Up!** The XP required increases for each subsequent level.
  - Each time you level up, you receive a **Gold reward**, scaling with your new level.
  - Check your current Level and XP progress with `/profile progress`. Level is purely a measure of chat activity.
- **Rank (Elo):** Your Rank represents your **combat prowess and skill** demonstrated in duels.
  - Winning duels increases your Rank (Elo rating), while losing decreases it.
  - Your Rank determines your standing on the combat leaderboards and signifies your fighting skill relative to other players.
  - Check your current Rank and Duel statistics (Wins/Losses) with `/profile progress`.

---

### **III. The Economy: Gold & Items**

Gold is the currency of the realm, used to acquire powerful items and recover from defeat.

**A. Earning Gold:**

1.  **Leveling Up:** Gain a deterministic gold reward upon reaching a new Level (from chat XP).
2.  **Combat Victory:** Defeating another player in a duel (`/attack`) grants you a **system-generated gold reward**.
    - This reward scales based on the **level of the opponent you defeated**.
    - The reward is further modified by the **level difference** between you and your opponent (bonus for beating higher levels, reduction for beating lower levels).
3.  **Loser Penalty:** When defeated, a player loses a small percentage of their current gold.
    - This percentage is modified by the **level difference** (higher penalty % for losing to lower levels, lower penalty % for losing to higher levels).
    - There's a **maximum cap** on how much gold can be lost in a single defeat.

**B. Spending Gold: The Store & Items**

- **The Store:** Access the item shop using `/store`. View all items or look up specifics using `/store [item name]`.
- **Buying Items:** Purchase items using `/buy [item name] [quantity]`. Your gold balance simply needs to cover the cost (debt doesn't prevent buying if you have enough _current_ gold).
- **Item Types:**
  - **Equippables:** Gear like Weapons, Armor, Helmets, Shields, and Footwear. Use `/equip [item name]` to wear them for passive stat bonuses. Check equipped items via `/profile property`.
  - **Consumables:** Items like Potions or Food. Use `/use [item name]` to consume them for a one-time effect, such as **instantly restoring Health or Energy**. The item is used up.

---

### **IV. Gameplay Loop: Combat & Recovery**

Engage with other players and manage your resources.

- **Attacking:** Initiate a duel with `/attack [member]`.
  - Attacking consumes **Energy**.
  - Your **Attack** stat influences damage dealt; opponent's **Defense** influences damage received.
  - After attacking, there is a **cooldown period** before you can attack again. Your **Speed** stat reduces the duration of this cooldown.
  - You **cannot** attack if you are currently **defeated**.
- **Defeat:** If your Health reaches 0 during a duel, you are **defeated**.
  - While defeated, the _only_ restriction is that you **cannot participate in duels** – you cannot initiate an attack (`/attack`) and cannot be targeted by others for an attack. You can still chat, gain XP, use items, manage inventory, etc.
- **Reviving:** To remove the "defeated" status and become eligible for duels again, use the `/revive` command.
  - Reviving costs a **gold fee** that scales with your Level.
  - If you cannot afford the cost, you can still revive but will enter **debt** (negative gold balance).
  - Being in debt **does not impose any gameplay restrictions**; it's simply a negative gold value you'll need to overcome through earning more gold.

---

### **V. Essential Commands**

Here’s a quick reference for the main commands:

**Profile & Information:** `/profile [subcommand]`

- `/profile overview`: Shows a summary of all your character information.
- `/profile status`: Displays your current Health, Energy, and core combat stats (Attack, Defense, Speed).
- `/profile property`: Lists your current Gold balance and your inventory (all items, highlighting equipped ones).
- `/profile progress`: Shows your **Rank (Elo)**, Duel statistics (Wins/Losses), **Level**, and XP progress.
- `/profile membership`: Displays relevant Discord server information like roles and join date.
- `/profile picture`: Shows your character's profile picture (if applicable/set).

**Store & Item Management:**

- `/store`: View all available items for purchase.
- `/store [item name]`: View details and stats of a specific item.
- `/buy [item name] [quantity]`: Purchase an item from the store.
- `/equip [item name]`: Equip a piece of gear from your inventory.
- `/use [item name]`: Use a consumable item from your inventory (e.g., to restore Health/Energy).

**Combat & Recovery:**

- `/attack [member]`: Initiate a duel against another server member (if neither is defeated).
- `/revive`: Pay the fee to recover after being defeated in a duel.

---

### 🔰 **Getting Started**

1.  Check your initial stats with `/profile status`.
2.  Start chatting to gain XP and level up for gold rewards! Track this via `/profile progress`.
3.  Browse the `/store` to plan your item purchases. Use `/buy` when ready.
4.  `/equip` gear to boost your stats. Use `/use` consumables to recover Health/Energy.
5.  Engage in duels with `/attack` to test your skills, earn gold, and climb the **Rank** ladder!
6.  If defeated, use `/revive` to get back into the action. Don't worry too much about debt.

Good luck on your adventures! If you have questions, don't hesitate to ask in the appropriate channels.
