import asyncio
import logging
from typing import List

import discord
from discord import Forbidden
from discord.ext import commands

from jonbot.backend.data_layer.models.discord_stuff.discord_chat_document import DiscordChatDocument
from jonbot.frontends.discord_bot.operations.discord_database_operations import (
    DiscordDatabaseOperations,
)
from jonbot.system.setup_logging.get_logger import get_jonbot_logger

logger = get_jonbot_logger()

logging.getLogger("discord").setLevel(logging.INFO)


class ServerScraperCog(commands.Cog):
    """A cog for scraping server data and storing it in a MongoDB database."""

    def __init__(self, database_operations: DiscordDatabaseOperations):
        self._database_operations = database_operations

    @commands.slash_command(
        name="scrape_server",
        description="Scrape all messages from all channels and threads in the server.",
    )
    @commands.has_permissions(administrator=True)
    async def scrape_server(self, ctx: discord.ApplicationContext):
        logger.info(f"Received scrape_server command in server: {ctx.guild.name}")

        channels = await ctx.guild.fetch_channels()
        await self._scrape(channels=list(channels), ctx=ctx)

    @commands.slash_command(
        name="scrape_local",
        description="Scrape all messages from invoking thread/channel only.",
    )
    @commands.has_permissions(administrator=True)
    async def scrape_messages_from_channel(
            self,
            ctx: discord.ApplicationContext,
    ):
        logger.info(f"Received scrape_local command from channel:  {ctx.channel.name}")

        channels = [ctx.channel]
        await self._scrape(channels=channels, ctx=ctx)

    async def _scrape(self, channels: List[discord.abc.Messageable], ctx: discord.ApplicationContext):
        upsert_tasks = []
        reply_embed_title = f"Scraping server: {ctx.guild.name}"
        reply_embed_description = ""
        reply_embed = discord.Embed(
            title=f"Scraping server: {ctx.guild.name}",
            description=reply_embed_description
        )
        reply_message = await ctx.send(
            embed=reply_embed
        )

        total_server_messages = 0
        all_messages = []
        try:
            filtered_channels = filter(lambda ch: isinstance(ch, discord.TextChannel), channels)
            for channel in filtered_channels:
                logger.info(f"Scraping channel:  {ctx.channel.name}")

                channel_message_count_string = ""
                total_channel_messages = 0
                channel_thread_message_count = 0

                channel_messages = await self._get_message_list_from_channel(
                    channel=channel
                )
                all_messages.extend(channel_messages)
                total_channel_messages += len(channel_messages)

                chat_documents = []
                for message in channel_messages:
                    if message.thread is not None:
                        thread_messages = await self._get_message_list_from_channel(channel=message.thread)
                        all_messages.extend(thread_messages)
                        channel_thread_message_count += len(thread_messages)
                        chat_documents.append(await DiscordChatDocument.build(chat_id=message.thread.id,
                                                                              parent_message=message,
                                                                              messages=thread_messages))
                total_channel_messages += channel_thread_message_count
                total_server_messages += total_channel_messages

                channel_message_count_string += (f"Channel: {channel}\n"
                                                 f"{len(channel_messages)} top level messages\n"
                                                 f"{len(chat_documents)} chats with {channel_thread_message_count} messages\n"
                                                 f"Total: {len(channel_messages) + channel_thread_message_count}\n"
                                                 f"-----------------------------\n")
                reply_embed_description = await self._update_reply_message_embed(
                    channel_message_count_string=channel_message_count_string,
                    total_server_messages_count=total_server_messages,
                    embed_title=reply_embed_title,
                    embed_message=reply_embed_description,
                    reply_message=reply_message,
                    done=False)
                logger.info(
                    f"Upserting {len(channel_messages)} channel messages and {len(chat_documents)} chat documents to database...")

                if len(channel_messages) > 0:
                    upsert_tasks.append(
                        asyncio.create_task(self._send_messages_to_database(messages_to_upsert=channel_messages)))

                if len(chat_documents) > 0:
                    upsert_tasks.append(
                        asyncio.create_task(self._send_chats_to_database(chat_documents=chat_documents)))

        except Exception as e:
            await ctx.send(
                embed=discord.Embed(
                    title=f"Error occurred while scraping channel: {ctx.channel.name}",
                    description=f"{e}"
                )
            )
            logger.error(f"Error occurred while scraping channel: {ctx.channel.name}: \n > {e}")
            logger.exception(e)
            raise e
        finally:
            logger.info(f"Awaiting {len(upsert_tasks)} tasks to upsert messages to database...")
            await asyncio.gather(*upsert_tasks)

            reply_embed_description = await self._update_reply_message_embed(
                channel_message_count_string="",
                total_server_messages_count=total_server_messages,
                embed_title=reply_embed_title,
                embed_message=reply_embed_description,
                reply_message=reply_message,
                done=True)
            if not len(all_messages) == total_server_messages:
                raise ValueError("Total messages scraped does not match total messages upserted!")

        logger.success(f"Finished scraping server: {ctx.guild.name}!\n "
                       f"{reply_embed_description}"
                       )

    async def _update_reply_message_embed(self,
                                          embed_title: str,
                                          embed_message: str,
                                          reply_message: discord.Message,
                                          channel_message_count_string: str,
                                          total_server_messages_count: int,
                                          done: bool) -> str:
        total_server_messages_string = "======================\nTotal Server Messages:"
        scraping_next_channel_string = "\n\nScraping next channel..."
        new_embed_description = embed_message.split(total_server_messages_string)[0]
        new_embed_description += channel_message_count_string

        new_embed_description += f"{total_server_messages_string} {total_server_messages_count}"
        if done:
            new_embed_description += "\n\nDone!"
        else:
            new_embed_description += scraping_next_channel_string

        await reply_message.edit(embed=discord.Embed(
            title=embed_title,
            description=new_embed_description
        ))
        return new_embed_description

    async def _send_messages_to_database(
            self, messages_to_upsert: List[discord.Message]
    ) -> bool:
        logger.info(f"Sending {len(messages_to_upsert)} messages to database...")
        return await self._database_operations.upsert_messages(
            messages=messages_to_upsert
        )

    async def _send_chats_to_database(
            self, chat_documents: List[DiscordChatDocument]
    ) -> bool:
        logger.info(f"Sending {len(chat_documents)} messages to database...")
        return await self._database_operations.upsert_chats(
            chat_documents=chat_documents
        )

    async def _get_message_list_from_channel(
            self, channel: discord.abc.Messageable
    ) -> List[discord.Message]:
        channel_messages = []
        try:
            logger.info(f"Scraping channel: {channel}")
            async for message in channel.history(limit=None, oldest_first=True):
                channel_messages.append(message)
            logger.info(f"Scraped {len(channel_messages)} messages from channel: {channel}")

        except Forbidden:
            logger.warning(f"Missing permissions to scrape channel: {channel}")

        return channel_messages
