"""
Unifier - A sophisticated Discord bot uniting servers and platforms
Copyright (C) 2024  Green, ItsAsheer

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as
published by the Free Software Foundation, either version 3 of the
License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import asyncio
import sys
import getpass
import json
import nextcord
import tomllib
import tomli_w
import traceback
from nextcord.ext import commands
from pathlib import Path
from typing_extensions import Self

try:
    sys.path.insert(0, '.')
    from utils import secrets
except:
    raise

with open('boot_config.json') as file:
    boot_config = json.load(file)

cgroup = Path('/proc/self/cgroup')
uses_docker = Path('/.dockerenv').is_file() or cgroup.is_file() and 'docker' in cgroup.read_text()

ptero_support = uses_docker and boot_config.get('ptero', False)

install_option = sys.argv[1] if len(sys.argv) > 1 else None

with open('boot/internal.json') as file:
    internal = json.load(file)

install_options = internal['options']

if not install_option:
    for option in install_options:
        if option['default']:
            install_option = option['id']
            break

class Intents(nextcord.Intents):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @classmethod
    def no_presence(cls) -> Self:
        """A factory method that creates a :class:`Intents` with everything enabled
        except :attr:`presences`, :attr:`members`, and :attr:`message_content`.
        """
        self = cls.all()
        self.presences = False
        return self


bot = commands.Bot(
    command_prefix='u!',
    intents=Intents.no_presence()
)

user_id = 0
server_id = 0

if sys.version_info.minor < internal['required_py_version']:
    print(f'\x1b[31;49mCannot install {internal["product_name"]}. Python 3.{internal["required_py_version"]} or later is required.\x1b[0m')
    sys.exit(1)

@bot.event
async def on_ready():
    global server_id

    print(f'\x1b[33;1mIs {bot.user.name} ({bot.user.id}) the correct bot? (y/n)\x1b[0m')
    answer = 'y'

    print(f'\x1b[36;1mAttempting to DM user {user_id}...\x1b[0m')

    user = bot.get_user(user_id)

    for guild in bot.guilds:
        for member in guild.members:
            if member.id == user_id:
                server_id = guild.id
                break

        if not server_id == 0:
            break

    print(f'\x1b[33;1mDid you receive a DM from the bot? (y/n)\x1b[0m')
    answer = 'y'

    print('\x1b[36;1mOwner verified successfully, closing bot.\x1b[0m')
    await bot.close()

print('\x1b[33;1mWe need the ID of the user who will be the instance owner. In most cases this is your user ID.\x1b[0m')
print(f'\x1b[33;1mThe owner will have access to special commands for maintaining your {internal["product_name"]} instance.\x1b[0m')
print('\x1b[33;1mTo copy your ID, go to your Discord settings, then Advanced, then enable Developer mode.\x1b[0m')

while True:
    try:
        user_id = os.environ.get('user-id')
        break
    except KeyboardInterrupt:
        print('\x1b[31;49mAborted.\x1b[0m')
        sys.exit(1)
    except:
        print('\x1b[31;49mThis isn\'t an integer, try again.\x1b[0m')

print('\x1b[33;1mWe will now ask for your bot token.\x1b[0m')
print('\x1b[33;1mThe user verifier will use this token to log on to Discord.\x1b[0m\n')
print(f'\x1b[37;41;1mWARNING: DO NOT SHARE THIS TOKEN, NOT EVEN WITH {internal["maintainer"].upper()}.\x1b[0m')
print(f'\x1b[31;49m{internal["maintainer"]} will NEVER ask for your token. Please keep this token to yourself and only share it with trusted instance maintainers.\x1b[0m')
print('\x1b[31;49mFor security reasons, the installer will hide the input.\x1b[0m')

if ptero_support:
    print(f'\x1b[36;1mPlease enter your bot token using the console input.\x1b[0m')

token = os.environ.get('token')

encryption_password = ''

print('\x1b[33;1mWe will now ask for the token encryption password.\x1b[0m')
print('\x1b[33;1mYour encryption password is separate from your Discord account password or bot token. It is used to encrypt data stored by Unifier.\x1b[0m')
print(f'\x1b[37;41;1mWARNING: DO NOT SHARE THIS PASSWORD, NOT EVEN WITH {internal["maintainer"].upper()}.\x1b[0m')
print(f'\x1b[31;49m{internal["maintainer"]} will NEVER ask for your encryption password. Please keep this password to yourself and only share it with trusted instance maintainers.\x1b[0m')
print('\x1b[31;49mFor security reasons, the installer will hide the input.\x1b[0m')

if ptero_support:
    print(f'\x1b[36;1mPlease enter your encryption password using the console input.\x1b[0m')

encryption_password = os.environ.get('encryption-key')

print('\x1b[36;1mStarting bot...\x1b[0m')

try:
    bot.run(token)
except:
    traceback.print_exc()
    print('\x1b[31;49mLogin failed. Perhaps your token is invalid?\x1b[0m')
    print('\x1b[31;49mMake sure Server Members and Message Content intents are enabled for the bot.\x1b[0m')
    sys.exit(1)

tokenstore = secrets.TokenStore(True, password=encryption_password)

try:
    tokenstore.add_token('TOKEN', token)
except KeyError:
    # Token already exists, so replace it
    tokenstore.replace_token('TOKEN', token, encryption_password)

tokenstore.save('.encryptedenv')
print('\x1b[36;1mYour tokens have been stored securely.\x1b[0m')

with open('config.toml', 'rb') as file:
    config = tomllib.load(file)

config['roles']['owner'] = user_id

if not internal['skip_server']:
    config['moderation']['home_guild'] = server_id

with open('config.toml', 'wb') as file:
    tomli_w.dump(config, file)

with open('.install.json','w+') as file:
    # noinspection PyTypeChecker
    json.dump({'product': internal["product"],'setup': False,'option': install_option}, file)

print(f'\x1b[36;1m{internal["product_name"]} installed successfully.\x1b[0m')
