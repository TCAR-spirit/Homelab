"""Zordon v0.1 -- scheduled world-building questions over Discord.

The loop:
  1. On a cron schedule, Zordon posts one lore question to your channel.
  2. Any normal message you send in that channel is logged as your answer.
  3. Zordon acknowledges in character. Future questions build on the log.

Commands (type in the Zordon channel):
  !ask    ask a question right now (great for testing)
  !recap  show the last chunk of the lore log
"""
import discord
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from discord.ext import commands

from . import config, llm, lore

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)
_scheduler_started = False


async def post_question() -> None:
    channel = bot.get_channel(config.CHANNEL_ID)
    if channel is None:
        print(f"Channel {config.CHANNEL_ID} not found -- check ZORDON_CHANNEL_ID")
        return
    question = await llm.generate_question(lore.recent())
    lore.log_question(question)
    await channel.send(question)


@bot.event
async def on_ready() -> None:
    global _scheduler_started
    if not _scheduler_started:
        scheduler = AsyncIOScheduler(timezone=config.TIMEZONE)
        scheduler.add_job(
            post_question,
            CronTrigger.from_crontab(config.QUESTION_CRON, timezone=config.TIMEZONE),
        )
        scheduler.start()
        _scheduler_started = True
    print(f"Zordon online as {bot.user} -- schedule: {config.QUESTION_CRON}")


@bot.event
async def on_message(message: discord.Message) -> None:
    if message.author.bot or message.channel.id != config.CHANNEL_ID:
        return
    if message.content.startswith("!"):
        await bot.process_commands(message)
        return
    # A plain message in the Zordon channel = an answer. Log it, acknowledge it.
    lore.log_answer(message.content)
    async with message.channel.typing():
        reply = await llm.acknowledge(lore.recent(), message.content)
    await message.channel.send(reply)


@bot.command(name="ask")
async def ask(ctx: commands.Context) -> None:
    """Fire a question immediately instead of waiting for the schedule."""
    async with ctx.typing():
        await post_question()


@bot.command(name="recap")
async def recap(ctx: commands.Context) -> None:
    """Show the recent lore log."""
    tail = lore.recent(max_chars=1800) or "The archives are empty, World Smith."
    await ctx.send(f"```markdown\n{tail}\n```")


def run() -> None:
    bot.run(config.DISCORD_TOKEN)


if __name__ == "__main__":
    run()
