import discord
import json
import asyncio
import random
import os
from discord.ext import commands
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

# On Start
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)
active_ghostping_tasks={}
@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    content = message.content.strip()
    guild = message.guild
    if message.content.startswith('$guess'):
        await message.channel.send('Guess a number between 1 and 10.')

        def is_correct(m):
            return m.author == message.author and m.channel == message.channel and m.content.isdigit()

        answer = random.randint(1, 10)

        try:
            guess = await client.wait_for('message', check=is_correct, timeout=5.0)
        except asyncio.TimeoutError:
            return await message.channel.send(f'Sorry, you took too long. It was {answer}.')

        if int(guess.content) == answer:
            await message.channel.send('You are right!')
        else:
            await message.channel.send(f'Oops. It is actually {answer}.')
    async def send_temp_reply(text):
        await message.channel.send(text)

    if content.startswith("$role create"):
        role_name = content[len("!role create "):].strip()
        if not role_name:
            await send_temp_reply("Please specify a role name.")
            return
        existing = discord.utils.get(guild.roles, name=role_name)
        if existing:
            await send_temp_reply(f"Role '{role_name}' already exists.")
        else:
            await guild.create_role(name=role_name)
            await send_temp_reply(f"Created role: {role_name}")

    elif content.startswith("$role add"):
        if not message.mentions:
            await send_temp_reply("Mention a user to add to your top role.")
            return
        member = message.mentions[0]
        top_role = message.author.top_role
        if top_role >= guild.me.top_role:
            await send_temp_reply("Cannot assign roles higher than my own.")
            return
        await member.add_roles(top_role)
        await send_temp_reply(f"Added {member.display_name} to role {top_role.name}")

    elif content.startswith("$role remove"):
        if not message.mentions:
            await send_temp_reply("Mention a user to remove from your top role.")
            return
        member = message.mentions[0]
        top_role = message.author.top_role
        if top_role >= guild.me.top_role:
            await send_temp_reply("Cannot remove roles higher than my own.")
            return
        await member.remove_roles(top_role)
        await send_temp_reply(f"Removed {member.display_name} from role {top_role.name}")

    if message.content.startswith('!ghostping'):
        if any(role.name.lower() in ['admin'] for role in message.author.roles):
            mentioned_user = message.mentions
            if mentioned_user:
                member = mentioned_user[0]
                if message.author.id not in active_ghostping_tasks:
                    async def ghostping_loop():
                        try:
                            while True:
                                bot_message = await message.channel.send(f'{member.mention}')
                                await bot_message.delete()
                        except asyncio.CancelledError:
                            pass

                    task = asyncio.create_task(ghostping_loop())
                    active_ghostping_tasks[message.author.id] = task
                    await message.channel.send(f"Started ghostping {member.mention}")
                else:
                    await message.channel.send("You are already ghostpinging someone. Use !stopping to stop.", delete_after=2)
                await message.delete()
            else:
                await message.channel.send("You need to mention a user to ghostping.", delete_after=2)
                await message.delete()
        else:
            await message.channel.send("You do not have permission to use this command.", delete_after=2)
            await message.delete()

    if message.content.startswith('!stopping'):
        if any(role.name.lower() in ['admin', 'chair'] for role in message.author.roles):
            if message.author.id in active_ghostping_tasks:
                task = active_ghostping_tasks.pop(message.author.id)
                task.cancel()
                await message.channel.send("Ghostping stopped.", delete_after=2)
            else:
                await message.channel.send("You are not currently ghostpinging anyone.", delete_after=2)
            await message.delete()
        else:
            await message.channel.send("You do not have permission to use this command.", delete_after=2)
            await message.delete()

    
    if message.content.strip() == "!init members":
        await message.delete()

        role = discord.utils.get(message.guild.roles, name="member")
        if not role:
            await send_temp_reply("Role 'member' not found.")
            return

        count = 0
        for member in message.guild.members:
            if member.bot:
                continue
            if member.id == 861800396318048266:
                continue
            if role not in member.roles:
                try:
                    await member.add_roles(role)
                    count += 1
                except discord.Forbidden:
                    pass  # Skip users where role cannot be added

        await send_temp_reply(f"Gave 'member' role to {count} users.")


class KeepAliveHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running.")

def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("", port), KeepAliveHandler)
    print(f"Web server running on port {port}")
    server.serve_forever()

threading.Thread(target=run_web_server).start()
client.run(os.environ["DISCORD_TOKEN"])
