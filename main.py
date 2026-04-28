from enum import member
import discord
from discord.ext import commands, tasks
from discord import app_commands
import json
import os
import asyncio
from discord import ButtonStyle, Interaction
from discord.ui import View, Button, Modal, TextInput, Select
from datetime import timedelta
import time
import re
import pymysql
import io
import traceback
bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())

TICKET_CATEGORY_ID = 1498367118461108274
TICKET_MANAGER_ROLE_ID = 1498368834057535519
TICKET_LOG_CHANNEL_ID = 1478139098463076404  

LSPD_ROLE_ID = 1490821864145027314

COOLDOWN_PERIOD = 15 * 24 * 60 * 60  
application_cooldowns = {} 

def is_on_cooldown(user_id):
    """Check if a user is on cooldown."""
    current_time = time.time()
    if user_id in application_cooldowns:
        last_submission_time = application_cooldowns[user_id]
        if current_time - last_submission_time < COOLDOWN_PERIOD:
            return True
    return False


def set_cooldown(user_id):
    """Set the cooldown for a user."""
    application_cooldowns[user_id] = time.time()

@bot.event
async def on_ready():
    await  bot.change_presence(activity=discord.activity.Game(name="Reloaded RolePlay"), status=discord.Status.online)
    bot.add_view(TicketView())
    bot.add_view(CloseTicketView())
    print("Είμαι Ξύπνιος")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} slash commands")
    except Exception as e:
        print(e)

# =========================
# DATABASE (HeidiSQL)
# =========================

db = pymysql.connect(
    host="sql7.freesqldatabase.com",
    user="sql7824617",
    password="ydSn3WRa8Q",
    database="sql7824617",
    port=3306,
    cursorclass=pymysql.cursors.Cursor,
    autocommit=True
)

cursor = db.cursor()
print("DB CONNECTED")
# =========================
# ACTIVE CACHE
# =========================

active_tickets = {}

# =========================
# TRANSCRIPT SYSTEM
# =========================

async def get_transcript(channel: discord.TextChannel):
    messages = [msg async for msg in channel.history(oldest_first=True, limit=None)]

    transcript = []
    transcript.append(f"=== TICKET TRANSCRIPT #{channel.name} ===\n")

    for msg in messages:
        time = msg.created_at.strftime("%Y-%m-%d %H:%M:%S")

        content = msg.content if msg.content else ""

        # embeds (basic text extraction)
        embeds_text = ""
        if msg.embeds:
            for embed in msg.embeds:
                if embed.title:
                    embeds_text += f"[EMBED TITLE] {embed.title}\n"
                if embed.description:
                    embeds_text += f"[EMBED DESC] {embed.description}\n"

        # attachments
        attachments = ""
        if msg.attachments:
            attachments = " | ".join([a.url for a in msg.attachments])

        transcript.append(
            f"[{time}] {msg.author} ({msg.author.id})\n"
            f"CONTENT: {content}\n"
            f"{'EMBEDS: ' + embeds_text if embeds_text else ''}"
            f"{'ATTACHMENTS: ' + attachments if attachments else ''}\n"
            f"{'-'*50}"
        )

    transcript.append("\n=== END OF TRANSCRIPT ===")

    return "\n".join(transcript)

# =========================
# CLEANUP SYSTEM
# =========================

async def cleanup_tickets(guild: discord.Guild):
    cursor.execute("SELECT user_id, channel_id FROM tickets")
    rows = cursor.fetchall()

    for user_id, channel_id in rows:
        channel = guild.get_channel(channel_id)

        if channel is None:
            cursor.execute("DELETE FROM tickets WHERE user_id=%s", (user_id,))
            db.commit()



   ################## Ranks

@bot.command()
@commands.has_permissions(administrator=True)  
async def post_ranks(ctx):
  
    embed = discord.Embed(
        title="",
        description="# <:policebadge:1496988066269761596>〢 RANK PD \n **Commissioner (00-XX)**\n"
                    "**Chief of Police (01-XX)**\n"
                    "**Assistant Chief of Police (02-XX)**\n"
                    "**Commander (03-XX)**\n"
                    "**Captain (04-XX)**\n"
                    "**Lieutenant II (05-XX)**\n"
                    "**Lieutenant I (06-XX)**\n"
                    "**Detective llI (07-XX)**\n"
                    "**Detective ll (08-XX)**\n"
                    "**Detective I (09-XX)**\n"
                    "**Sergeant ll (10-XX)**\n"
                    "**Sergeant l (11-XX)**\n"
                    "**Corporal (12-XX)**\n"
                    "**Officer III (13-XX)**\n"
                    "**Officer II (14-XX)**\n"
                    "**Officer I (15-XX)**\n",
        color=discord.Color.dark_red()
    )
    embed.set_footer(text="Reloaded Roleplay")
    await ctx.send(embed=embed)


   ################## GENERAL RULES

@bot.command()
@commands.has_permissions(administrator=True)  
async def generalrules(ctx):
  
    embed = discord.Embed(
        title="",
        description="# <a:shieldtick:1498110046888788119>〢 Κανόνες του Discord \n **Όλα τα μέλη του Discord Server μας υποχρεούνται να τηρούν τους παρακάτω κανονισμούς.**\n"
        "# <a:number1p:1498110257803690044> Γενικοί Κανόνες Server\n"
        "**• Σεβασμός προς όλα τα μέλη.**\n"
        "**• Απαγορεύονται προσβολές, ρατσισμός και τοξική συμπεριφορά.**\n"
        "**• Απαγορεύεται το spam, flood και άσχετο περιεχόμενο.**\n"
        "**• Ακολουθείτε πάντα τις οδηγίες των admins/mods.**\n"
        "**• Απαγορεύεται η διαφήμιση χωρίς άδεια.**\n"
        "**• Μην κάνετε abuse τα roles ή τα permissions.**\n\n"

        "# <a:number2p:1498110620489482270> Communication Rules\n"
        "**• Μην μιλάτε πάνω από άλλους στα voice channels.**\n"
        "**• Χρησιμοποιείτε push-to-talk αν υπάρχει θόρυβος.**\n"
        "**• Απαγορεύονται ear rape / δυνατοί ήχοι / trolls.**\n\n",
        color=discord.Color.dark_red()
    )
    embed.set_footer(text="Reloaded Roleplay")
    await ctx.send(embed=embed)


   ################## IN-GAME RULES

@bot.command()
@commands.has_permissions(administrator=True)  
async def post_igrules(ctx):
  
    embed = discord.Embed(
        title="",
        description="# <:paper:1498051675456274682>〢 In-Game Rules \n **Όλα τα μέλη του Los Santos Police Department υποχρεούνται να τηρούν τους παρακάτω κανονισμούς εντός και εκτός υπηρεσίας.**\n"
        "# <a:number1:1496977899650158774> Γενικοί Κανόνες Συμπεριφοράς\n"
        "**• Σεβασμός προς όλους**\n"
        "**• Απαγορεύονται προσβολές, βρισιές, ρατσιστικά ή σεξιστικά σχόλια.**\n"
        "**• Κάθε πρόβλημα λύνεται μέσω της ιεραρχίας**\n\n"
        "# <a:number2:1497004268060676178> Υπακοή στην ιεραρχία\n"
        "**• Η υπακοή προς ανώτερους βαθμούς ειναι υποχρεωτική**\n\n"
        "**• Οποιαδήποτε διαφωνία λύνεται μέσω ticket ή σε private channel με staff.**\n\n"
        "# <a:number3:1497006504115572766> RP Συμπεριφορά\n"
        "**• Διατηρείτε σοβαρό και ρεαλιστικό roleplay.**\n"
        "**• Απαγορεύεται το trolling ή το fail RP.**\n"
        "**• Δεν μιλάμε OOC σε IC κανάλια.**\n"
        "# <a:number4:1498024591770259617> Αναφορές και παράπονα\n"
        "**• Απαγορεύονται τα δημόσια arguments.**\n"
        "# <a:number5:1498026699680649277> Voice κανόνες\n"
        "**• Push-to-talk όπου χρειάζεται.**\n"
        "**• Όχι μουσική, θόρυβοι ή mic spam στα duty channels.**\n"
        "**• Μικρές και καθαρές κλήσεις**\n"
        "**• Όχι άσχετες συζητήσεις σε επιχειρήσεις**\n"
        "# <a:number6:1498032644179628083> Evidence & Reports\n"
        "**• Όλες οι σοβαρές υποθέσεις χρειάζονται report**\n"
        "**• Καταγραφή evidence / screenshots όπου απαιτείται**\n"
        "**• Ψεύτικες αναφορές επιφέρουν ποινή**\n"
        "# <a:poines:1498033632693059594> Ποινές\n"
        "**• 1η παράβαση: προειδοποίηση**\n"
        "**• 2η παράβαση: mute / suspension**\n"
        "**• 3η παράβαση: demotion ή αποβολή από το LSPD**\n\n"
        "# <:sheriffbadge:1498048774189351063> To Protect And To Serve\n",
        color=discord.Color.dark_red()
    )
    embed.set_footer(text="Reloaded Roleplay")
    await ctx.send(embed=embed)


   ################## RULES

@bot.command()
@commands.has_permissions(administrator=True)  
async def post_rules(ctx):
  
    embed = discord.Embed(
        title="",
        description="# <a:police:1496977575581454367>〢 Κανόνες LSPD Discord \n **Όλα τα μέλη του Los Santos Police Department υποχρεούνται να τηρούν τους παρακάτω κανονισμούς εντός και εκτός υπηρεσίας.**\n"
        "# <a:number1:1496977899650158774> Γενικοί Κανόνες Συμπεριφοράς\n"
        "**• Σεβασμός προς όλα τα μέλοι του Server**\n"
        "**• Απαγορεύονται προσβολές, βρισιές, ρατσιστικά ή σεξιστικά σχόλια.**\n"
        "**• Κάθε πρόβλημα λύνεται μέσω της ιεραρχίας**\n\n"
        "# <a:number2:1497004268060676178> Υπακοή στην ιεραρχία\n"
        "**• Η υπακοή προς ανώτερους βαθμούς ειναι υποχρεωτική**\n\n"
        "# <a:number3:1497006504115572766> Χρήση σωστών καναλιών\n"
        "**• Χρησιμοποιείτε το κατάλληλο κανάλι για κάθε θέμα.**\n"
        "**• Απαγορεύεται το spam σε text ή voice channels.**\n"
        "# <a:number4:1498024591770259617> Αναφορές και παράπονα\n"
        "**• Για οποιoδίποτε παράπονο θέλετε να κάνετε αναφερθείτε στους ανωτερους σας (Captain)**\n"
        "# <a:number5:1498026699680649277> Activity / Παρουσία\n"
        "**• Όλα τα μέλη του LSPD πρέπει να είναι ενεργά.**\n"
        "**• Απουσία άνω των Χ ημερών χωρίς ενημέρωση μπορεί να οδηγήσει σε demotion ή kick. [Ενημερώνουμε εδώ👆🏼](https://discord.com/channels/1472021824861634594/1477687266531868895)**\n"
        "# <a:number6:1498032644179628083> Εμπιστευτικότητα\n"
        "**• Πληροφορίες επιχειρήσεων, κωδικών και εσωτερικών συνομιλιών δεν κοινοποιούνται εκτός LSPD.**\n"
        "**• Leak σε screenshots ή συνομιλίες = άμεσο ban.**\n"
        "# <a:number7:1498032908202676274> Στολές και βαθμοί\n"
        "**• Υποχρεωτική χρήση της σωστής στολής και rank tags.**\n"
        "**• Απαγορεύεται η αυθαίρετη αλλαγή nickname ή rank.**\n"
        "# <a:number8:1498048090656211174> Duty / Off Duty\n"
        "**•  Όταν είσαι on duty παίζεις αποκλειστικά Police RP**\n\n"
        "# <a:poines:1498033632693059594> Ποινές\n"
        "**• 1η παράβαση: προειδοποίηση**\n"
        "**• 2η παράβαση: mute / suspension**\n"
        "**• 3η παράβαση: demotion ή αποβολή από το LSPD**\n\n"
        "# <:sheriffbadge:1498048774189351063> To Protect And To Serve\n",
        color=discord.Color.dark_red()
    )
    embed.set_footer(text="Reloaded Roleplay")
    await ctx.send(embed=embed)

   ################## ARMORY

@bot.command()
@commands.has_permissions(administrator=True)  
async def post_armory(ctx):
  
    embed = discord.Embed(
        title="",
        description="# <:pistol:1496997977200267365>〢 Armory \n **Officer (I, II, III) : Smg, Pistol, Nightstick, Taser,Flashlight**\n\n"
        "**Corporal : Carbine Rifle , SMG, Pistol, Nightstick, Taser, Flashlight**\n\n"
        "**Sergeant (I, II) : SMG, Pistol, Nightstick, Taser, Flashlight**\n\n"
        "**Detective (I, II) : SMG, Pistol, Nightstick, Taser, Flashlight**\n\n"
        "**Detective (III) : Carbine Rifle , SMG, Pistol, Nightstick, Taser, Flashlight**\n\n"
        "**Lieutenant (I, II) : Carbine Rifle , SMG, Pistol, Nightstick, Taser, Flashlight**\n\n"
        "**Captain : Carbine Rifle , SMG, Pistol, Nightstick, Taser, Flashlight**\n\n"
        "**Commander : Carbine Rifle , SMG, Pistol, Nightstick, Taser, Flashlight**\n\n"
        "**Assistant Chief of Poilice : Carbine Rifle , SMG, Pistol, Nightstick, Taser, Flashlight**\n\n"
        "**Chief of police : Carbine Rifle , SMG, Pistol, Nightstick, Taser, Flashlight**\n\n"
        "**Commissioner : Carbine Rifle , SMG, Pistol, Nightstick, Taser, Flashlight**\n\n",
        color=discord.Color.dark_red()
    )
    embed.set_footer(text="Reloaded Roleplay")
    await ctx.send(embed=embed)

   ################## SPECIAL RULES

@bot.command()
async def specialrules(ctx):
    channel1 = bot.get_channel(1498055536233549864)
    channel2 = bot.get_channel(1498055701321351188)
    channel3 = bot.get_channel(1498065437794242590)

    embed1 = discord.Embed(
        title="",
        description="# <a:police:1496977575581454367>〢 Κανόνες Swat Reloaded Roleplay \n **Όλα τα μέλη του Los Santos Police Department του τομέα των Swat υποχρεούνται να τηρούν τους παρακάτω κανονισμούς εντός υπηρεσίας.**\n"
        "# <a:number1:1496977899650158774> Τί αναλαμβάνετε\n"
        "**  Ο τομέας των Swat αναλαμβάνει :**\n"
        "**• Ομηρίες**\n"
        "**• Bank robbery**\n"
        "**• Ηeavily armed suspects**\n"
        "**• Ηigh-risk warrants**\n\n"
        "# <a:number2:1497004268060676178> Έγκριση \n"
        "**• Απαιτείται έγκριση από Captain των Swat και πάνω**\n\n"
        "# <a:number3:1497006504115572766> Ρουχισμός\n"
        "**• Υποχρεωτική είναι η χρήση tactical gear.**\n"
        "# <a:number4:1498024591770259617> Περιπολίες\n"
        "**• Δεν αναλαμβάνετε απλές περιπολίες.**\n"
        "# <a:number5:1498026699680649277> Shooting\n"
        "**• Shoot-to-kill μόνο σε άμεση απειλή**\n",
        color=discord.Color.blue()
    )
    embed1.set_footer(text="Reloaded Roleplay")

    embed2 = discord.Embed(
        title="",
        description="# <a:police:1496977575581454367>〢 Κανόνες Detective Reloaded Roleplay \n **Όλα τα μέλη του Los Santos Police Department του τομέα των Detective υποχρεούνται να τηρούν τους παρακάτω κανονισμούς εντός υπηρεσίας.**\n"
        "# <a:number1:1496977899650158774> Τί αναλαμβάνετε\n"
        "**  Ο τομέας των Detective αναλαμβάνει :**\n"
        "**• Murder cases**\n"
        "**• Organized crime**\n"
        "**• Narcotics**\n"
        "**• Long investigations**\n\n"
        "# <a:number2:1497004268060676178> Case Reports \n"
        "**• Υποχρεωτικό case report για κάθε υπόθεση**\n\n"
        "# <a:number3:1497006504115572766> Evidence Chain\n"
        "**• Evidence chain πρέπει να είναι πλήρης**\n"
        "# <a:number4:1498024591770259617> Detective Badge\n"
        "**• Απαγορεύεται η χρήση Detective Badge για Abuse**\n"
        "# <a:number5:1498026699680649277> Operations\n"
        "**• UnderCover Operations μόνο με έγκριση Captain+**\n"
        "# <a:number6:1498032644179628083> Identity\n"
        "**•  Η ταυτότητα του officer δεν αποκαλύπτεται χωρίς λόγο**\n"
        "# <a:number7:1498032908202676274> Απαγορεύεται\n"
        "**• Απαγορεύεται UC για προσωπικό όφελος**\n"
        "# <a:number8:1498048090656211174> Report\n"
        "**• Κάθε operation χρειάζεται detailed report**\n\n",
        color=discord.Color.blue()
    )
    embed2.set_footer(text="Reloaded Roleplay")

    embed3 = discord.Embed(
        title="",
        description="# <a:police:1496977575581454367>〢 Κανόνες FBI Reloaded Roleplay \n **Όλα τα μέλη του Los Santos Police Department του τομέα των FBI υποχρεούνται να τηρούν τους παρακάτω κανονισμούς εντός υπηρεσίας.**\n"
        "# <a:number1:1496977899650158774> Συμπεριφορά\n"
        "**• Σεβασμός σε όλους και σωστή συμπεριφορά.**\n"
        "**• Υποχρεωτική τήρηση ιεραρχίας και εντολών ανωτέρων.**\n"
        "**• Serious RP μόνο — απαγορεύονται troll / meme συμπεριφορές.**\n"
        "**• Απαγορεύονται metagaming, powergaming και failRP.**\n"
        "# <a:number2:1497004268060676178> Radio \n"
        "**• Χρήση radio με σωστά callsigns και clear communication.**\n\n"
        "# <a:number3:1497006504115572766> Έγκριση\n"
        "**• Όλες οι επιχειρήσεις γίνονται με έγκριση supervisor.**\n"
        "# <a:number4:1498024591770259617> Arrest / Raid\n"
        "**• Arrest / Raid μόνο με αποδείξεις και σωστό RP.**\n"
        "# <a:number5:1498026699680649277> Όπλο\n"
        "**• Όπλο τραβιέται μόνο σε πραγματική απειλή.**\n"
        "# <a:number6:1498032644179628083> Απόρρητο\n"
        "**• Undercover πληροφορίες παραμένουν απόρρητες.**\n"
        "# <a:number7:1498032908202676274> Κατάχρηση\n"
        "**• Abuse εξουσίας ή corruption χωρίς άδεια = άμεση αποβολή.**\n",
        color=discord.Color.blue()
    )
    embed3.set_footer(text="Reloaded Roleplay")


    await channel1.send(embed=embed1)
    await channel2.send(embed=embed2)
    await channel3.send(embed=embed3)



######### TICKET
class TicketSelect(Select):
    def __init__(self):
        options = [
            discord.SelectOption(
                label="Report an Officer",
                description="Κάντε Report έναν Αστυνομικό",
                emoji="<a:siren:1498369700025995294>"
            ),
            discord.SelectOption(
                label="Report LSPD",
                description="Κάντε Report το LSPD",
                emoji="<a:ticketpd:1498375774258856079>"
            ),
            discord.SelectOption(
                label="Other",
                description="Άνοιξε ένα Ticket για κάτι άλλο",
                emoji="<a:question:1498376468550647978>"
            )
        ]

        super().__init__(
            placeholder="Ανοίξτε ένα Ticket...",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="ticket_select"
        )

    async def callback(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer(ephemeral=True)

            guild = interaction.guild
            user_id = interaction.user.id

            category = discord.utils.get(guild.categories, id=TICKET_CATEGORY_ID)
            if category is None:
                return await interaction.followup.send(
                    "❌ Δεν βρέθηκε category για tickets.",
                    ephemeral=True
                )

            cursor.execute("SELECT channel_id FROM tickets WHERE user_id=%s", (user_id,))
            existing = cursor.fetchone()

            if existing:
                channel = guild.get_channel(existing[0])
                if channel:
                    return await interaction.followup.send(
                        f"⚠️ Έχετε ήδη ανοικτό ticket: {channel.mention}",
                        ephemeral=True
                    )
                else:
                    cursor.execute("DELETE FROM tickets WHERE user_id=%s", (user_id,))
                    db.commit()

            selected_option = self.values[0]

            role = guild.get_role(TICKET_MANAGER_ROLE_ID)

            username = re.sub(r'[^a-z0-9-]', '', interaction.user.name.lower())
            channel_name = f"ticket-{username}"

            overwrites = {
                guild.default_role: discord.PermissionOverwrite(view_channel=False),
                interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True),
            }

            if role:
                overwrites[role] = discord.PermissionOverwrite(view_channel=True, send_messages=True)

            ticket_channel = await guild.create_text_channel(
                name=channel_name,
                category=category,
                overwrites=overwrites
            )

            cursor.execute(
                "INSERT INTO tickets (user_id, channel_id, type) VALUES (%s, %s, %s)",
                (user_id, ticket_channel.id, selected_option)
            )
            db.commit()

            embed = discord.Embed(
                title="🎟️ Ticket Opened",
                description=(
                    f"👋 Γεια σας {interaction.user.mention}, το ticket σας δημιουργήθηκε!\n"
                    f"Το **{selected_option}** αίτημά σας θα απαντηθεί σύντομα.\n\n"
                    "**Παρακαλώ να έχετε υπομονή!**"
                ),
                color=discord.Color.blue(),
                timestamp=discord.utils.utcnow()
            )

            embed.add_field(name="👤 Χρήστης", value=interaction.user.mention, inline=True)
            embed.add_field(
                name="📅 Ημερομηνία Δημιουργίας",
                value=discord.utils.format_dt(interaction.created_at, style='F'),
                inline=True
            )
            embed.add_field(name="🔍 Τύπος Ticket", value=f"**{selected_option}**", inline=True)

            embed.add_field(
                name="⚠️ Ειδοποίηση",
                value="Παρακαλώ μην κάνετε συνεχόμενα ping.",
                inline=False
            )

            embed.add_field(
                name="📜 Κατευθυντήριες Οδηγίες",
                value="Να είστε ευγενικοί και να ακολουθείτε τους κανόνες.",
                inline=False
            )

            embed.set_thumbnail(url=interaction.user.display_avatar.url)

            if guild.icon:
                embed.set_footer(text="Σύστημα Υποστήριξης Ticket", icon_url=guild.icon.url)
            else:
                embed.set_footer(text="Σύστημα Υποστήριξης Ticket")

            await ticket_channel.send(
                content=interaction.user.mention,
                embed=embed,
                view=CloseTicketView()
            )

            await interaction.followup.send(
                f"✅ Ticket created: {ticket_channel.mention}",
                ephemeral=True
            )

        except Exception as e:
            print(traceback.format_exc())
            await interaction.followup.send(
        f"❌ Error creating ticket:\n```{e}```",
        ephemeral=True
    )
# =========================
# CLOSE BUTTON
# =========================

class CloseTicketButton(Button):
    def __init__(self):
        super().__init__(
            label="Κλείσιμο Αιτήματος",
            style=discord.ButtonStyle.danger,
            emoji="🔒",
            custom_id="close_ticket_button"
        )

    async def callback(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer(ephemeral=True)

            channel = interaction.channel

            cursor.execute(
                "SELECT user_id, type FROM tickets WHERE channel_id=%s",
                (channel.id,)
            )
            data = cursor.fetchone()

            if not data:
                await channel.delete()
                return

            user_id, ticket_type = data

            # =========================
            # TRANSCRIPT
            # =========================
            transcript = await get_transcript(channel)

            file = discord.File(
                fp=io.BytesIO(transcript.encode("utf-8")),
                filename=f"ticket-{channel.id}.txt"
            )

            # =========================
            # LOG CHANNEL
            # =========================
            log_channel = bot.get_channel(TICKET_LOG_CHANNEL_ID)

            if log_channel:
                await log_channel.send(
                    content=(
                        f"📁 **Ticket Closed**\n"
                        f"👤 User: <@{user_id}>\n"
                        f"🎫 Type: {ticket_type}\n"
                        f"🏷️ Channel: #{channel.name}"
                    ),
                    file=file
                )

            # =========================
            # DB SAVE
            # =========================
            cursor.execute(
                "INSERT INTO closed_tickets (user_id, channel_id, type, transcript) VALUES (%s, %s, %s, %s)",
                (user_id, channel.id, ticket_type, transcript)
            )

            cursor.execute(
                "DELETE FROM tickets WHERE channel_id=%s",
                (channel.id,)
            )

            db.commit()

            await interaction.followup.send("🔒 Closing ticket...", ephemeral=True)

            await channel.delete()

        except Exception as e:
            print("Ticket close error:", e)
            try:
                await interaction.followup.send("❌ Failed to close ticket", ephemeral=True)
            except:
                pass
# =========================
# VIEWS
# =========================

class CloseTicketView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(CloseTicketButton())

class TicketView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketSelect())

# =========================
# STAFF PANEL
# =========================

class StaffPanel(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🔄 Cleanup", style=discord.ButtonStyle.secondary)
    async def cleanup(self, interaction: discord.Interaction, button: Button):
        await cleanup_tickets(interaction.guild)
        await interaction.response.send_message("Cleanup done", ephemeral=True)

    @discord.ui.button(label="📊 Active", style=discord.ButtonStyle.primary)
    async def active(self, interaction: discord.Interaction, button: Button):
        cursor.execute("SELECT COUNT(*) FROM tickets")
        await interaction.response.send_message(
            f"Active: {cursor.fetchone()[0]}",
            ephemeral=True
        )

    @discord.ui.button(label="📁 Closed", style=discord.ButtonStyle.success)
    async def closed(self, interaction: discord.Interaction, button: Button):
        cursor.execute("SELECT COUNT(*) FROM closed_tickets")
        await interaction.response.send_message(
            f"Closed: {cursor.fetchone()[0]}",
            ephemeral=True
        )


@bot.command()
@commands.has_permissions(administrator=True)
async def post_ticket(ctx):
    embed = discord.Embed(
        title="",
        description=(
            "# <a:ticket:1498373029573693473> Ticket \n"
            "Για οποιοδίποτε πιθανό πρόβλημα έχετε όπως: \n> ```Officer Report``` \n> ```LSPD Report``` \n> ```Other```\n"
            "Ανοίξτε ένα ticket ώστε να επικοινωνήσετε μαζί μας.\n"
        ),
        color=discord.Color.dark_red()
    )
    embed.set_footer(text="Reloaded Roleplay")

    await ctx.send(embed=embed, view=TicketView())

# =========================
# AUTO CLEANUP LOOP
# =========================

@tasks.loop(minutes=10)
async def auto_cleanup():
    for guild in bot.guilds:
        await cleanup_tickets(guild)


# ========================
# APPLICATIONS

class LSPDApplicationModal(Modal):
    def __init__(self, user: discord.Member):
        super().__init__(title="Αίτηση για την ένταξη σας στο σώμα του LSPD")
        self.user = user

        self.name = TextInput(label="Όνομα (IRL)", placeholder="Ποιο είναι το ονοματεπώνυμό σας (IRL)", required=True)
        self.age = TextInput(label="Ηλικία",style=discord.TextStyle.paragraph, placeholder="Ποία είναι η ηλικία σας ", required=True)
        self.hours = TextInput(label="Ώρες FiveM", placeholder="Πόσες ώρες έχετε στην FiveM", required=True)

        self.add_item(self.name)
        self.add_item(self.age)
        self.add_item(self.hours)

    async def on_submit(self, interaction: discord.Interaction):
        application_channel = interaction.guild.get_channel(1490825114244091995)  
        if is_on_cooldown(self.user.id):
            cooldown_remaining = int(COOLDOWN_PERIOD - (time.time() - application_cooldowns[self.user.id]))
            days_remaining = cooldown_remaining // (24 * 60 * 60)  
            await interaction.response.send_message(f"Μπορείτε να ξανακάνετε αίτηση σε {days_remaining} μέρες.", ephemeral=True)
            return

        set_cooldown(self.user.id)  

        embed = discord.Embed(
    title="🚓 Νέα Αίτηση LSPD",
    description=(
        f"👋 Υποβλήθηκε νέα αίτηση από {self.user.mention}\n"
        "Παρακαλώ ελέγξτε τα στοιχεία και επιλέξτε ενέργεια."
    ),
    color=discord.Color.dark_red(),
    timestamp=discord.utils.utcnow()
)

        embed.add_field(name="👤 Όνομα (IRL)", value=f"**{self.name.value}**", inline=True)
        embed.add_field(name="🎂 Ηλικία", value=f"**{self.age.value}**", inline=True)
        embed.add_field(name="🕒 Ώρες FiveM", value=f"**{self.hours.value}**", inline=True)

        embed.add_field(
    name="📌 Κατάσταση",
    value="🟡 Σε αναμονή αξιολόγησης",
    inline=False
)

        embed.set_thumbnail(url=self.user.display_avatar.url)

        if interaction.guild.icon:
            embed.set_footer(
        text="LSPD Application System",
        icon_url=interaction.guild.icon.url
    )
        else:
            embed.set_footer(text="LSPD Application System")

        await application_channel.send(
    content=self.user.mention,
    embed=embed,
    view=LSPDApplicationReviewButtons(self.user)
)

        await interaction.response.send_message(
    "✅ Η αίτηση σας έχει υποβληθεί!",
    ephemeral=True
)

# BUTTONS

class LSPDApplicationReviewButtons(discord.ui.View):
    def __init__(self, user: discord.Member = None):
        super().__init__(timeout=None)  
        self.user = user  

    @discord.ui.button(label="Αποδοχή", style=discord.ButtonStyle.success, custom_id="accept_lspd")
    async def accept_button_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        applicant = await self.get_applicant(interaction)
        if not applicant:
            embed = discord.Embed(
                title="❌ Error",
                description="Applicant not found.",
                color=discord.Color.red()
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        role = interaction.guild.get_role(LSPD_ROLE_ID)
        if role:
            await applicant.add_roles(role)
        
        embed = discord.Embed(
    title="✅ Αίτηση Εγκρίθηκε",
    description=f"👮 {applicant.mention}, Η αίτηση έγινε αποδεκτή!",
    color=discord.Color.blue(),
    timestamp=discord.utils.utcnow()
)

        embed.add_field(
    name="📌 Κατάσταση",
    value="🟢 Εγκρίθηκε",
    inline=True
)

        embed.add_field(
    name="👤 Υπεύθυνος",
    value=interaction.user.mention,
    inline=True
)

        embed.set_thumbnail(url=applicant.display_avatar.url)

        await interaction.response.send_message(embed=embed)
        await interaction.message.edit(view=None)

        try:
            dm_embed = discord.Embed(
                title="🚓 LSPD Recruitment",
                description="# <a:bsiren:1498453102167068842> 〢 Η Αίτηση Εγκρίθηκε\n\n"
                "🎉 Συγχαρητήρια! Έχετε γίνει δεκτός στο LSPD.\n\n"
                        "```Για να μάθετε πληροφορίες σχετικά με το πότε θα γίνει το εντατικό μάθημα για την ένταξη σας στο LSPD παρακαλώ πολύ περιμένετε να βγεί ανακοίνωση απο τα υψηλόβαθμα μέλοι του LSPD στον Discord Server του Reloaded PD.```",
                color=discord.Color.blue(),
                timestamp=discord.utils.utcnow()
            )
            dm_embed.set_thumbnail(url=applicant.display_avatar.url)
            await applicant.send(embed=dm_embed)
        except discord.Forbidden:
            error_embed = discord.Embed(
                title="❌ Error",
                description=f"Could not send a DM to {applicant.mention}.",
                color=discord.Color.red()
            )
            await interaction.channel.send(embed=error_embed)

@discord.ui.button(label="Απόρριψη", style=discord.ButtonStyle.danger, custom_id="deny_lspd")
async def deny_button_callback(self, interaction: discord.Interaction, button: discord.ui.Button):

    await interaction.response.defer()

    # ✅ Πάρε τον σωστό applicant από το View
    applicant = self.user

    if not applicant:
        return await interaction.followup.send(
            "❌ Applicant not found.",
            ephemeral=True
        )

    # 🔴 Main embed
    embed = discord.Embed(
        title="❌ Αίτηση Απορρίφθηκε",
        description=f"{applicant.mention}, η αίτησή σας δεν έγινε αποδεκτή.",
        color=discord.Color.red(),
        timestamp=discord.utils.utcnow()
    )

    embed.add_field(name="📌 Κατάσταση", value="🔴 Απορρίφθηκε", inline=True)
    embed.add_field(name="👤 Υπεύθυνος", value=interaction.user.mention, inline=True)

    embed.set_thumbnail(url=applicant.display_avatar.url)

    await interaction.followup.send(embed=embed)

    # ❌ Disable buttons (καλύτερο από remove)
    for item in self.children:
        item.disabled = True
    await interaction.message.edit(view=self)

    # 📩 DM στον applicant
    try:
        dm_embed = discord.Embed(
            title="🚓 LSPD Recruitment",
            description=(
                "# <a:siren:1498369700025995294> 〢 Η Αίτηση Απορρίφθηκε\n\n"
                "❌ Η αίτησή σας απορρίφθηκε.\n"
                "📅 Μπορείτε να ξανακάνετε αίτηση σε 15 ημέρες."
            ),
            color=discord.Color.red(),
            timestamp=discord.utils.utcnow()
        )

        dm_embed.set_thumbnail(url=applicant.display_avatar.url)

        dm = await applicant.create_dm()
        await dm.send(embed=dm_embed)

    except discord.Forbidden:
        await interaction.followup.send(
        embed=discord.Embed(
            title="❌ Error",
            description=f"Could not send a DM to {applicant.mention}.",
            color=discord.Color.red()
        ),
        ephemeral=True
    )

        await interaction.message.edit(view=None)

    async def get_applicant(self, interaction: discord.Interaction):
        """Fetches the applicant from cache or API."""
        return interaction.guild.get_member(interaction.user.id) or await interaction.guild.fetch_member(interaction.user.id)

class ApplicationSelectView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Αίτηση για LSPD", style=discord.ButtonStyle.success, custom_id="lspd_application_button")
    async def lspd_application(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = LSPDApplicationModal(user=interaction.user)
        await interaction.response.send_modal(modal)

@bot.command()
@commands.has_permissions(administrator=True)
async def post_applications(ctx):
    view = ApplicationSelectView()

    embed = discord.Embed(
        title="",
        description="# <:papers:1498454953172144268> Αιτήσεις \n Για να ενταχθείτε στο LSPD: \n> LSPD \n κάντε κλικ <a:click:1498455335919292587> πάνω στο κουμπί \n\n  Βασικές προϋποθέσεις: \n> Να είστε άνω των 16 ετών \n> Να έχετε διαβάσει προσεκτικά τους κανονισμούς της πόλης \n> Να αντιμετωπίσετε με σοβαρότητα την αίτηση που θα επιλέξετε \n\n Καλή σας τύχη",
        color=discord.Color.dark_red()
    )
    embed.set_footer(text="Reloaded Roleplay")

    await ctx.send(embed=embed, view=view)


bot.run("MTQ5Njk2ODMwOTEyNjU5NDc0MA.GqDHRl.oESVGUmCxhiIWGPAbnNWu1t0rVSRg1iLa_UcBw")