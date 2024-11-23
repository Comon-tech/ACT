---
# TACT (The Assistant of Common Tech) Discord Bot

TACT is a feature-rich, open-source Discord bot designed to gamify and enhance server engagement by awarding XP, tracking levels, and enabling users to interact through fun commands. This bot is built with Python, Discord.py, and PostgreSQL, and is Dockerized for seamless deployment.

## Features

- **Leveling System**: Users earn XP by messaging and participating in server activities.
- **Server Bump Rewards**: Users are awarded XP for bumping the server.
- **Interactive Fun Commands**: Users can “steal” XP, “shoot” each other, and buy virtual items from a store.
- **Leaderboard and Server Stats**: Displays top users by level and overall server stats.
- **Persistent Data**: Uses PostgreSQL for data storage.
- **Dockerized Setup**: Deploy easily using Docker.

## Installation

### Quick Start

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/comon-tech/TACT.git
   cd TACT
   ```

2. **Set Up Environment Variables**:
   Rename `.env.example` to `.env` and replace with your own values:
   ```bash
   DISCORD_TOKEN=your-discord-token
   DATABASE_URL=postgresql://bot_user:bot_password@db:5432/bot_db
   ```

3. **Run**:
   ```py
   python app.py
   ```

## Commands

### General Commands

| Command             | Description                                                                                 | Usage                                  |
|---------------------|---------------------------------------------------------------------------------------------|----------------------------------------|
| `/level`            | Displays your current level and XP.                                                         | `/level`                               |
| `/leaderboard`      | Shows the top users by level in the server.                                                 | `/leaderboard`                         |
| `/server_stats`     | Displays the server's total users, total XP, and average level (admin-only).                | `/server_stats`                        |
| `/give_xp`          | Grants XP to a user.                                                                        | `/give_xp <@user> <amount>`            |
| `/reset_xp`         | Resets a user's XP and level (admin-only).                                                  | `/reset_xp <@user>`                    |

### Fun Interaction Commands

| Command             | Description                                                                                 | Usage                                  |
|---------------------|---------------------------------------------------------------------------------------------|----------------------------------------|
| `/steal <@user>`    | Attempt to steal XP from another user.                                                      | `/steal <@user>`                       |
| `/shoot <@user>`    | Attempt to shoot another user (for fun).                                                    | `/shoot <@user>`                       |
| `/inventory`        | Shows the items you currently own.                                                          | `/inventory`                           |

### Store Commands

| Command             | Description                                                                                 | Usage                                  |
|---------------------|---------------------------------------------------------------------------------------------|----------------------------------------|
| `/store`            | Displays available items for purchase and their prices.                                     | `/store`                               |
| `/buy <item>`       | Buy an item from the store if you have enough XP.                                           | `/buy <item>`                          |

## Data Persistence


TACT uses (currently a json file but migrating soon) PostgreSQL to store XP, level, and inventory data for persistent tracking across sessions. Docker Compose configures and manages the PostgreSQL container.

## Contributing

We welcome contributions! Please fork this repository, create a branch with your feature or fix, and submit a pull request.

1. Fork the repository.
2. Clone your fork:
   ```bash
   git clone https://github.com/yourusername/TACT.git
   ```
3. Create a new branch:
   ```bash
   git checkout -b feature-branch
   ```
4. Make your changes and commit them:
   ```bash
   git commit -m "Add new feature"
   ```
5. Push to your fork and submit a pull request.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more details.

---
