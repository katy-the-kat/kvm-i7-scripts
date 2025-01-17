import random
import string
import subprocess
import paramiko
import discord
from discord.ext import commands
from discord import app_commands

WEBHOOK_URL = ""
TOKEN = ""
SERVER_ID = 1293949144540381185
ALLOWED_ROLES = [1304429499445809203]
NODE_DETAILS = {
    "usa-1": {"ip": "localhost", "username": "host2", "password": "asdwindows"},
}

VPS_PLANS = {
    "sb": {"ram": 1, "cores": 1, "disk": 16},
    "b": {"ram": 4, "cores": 1, "disk": 32},
    "s": {"ram": 8, "cores": 2, "disk": 64},
    "v": {"ram": 16, "cores": 4, "disk": 128},
    "st": {"ram": 32, "cores": 8, "disk": 256},
    "Super Basic": {"ram": 1, "cores": 1, "disk": 16},
    "Basic": {"ram": 4, "cores": 1, "disk": 32},
    "Starter": {"ram": 8, "cores": 2, "disk": 64},
    "Value": {"ram": 16, "cores": 4, "disk": 128},
    "Standard": {"ram": 32, "cores": 8, "disk": 256},
    "1": {"ram": 1, "cores": 1, "disk": 16},
    "2": {"ram": 4, "cores": 1, "disk": 32},
    "3": {"ram": 8, "cores": 2, "disk": 64},
    "4": {"ram": 16, "cores": 4, "disk": 128},
    "5": {"ram": 32, "cores": 8, "disk": 256},
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

def run_shell_command(command):
    result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0:
        raise Exception(result.stderr.strip())
    return result.stdout.strip()

def run_ssh_command(node, command, timeout=60):
    node_config = NODE_DETAILS[node]
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(node_config["ip"], username=node_config["username"], password=node_config["password"], timeout=timeout)
        sudo_command = f"echo '{node_config['password']}' | sudo -n -S {command}"
        stdin, stdout, stderr = ssh.exec_command(sudo_command)
        output = stdout.read().decode().strip()
        error = stderr.read().decode().strip()
        ssh.close()
        if error:
            raise Exception(f"Error: {error}")
        return output
    except Exception as e:
        raise Exception(f"SSH Error on node {node}: {str(e)}")

def user_exists_on_node(node, user):
    try:
        command = f"sudo -S pveum user list | grep -w '{user}'"
        output = run_ssh_command(node, command)
        return bool(output.strip())
    except:
        return False

async def create_proxmox_vm(memory, cores, disk, user, node):
    vps_id = random.randint(1000, 1000000)
    vps_name = f"{user}-{vps_id}"
    user_account = f"{user}@pve"
    password = '2pJ3GZ9e5uQDN8hwTEwLFGYsADsyL'
    try:
        if not user_exists_on_node(node, user_account):
            add_user_command = f"echo '{NODE_DETAILS[node]['password']}' | sudo -n -S pveum user add {user_account} --password {password}"
            run_ssh_command(node, add_user_command)
        vm_clone_command = f"echo '{NODE_DETAILS[node]['password']}' | sudo -n -S qm clone 1000000 {vps_id} --name {vps_name} --full --storage local-2"
        vm_config_command = (
            f"echo '{NODE_DETAILS[node]['password']}' | sudo -n -S qm set {vps_id} --memory {memory * 1024} --cores {cores} "
            f"--virtio2 local-2:{disk},size={disk}G --net0 model=virtio,bridge=vmbr0 --bootdisk virtio2 --boot order=virtio2\;scsi2\;sata0\;sata1\;sata2\;sata3\;sata4\;sata5"
        )
        assign_permissions = f"echo '{NODE_DETAILS[node]['password']}' | sudo -n -S pveum aclmod /vms/{vps_id} --user {user_account} --role PVEVMUser"
        clone_output = run_ssh_command(node, vm_clone_command)
        config_output = run_ssh_command(node, vm_config_command)
        assign_output = run_ssh_command(node, assign_permissions)
        return {"vps_id": vps_id, "user": user_account, "password": password}
    except Exception as e:
        raise Exception(f"Error during VM creation: {str(e)}")

@bot.tree.command(name="create-vps", description="Create a KVM-i7 VPS for a user using VPS plans")
@app_commands.describe(
    plan="The VPS plan to choose",
    customer="The user to DM",
    node="The node to create the VPS on"
)
async def create_vps(interaction: discord.Interaction, plan: str, customer: discord.Member, node: str):
    if node not in NODE_DETAILS:
        await interaction.response.send_message("Invalid node specified.", ephemeral=True)
        return
    if plan not in VPS_PLANS:
        await interaction.response.send_message("Invalid VPS plan specified.", ephemeral=True)
        return
    if not is_authorized(interaction):
        await interaction.response.send_message("You are not authorized to use this command.", ephemeral=True)
        return
    vps_plan = VPS_PLANS[plan]
    memory = vps_plan["ram"]
    cores = vps_plan["cores"]
    disk = vps_plan["disk"]
    await interaction.response.send_message(f"Creating {plan} Plan VPS...", ephemeral=True)
    try:
        result = await create_proxmox_vm(memory, cores, disk, customer.id, node)
        details = f"""
**Your VPS is Ready!**
Access via Webui:

`https://panel-proxmox.kvm-i7.host`
- 👤  **Username:** `{result['user']}`
- 🔑  **Password:** `{result['password']}` 
- 💻  **VPS ID:** `{result['vps_id']}`
- 💡  **Node ID**: `{node}`

**📊 Specs:**
- 🧠 {memory}GB RAM 
- 💾 {disk}GB Storage 
- ⚙️ {cores} cores

**🚀 Quick Start:**
- 📱 Mobile: Use **[ProxMon App](<https://play.google.com/store/apps/details?id=dev.reimu.proxmon&pcampaignid=web_share>)** on the google play store.
- 🖥️ PC: Click the **[link](<https://panel-proxmox.kvm-i7.host>)** and use your **webbrowser**.

💬 **Share Your Experience!**
- Screenshot `neofetch` & post in [Showcase](https://discord.com/channels/1293949144540381185/1305158339298066432).  
- Feedback in [Rate Us](https://discord.com/channels/1293949144540381185/1307723962876170250).  
- Invite friends for upgrades!

:warning: Make sure to reset your account password.
<:_ubuntu:1261893624602296400> To install an OS, Follow this [Youtube Tutorial](<https://www.youtube.com/watch?v=05eAwJtHqnA&ab_channel=Katy>), Else make a ticket and we will install an OS for you.
"""

        await customer.send(details)
        await interaction.followup.send(f"VM created successfully on node {node}.", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"Error: {str(e)}", ephemeral=True)

@bot.event
async def on_ready():
    await bot.tree.sync()
    activity = discord.Activity(type=discord.ActivityType.watching, name="KVM VM Creation")
    await bot.change_presence(activity=activity)

bot.run(TOKEN)
