# 🤖 Assistant of Common Tech (ACT)

[![Web](https://img.shields.io/badge/web-blue?logo=googlechrome)](https://github.com/topics/web)
[![Python](https://img.shields.io/badge/python-blue?logo=python)](https://github.com/topics/python)
[![Discord](https://img.shields.io/badge/discord-blue?logo=discord)](https://github.com/topics/discord)
[![FastAPI](https://img.shields.io/badge/fastapi-blue?logo=fastapi)](https://github.com/topics/fastapi)
[![MongoDB](https://img.shields.io/badge/mongodb-blue?logo=mongodb)](https://github.com/topics/mongo)

ACT is a [Discord](http://discord.com) bot designed to boost community engagement and interaction by providing a robust economy system and an array of entertaining commands, all tailored to deliver a dynamic and lively server experience.

<!-- ![Screenshot](./screenshot.gif?raw=true) -->

## 🏁 Getting started.

1. [Clone](https://docs.github.com/en/repositories/creating-and-managing-repositories/cloning-a-repository) repository:

   ```bash
    git clone <repository-url>
    cd <repository-folder>
   ```

2. [Install UV](https://docs.astral.sh/uv/getting-started/installation) for dependency management.

3. [Install MongoDB](https://www.mongodb.com/docs/manual/installation) and run **database** for development:

   ```bash
   uv run task db
   ```

   > [!TIP]
   >
   > 💡 To access the database using [Mongodb Shell](https://www.mongodb.com/products/tools/shell):
   >
   > ```bash
   > uv run task db-man
   > ```
   >
   > Ensure both the MongoDB **server** and the **shell** are using the same port.
   >
   > 💡 To fix a broken database:
   >
   > ```bash
   > uv run task db-fix
   > ```

4. Run **application** for development :

   ```bash
   uv run task app
   ```

   > [!TIP]
   >
   > 💡 Virtual environments and dependencies are automatically installed when you run any UV command, such as `uv run`, `uv sync`, or `uv lock`. [Learn more about UV projects](https://docs.astral.sh/uv/guides/projects)

## ✈️ Deployment

1. Create and run a live **MongoDB** database using a service like [**MongoDB Atlas**](https://www.mongodb.com/cloud/atlas) and get the **connection string**.

   > 💡 The remote MongoDB **connection string** (URI) usually looks something like this:
   >
   > ```
   > mongodb+srv://username:password@host-address/database-name?retryWrites=true&w=majority
   > ```
   >
   > where **username**, **password**, **host-address**, and **database-name** are placeholders for the values provided by the service and specific to the user.

2. Push the repository to a **Python server** using a service like [**Heroku**](https://heroku.com).

3. In the remote python server:

   a. Set the environment variable `MONGO_DB_URI` to the obtained mongoDB **connection string**:

   ```
   MONGO_DB_URI=mongodb+srv://...etc
   ```

   b. Set all other needed environment variables:

   ```
   DISCORD_BOT_TOKEN=PLACE_VALUE_HERE
   GEMINI_AI_API_KEY=PLACE_VALUE_HERE
   MONGO_DB_URI=mongodb://localhost:1717
   APP_SERVER_URL=http://localhost:8000
   ```

   c. Run **application** for production:

   ```bash
   uv run task app-prod
   ```

   🎉 Now your bot should be live and connected to the remote database!

## 🚀 Development

### 🏭 Environment

- Runtime: [**Python**](https://github.com/python)
  - Package Manager: [**UV**](https://github.com/astral-sh/uv)
  - Task Runner: [**Taskipy**](https://github.com/taskipy/taskipy)
- Editor: [**Visual Studio Code**](https://code.visualstudio.com)

### 🌑 Backend

- 🖥 Application:
  - 🤖 Bot: [**DiscordPy**](https://discordpy.readthedocs.io/en/stable/index.html)
  - 🌍 API: [**FastAPI**](https://fastapi.tiangolo.com)
- 💽 Database:
  - Engine: [**MongoDB**](https://www.mongodb.com)
  - Driver: [**PyMongo**](https://pymongo.readthedocs.io)
  - Validator: [**Pydantic**](https://docs.pydantic.dev)
  - ODM: [**ODMantic**](https://art049.github.io/odmantic)

### 📔 Convention

- Style Guide: [**PEP 8**](https://peps.python.org/pep-0008/)
  - Formatter: [**Black Formatter**](https://black.readthedocs.io/en/stable) / [**Black Formatter for Visual Studio Code**](https://marketplace.visualstudio.com/items?itemName=ms-python.black-formatter)

## 📄 License

Licensed under [GNU GPL](./LICENSE).
