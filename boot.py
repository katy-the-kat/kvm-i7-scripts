import requests
import discord
import random
import string
import asyncio
import paramiko
import subprocess
from discord.ext import commands
from discord import app_commands

WEBHOOK_URL = ""
TOKEN = ""
SERVER_ID = 1293949144540381185
ALLOWED_ROLES = [1304429499445809203]
TEMPLATE = "local:vztmpl/ubuntu-22.04-standard_22.04-1_amd64.tar.zst"
DISK_SIZE = "4G"
BRIDGE = "vmbr0"
FILE_PATH = "/home/ssh/tokens.txt"
NODE_DETAILS = {
    "nl-1": {"ip": "localhost", "username": "host", "password": ""},
}

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

def is_authorized(interaction):
    if interaction.guild.id != SERVER_ID:
        return False
    user_roles = [role.id for role in interaction.user.roles]
    return any(role in ALLOWED_ROLES for role in user_roles)

def generate_token(length=24):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def send_webhook_log(title, description, color=0x3498db):
    embed = {
        "embeds": [{
            "title": title,
            "description": description,
            "color": color
        }]
    }
    requests.post(WEBHOOK_URL, json=embed)

def save_vps_details(node, token, vps_id, customer_id):
    node_config = NODE_DETAILS[node]
    entry = f"{token},{vps_id}\n"
    remote_file_path = "/home/ssh/tokens.txt"
    save_command = f"echo '{entry}' | sudo tee -a {remote_file_path} > /dev/null"
    try:
        run_ssh_command(node, save_command)
        print(f"Token successfully saved on node {node}")
    except Exception as e:
        raise Exception(f"Failed to save token on node {node}: {str(e)}")

def run_shell_command(command):
    result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    print(f"STDOUT: {result.stdout}")
    if result.returncode != 0:
        print(f"STDERR: {result.stderr}")
        raise Exception(result.stderr.strip())
    return result.stdout.strip()

async def create_proxmox_vps_on_node(memory, cores, disk, customer_id, node):
    vps_id = random.randint(1000, 1000000)
    random_port = random.randint(10000, 1000000)
    vps_name = f"{customer_id}-{random_port}"
    token = generate_token()
    password = 'nopassword'
    memory_mb = memory * 1024
    creation_command = (
        f"sudo pct create {vps_id} {TEMPLATE} --net0 name=eth0,bridge={BRIDGE},firewall=1,ip=dhcp "
        f"--hostname {vps_name} --storage local --rootfs local:{disk} --cores {cores} --memory {memory_mb} "
        f"--password {password} --unprivileged 1 --features nesting=1"
    )
    start_command = f"sudo pct start {vps_id}"
    try:
        run_ssh_command(node, creation_command)
        run_ssh_command(node, start_command)
        save_vps_details(node, token, vps_id, customer_id)
        return {
            "vps_id": vps_id,
            "token": token,
            "random_port": random_port,
            "vps_name": vps_name
        }
    except Exception as e:
        raise e

def run_ssh_command(node, command):
    node_config = NODE_DETAILS[node]
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(node_config["ip"], username=node_config["username"], password=node_config["password"])
        stdin, stdout, stderr = ssh.exec_command(command)
        output = stdout.read().decode().strip()
        error = stderr.read().decode().strip()
        ssh.close()
        if error:
            raise Exception(error)
        return output
    except Exception as e:
        raise Exception(f"SSH Error on node {node}: {str(e)}")

@bot.tree.command(name="create-vps", description="Create a Proxmox VPS on a specified node")
@app_commands.describe(
    memory="Memory in GB",
    cores="Number of CPU cores",
    disk="Disk size (e.g., 4)",
    node="The node to create the VPS on.",
    customer="The user to DM"
)
async def create_vps(interaction: discord.Interaction, memory: int, cores: int, disk: int, customer: discord.Member, node: str):
    if node not in NODE_DETAILS:
        await interaction.response.send_message("Invalid node specified.", ephemeral=True)
        return
    if not is_authorized(interaction):
        await interaction.response.send_message("You are not authorized to use this command.", ephemeral=True)
        return
    await interaction.response.send_message("Starting VPS creation...", ephemeral=True)
    try:
        result = await create_proxmox_vps_on_node(memory, cores, disk, customer.id, node)
        ssh_details = f"""
**Your VPS Instance is Now Active on {node}!**
You can access your VPS instance via SSH:

||`ssh@ssh.kvm-i7.host`||
- **Authentication Token:** ||`{result['token']}`||
- **VPS ID:** ||`{result['vps_id']}`||
- **SSH Creds:** Username ||`ssh`||, Password ||`ssh`||
- **Node ID**: ||`{node}`||

Hardware Info
- Memory: {memory}GB
- Storage: {disk}GB
- Cores: {cores}

**Getting Started:**
- **Mobile:** Download Termius on App-Store (iOS/Android) and connect with SSH.
- **PC:** Open Windows Terminal and enter `ssh ssh@ssh.kvm-i7.host`.
Thank you for choosing **KVM-i7** – The Leading Hosting Service.
        """
        await customer.send(ssh_details)
        await interaction.followup.send(f"VPS created on {node} and details sent via DM.", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"Error: {str(e)}", ephemeral=True)

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"Bot is ready. Logged in as {bot.user}")
    activity = discord.Activity(type=discord.ActivityType.watching, name="KVM-i7")
    await bot.change_presence(activity=activity)

bot.run(TOKEN)
