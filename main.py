import os
from bot import Bot
from utils.functions import getCurrentTime

from dotenv import load_dotenv
from discord import errors as ds_errors, Intents

from colorama import Fore, Style
from colorama import just_fix_windows_console as fix_win_console

fix_win_console()
load_dotenv()


sys_message_divider = "---------------"

production_token = os.getenv("prod_token")
test_token       = os.getenv("test_token")
debug_guild_id   = os.getenv("debug_guild_id")

intents = Intents().default()
intents.members = True
intents.message_content = True

bot = Bot("/", intents, debug_guild_id)


try:
    token = 0

    if os.getlogin() == 'pi':

        print(Fore.BLUE+'The bot is using the production token!')
        token = production_token

    else:
        print(Fore.BLUE+'The bot is using the test token!')
        token = test_token

    print(f'Start time: {getCurrentTime()}\n')
    print(f'{sys_message_divider}'+Style.RESET_ALL)

    bot.run(token)


except NameError:

    print(Fore.RED+ '\nFatal: Token variable not found' +Style.RESET_ALL)

except ds_errors.LoginFailure or ds_errors.HTTPException:

    print(Fore.RED+ '\nFatal: Invalid token' +Style.RESET_ALL)