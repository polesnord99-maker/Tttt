"""Point d'entrée du bot Discord d'entreprise."""
import asyncio
import logging
import discord
from discord.ext import commands
from config import TOKEN, LOG_LEVEL, DEV_GUILD_ID
from database import Database
from cogs.services import ServicePanel
from cogs.tickets import TicketStaffView

EXTENSIONS = ["cogs.configuration", "cogs.members", "cogs.tickets", "cogs.absences", "cogs.services"]

class EntrepriseBot(commands.Bot):
    def __init__(self):
        intents=discord.Intents.default()
        intents.members=True
        intents.message_content=True
        super().__init__(command_prefix="!", intents=intents)
        self.db=Database()

    async def setup_hook(self):
        await self.db.connect()
        for ext in EXTENSIONS:
            try: await self.load_extension(ext)
            except Exception: logging.exception("Échec de chargement de %s",ext)
        # Vues persistantes ré-enregistrées avec leurs identifiants stables.
        self.add_view(ServicePanel(self))
        cur=await self.db.db().execute("SELECT id FROM tickets WHERE status='open'")
        for row in await cur.fetchall():
            try: self.add_view(TicketStaffView(self,row["id"]))
            except Exception: logging.exception("Impossible de restaurer le ticket %s",row["id"])
        if DEV_GUILD_ID:
            guild=discord.Object(id=DEV_GUILD_ID)
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
            logging.info("Commandes synchronisées sur le serveur de développement %s",DEV_GUILD_ID)
        else:
            await self.tree.sync()
            logging.info("Commandes globales synchronisées")

    async def on_ready(self):
        logging.info("Connecté comme %s (%s)",self.user,self.user.id)

    async def close(self):
        await self.db.close()
        await super().close()

async def main():
    logging.basicConfig(level=getattr(logging,LOG_LEVEL,logging.INFO),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")
    if not TOKEN or TOKEN=="COLLER_LE_TOKEN_ICI":
        raise RuntimeError("Configurez DISCORD_TOKEN dans le fichier .env.")
    async with EntrepriseBot() as bot:
        await bot.start(TOKEN)

if __name__=="__main__":
    asyncio.run(main())
