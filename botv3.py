import subprocess
import discord
import paramiko
import random
import string
import os
import asyncio
from discord.ext import commands
from discord import app_commands

NODES = [
    {"id": "test-1", "ip": "", "tmate": False},
    {"id": "test-2", "ip": "", "tmate": True}
]

remote_user = "root"
remote_password = ""
server_id = 1293949144540381185
allowed_roles = [1304429499445809203]
session_file = "/sessions.txt"
database_file = "database.txt"

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

def is_authorized(interaction):
    return interaction.guild.id == server_id and any(role.id in allowed_roles for role in interaction.user.roles)

def generate_random_password(length=12):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

def find_node_by_id(node_id):
    return next((node for node in NODES if node["id"] == node_id), None)

async def capture_ssh_session_line(stdout):
    while True:
        output = await asyncio.to_thread(stdout.readline)
        if not output:
            break
        output = output.strip()
        if "ssh session:" in output.lower():
            return output.split("ssh session:")[1].strip()
    return None

async def create_docker_container(memory, cores, customer_id, vps_count, node, random_port):
    remote_host = node["ip"]
    container_name = f"vps_{customer_id}_{random_port}"
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        await asyncio.to_thread(ssh.connect, remote_host, username=remote_user, password=remote_password)
        docker_command = f"docker run -itd --privileged  --memory {memory} --cpus {cores} --name {container_name} utmp &"
        stdin, stdout, stderr = await asyncio.to_thread(ssh.exec_command, docker_command)
        if stderr.read():
            return None, "Error in container creation."
        if node["tmate"]:
            exec_tmate_command = f"docker exec {container_name} tmate -F"
            stdin, stdout, stderr = await asyncio.to_thread(ssh.exec_command, exec_tmate_command)
            tmate_session = await capture_ssh_session_line(stdout)
            if not tmate_session:
                return None, "Error retrieving tmate session."
            return container_name, remote_host, tmate_session, None
        else:
            ssh_port_command = f"docker run -itd --privileged  -p {random_port}:22 --memory {memory} --cpus {cores} --name {container_name} utmp"
            await asyncio.to_thread(ssh.exec_command, ssh_port_command)
            random_password = generate_random_password()
            password_command = f"docker exec {container_name} sh -c \"echo root:{random_password} | chpasswd\""
            await asyncio.to_thread(ssh.exec_command, password_command)
            return container_name, remote_host, random_port, random_password
    finally:
        ssh.close()

@bot.tree.command(name="deploy", description="Deploy a customer VPS on a specific node")
@app_commands.describe(memory="Memory limit (e.g., 512m, 1g)", cores="Number of CPU cores", customer="The user to DM", node_id="Node ID (e.g., usa-1)")
async def deploy_customer(interaction: discord.Interaction, memory: str, cores: str, customer: discord.Member, node_id: str):
    if not is_authorized(interaction):
        await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
        return
    node = find_node_by_id(node_id)
    if not node:
        await interaction.response.send_message(f"Invalid node ID: {node_id}", ephemeral=True)
        return
    await interaction.response.send_message("VPS creation started. You'll receive the details soon.", ephemeral=True)
    async def create_and_notify():
        customer_id = str(customer.id)
        vps_count = random.randint(1, 1024)
        random_port = random.randint(1024, 65535)
        result = await create_docker_container(memory, cores, customer_id, vps_count, node, random_port)
        if not result or len(result) < 3:
            await interaction.followup.send("Failed to create the VPS.", ephemeral=True)
            return
        container_name, remote_host, ssh_info, password = result
        if node["tmate"]:
            ssh_details = f"""**Your VPS is Ready!**
Access via SSH:

`{ssh_info}`
- 🌐 **Shared-IPv4 Usage:** Use the `port` command to add ports
- 💾 **Memory:** {memory}GB
- 📗 **Cores:** {cores}

**🚀 Quick Start:**
- 📱 Mobile: Use **Termux** to connect. (Termius won't work)
- 🖥️ PC: Open `cmd` and paste the command in.

💬 **Share Your Experience!**
- 🖼️ Screenshot `neofetch` & post in [Showcase](https://discord.com/channels/1293949144540381185/1334682558507647007).  
- ⭐ Feedback in [Rate Us](https://discord.com/channels/1293949144540381185/1334682666301263883).
"""
        else:
            ssh_details = f"""**Your VPS is Ready!**
Access via SSH:

`ssh root@{remote_host} -p {ssh_info}`
- 👤 **Username:** `root`
- 🔑 **Password:** `{password}`
- 🌐 **Shared-IPv4 Usage**: Use the `port` command to add ports

**🚀 Quick Start:**
- 📱 Mobile: Use **Termius** to connect.
- 🖥️ PC: Open `cmd` and paste the command in.

💬 **Share Your Experience!**
- 🖼️ Screenshot `neofetch` & post in [Showcase](https://discord.com/channels/1293949144540381185/1334682558507647007).  
- ⭐ Feedback in [Rate Us](https://discord.com/channels/1293949144540381185/1334682666301263883).
"""

        try:
            await customer.send(ssh_details)
        except discord.Forbidden:
            await interaction.followup.send("Failed to DM user. Ensure their DMs are open.", ephemeral=True)
        else:
            await interaction.followup.send("VPS successfully created and details sent via DM.", ephemeral=True)
    await create_and_notify()

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f'Bot is ready. Logged in as {bot.user}')
    activity = discord.Activity(type=discord.ActivityType.watching, name="VPS Instances")
    await bot.change_presence(activity=activity)

bot.run('')
