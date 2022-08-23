import logging
from typing import Optional

import discord

from tracking.logic import log_check_in
from tracking.models import CheckIn, Contestant, Contest

logger = logging.getLogger(__name__)


class WeighbotClient(discord.Client):
    def __init__(self, *, intents, **options):
        super(WeighbotClient, self).__init__(intents=intents, **options)

    async def get_check_in_for_thread(self, thread_id) -> Optional[CheckIn]:
        # TODO: add some caching here otherwise we'll query everytime
        try:
            check_in = await CheckIn.objects.aget(thread_id=str(thread_id))
            return check_in
        except CheckIn.DoesNotExist:
            return None

    async def handle_join(self, message: discord.Message):
        try:
            await Contestant.objects.aget(
                discord_id=str(message.author.id),
                contest__channel_id=message.channel.id
            )
            await message.add_reaction('❌')
            logger.info('User attempting to join contest again')
        except Contestant.DoesNotExist:
            logger.info('Joining user: %s %s', message.author.id, message.author.name)
            contest = await Contest.objects.aget(
                channel_id=message.channel.id
            )
            await Contestant.objects.acreate(
                name=message.author.name,
                discord_id=message.author.id,
                contest=contest
            )
            await message.add_reaction('✅')

    async def on_ready(self):
        logger.info('Bot is ready')

    async def on_message(self, message: discord.Message):
        logger.info(message)
        channel_id = message.channel.id
        message_id = message.id
        logger.info(
            '(channel: %s + message: %s) -> %s: %s', channel_id, message_id, message.channel.name, message.content
        )

        match message.content.split():
            case ['!wbjoin', *_]:
                await self.handle_join(message)
            case ['!wbcheckin', *_]:
                check_in = await self.get_check_in_for_thread(channel_id)
                if check_in is not None:
                    if not check_in.finished:
                        await log_check_in(message, check_in)
                    else:
                        await message.channel.send('The check-in is done you dummy')
            case ['!wbcard', *_]:
                pass
            case ['!wbhelp', *_]:
                pass
