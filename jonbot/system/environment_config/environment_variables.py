import os

from dotenv import load_dotenv

from jonbot.system.environment_config.discord_config.load_discord_config import BOT_NICK_NAME

load_dotenv()



#API Keys and tokens
OPENAI_API_KEY = os.getenv("OPEN_AI_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

#Local path stuff
LOG_FILE_FOLDER_NAME = "logs"
BASE_DATA_FOLDER_NAME = f"{os.getenv('BOT_NICK_NAME')}_data"
DATABASE_BACKUP = "database_backup"

#Database stuff
MONGO_URI = os.getenv('MONGO_URI')
DATABASE_NAME = f"{BOT_NICK_NAME}_database"
USERS_COLLECTION_NAME = f"users"
CONVERSATION_HISTORY_COLLECTION_NAME = "conversation_history"

#URL stuff
URL_PREFIX = os.getenv('PREFIX')
HOST_NAME = os.getenv('HOST_NAME', 'localhost')
API_HOST_NAME = 'localhost'
PORT_NUMBER = int(os.getenv('PORT_NUMBER'))
if os.path.exists('/.dockerenv'):
    API_HOST_NAME = 'api'
    HOST_NAME = '0.0.0.0'
    PORT_NUMBER = 8091



