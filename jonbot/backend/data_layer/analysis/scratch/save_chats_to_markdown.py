import asyncio
from pathlib import Path

from jonbot import logger
from jonbot.backend.data_layer.database.get_mongo_database_manager import get_mongo_database_manager
from jonbot.system.environment_variables import CHATS_COLLECTION_NAME
from jonbot.system.path_getters import get_base_data_folder_path


async def save_chats_to_markdown(database_name: str,
                                 channel_id: int,
                                 save_folder: str,
                                 ignored_users: list[int],
                                 collection_name: str = CHATS_COLLECTION_NAME):
    try:
        save_path = Path(save_folder)
        bot_nick_name = database_name.replace("_database", "")

        mongo_database = await get_mongo_database_manager()

        logger.info(f"Getting collection: {collection_name} in database: {database_name}")
        collection = mongo_database.get_collection(database_name=database_name,
                                                   collection_name=collection_name)
        query = {"channel_id": channel_id}
        logger.info(f"Querying collection: {collection_name} with query: {query}")
        chat_documents = await collection.find(query).to_list(length=None)
        logger.info(f"Found {len(chat_documents)} chat documents in channel: {channel_id}")
        #
        # json_file_name = f"chat_summary_{database_name}_{channel_id}.json"
        # json_file_path = save_path / json_file_name
        # json_file_path.write_text(json.dumps(chat_documents, indent=4))
        # logger.info(f"Saving chats as json file: {json_file_path}")

        markdown_file_name = f"chat_summary_{bot_nick_name}_channel-{channel_id}.md"
        markdown_file_path = save_path / markdown_file_name
        markdown_output = ""

        for chat_document in chat_documents:
            if chat_document['owner_id'] in ignored_users:
                logger.debug(
                    f"Ignoring chat from user: {chat_document['owner_name']} (id: {chat_document['owner_id']})")
                continue

            chat_title_string = f"## Chat Title: {chat_document['thread_name']} (id: {chat_document['thread_id']})\n"
            chat_title_string += f"Chat Owner: {chat_document['owner_name']} (id: {chat_document['owner_id']})\n\n"
            chat_title_string += "### Messages:\n"
            markdown_output += chat_title_string
            messages_string = ""
            for message in chat_document['messages']:
                messages_string += f"- **{message['author']} (id: {message['author_id']})**:"
                messages_string += f"\n\n{message['content']}\n\n"
            markdown_output += messages_string
            markdown_output += "_______\n\n"
        markdown_output += "\n\n"
        with open(markdown_file_path, "w", encoding="utf-8") as f:
            f.write(markdown_output)

        logger.success(f"Saved chats as markdown file: {markdown_file_path}")
    except Exception as e:
        logger.error(f"Error occurred while saving chats: {e}")
        logger.exception(e)
        raise e


if __name__ == "__main__":
    database_name = "classbot_database"
    channel_id = 1151164504483315722
    ignored_users_in = [362711467104927744]

    dropbox_folder_path = Path(
        r"D:\Dropbox\Northeastern\Courses\neural_control_of_real_world_human_movement\2023-09-Fall")
    if dropbox_folder_path.exists():
        save_folder_in = dropbox_folder_path / "chat_summaries"
        save_folder_in.mkdir(parents=True, exist_ok=True)
        save_folder_in = str(save_folder_in)
    else:
        save_folder_in = get_base_data_folder_path()

    asyncio.run(save_chats_to_markdown(database_name=database_name,
                                       channel_id=channel_id,
                                       save_folder=save_folder_in,
                                       ignored_users=ignored_users_in
                                       )
                )
    print("Done!")
