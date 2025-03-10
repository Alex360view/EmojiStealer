from discord import Client
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt, Confirm
from time import sleep
import sys
import asyncio

console = Console()
client = Client()
console.clear()

# Updated ASCII Art
console.print('[bold yellow]███████╗███╗   ███╗ ██████╗      ██╗██╗    ███████╗████████╗███████╗ █████╗ ██╗     ███████╗██████╗ [/bold yellow]')
console.print('[bold yellow]██╔════╝████╗ ████║██╔═══██╗     ██║██║    ██╔════╝╚══██╔══╝██╔════╝██╔══██╗██║     ██╔════╝██╔══██╗[/bold yellow]')
console.print('[bold yellow]█████╗  ██╔████╔██║██║   ██║     ██║██║    ███████╗   ██║   █████╗  ███████║██║     █████╗  ██████╔╝[/bold yellow]')
console.print('[bold yellow]██╔══╝  ██║╚██╔╝██║██║   ██║██   ██║██║    ╚════██║   ██║   ██╔══╝  ██╔══██║██║     ██╔══╝  ██╔══██╗[/bold yellow]')
console.print('[bold yellow]███████╗██║ ╚═╝ ██║╚██████╔╝╚█████╔╝██║    ███████║   ██║   ███████╗██║  ██║███████╗███████╗██║  ██║[/bold yellow]')
console.print('[bold yellow]╚══════╝╚═╝     ╚═╝ ╚═════╝  ╚════╝ ╚═╝    ╚══════╝   ╚═╝   ╚══════╝╚═╝  ╚═╝╚══════╝╚══════╝╚═╝  ╚═╝[/bold yellow]')
console.print()

# Function to exit the script gracefully
async def exit_code():
    console.log('Exiting the script...')
    await client.close()
    await asyncio.sleep(1)
    sys.exit()

# Function to select a guild by index or name
def select_guild(guilds, prompt_message):
    while True:
        user_input = Prompt.ask(prompt_message)
        try:
            # If the input is a number, treat it as an index
            index = int(user_input)
            if 0 <= index < len(guilds):
                return guilds[index]
            else:
                console.print(f'[red]Invalid index. Please enter a number between 0 and {len(guilds) - 1}.[/]')
        except ValueError:
            # If the input is not a number, search for the guild by name
            guild = next((g for g in guilds if g.name == user_input), None)
            if guild:
                return guild
            else:
                console.print(f'[red]Guild "{user_input}" not found. Please try again.[/]')

# Discord client event: on_ready
@client.event
async def on_ready():
    try:
        console.log(f'Successfully logged in as [green bold]{client.user}[/]')
        guilds = list(client.guilds)

        # Fetch and display guild list
        with console.status('[bold green]Fetching guild list...') as status:
            await asyncio.sleep(1.5)
            guild_list = Table(title="[magenta bold]Guild List")
            guild_list.add_column('Index', justify='right', style='bold green', no_wrap=True)
            guild_list.add_column('Guild Name', style='dim')
            guild_list.add_column('Guild ID', style='bold cyan', no_wrap=True)
            for i, guild in enumerate(guilds):
                guild_list.add_row(f'{i}', guild.name, f'{guild.id}')
            console.log('Fetched [bold green]guild list')
            console.print(guild_list)

        # Prompt for source guild (server to copy emojis from)
        source_guild = select_guild(guilds, '[[cyan]?[/]]Enter the [bold yellow]index[/] or [bold yellow]name[/] of the guild to copy emojis from')

        # Prompt for sink guild (server to paste emojis to)
        sink_guild = select_guild(guilds, '[[cyan]?[/]]Enter the [bold yellow]index[/] or [bold yellow]name[/] of the guild to paste emojis to')

        # Check permissions for managing emojis in the sink guild
        if not sink_guild.me.guild_permissions.manage_emojis:
            console.print(f'[[bold red]ERROR[/]][red]You do not have permissions to manage emojis in guild \'{sink_guild.name}\'')
            await exit_code()

        # Fetch and display emoji list for the source guild
        with console.status(f'[bold green]Fetching emoji list for guild {source_guild.name}...') as status:
            await asyncio.sleep(1)
            emoji_list = Table(title="[magenta bold]Emoji List")
            emoji_list.add_column('Emoji Name', style='dim')
            emoji_list.add_column('Emoji ID', style='cyan', no_wrap=True)
            emoji_list.add_column('Animated?')
            for emoji in source_guild.emojis:
                emoji_list.add_row(emoji.name, f'{emoji.id}', 'Yes' if emoji.animated else 'No')
            console.log(f'Fetched [bold green]emoji list[/] for [dim]{source_guild.name}')
            console.print(emoji_list)

        # Check free emoji slots in the sink guild
        free_slots = sink_guild.emoji_limit - len(sink_guild.emojis)
        if free_slots == 0:
            console.print(f'[[bold red]ERROR[/]][red]Guild {sink_guild.name} has no free emoji slots!')
            await exit_code()

        console.print(f'Guild [bold green]{sink_guild.name}[/] has [bold green]{free_slots}[/] free emoji slots.')

        # Prompt for emojis to copy
        values = Prompt.ask('[[cyan]?[/]]Enter [bold yellow]comma-separated[/] emoji names to copy [dim](TIP: Type "all" to copy all emojis)[/]', default='all')
        if values == 'all':
            emojis_to_copy = source_guild.emojis
        else:
            emojis_to_copy = [emoji for emoji in source_guild.emojis if emoji.name in values.split(',')]

        if len(emojis_to_copy) > free_slots:
            console.print(f'[[bold red]ERROR[/]][red]Guild {sink_guild.name} does not have enough free emoji slots!')
            await exit_code()

        # Display transaction summary
        transaction = Table(title="[magenta bold]Copy Transactions")
        transaction.add_column('From', style='bold yellow')
        transaction.add_column('To', style='bold yellow')
        transaction.add_column('Emojis Copied')
        transaction.add_row(source_guild.name, sink_guild.name, '\n'.join(emoji.name for emoji in emojis_to_copy))
        console.print(transaction)

        # Confirm transaction
        if not Confirm.ask("[[cyan]?[/]]Apply transactions?", default=True):
            await exit_code()

        # Copy emojis
        with console.status('[bold green]Copying emojis...') as status:
            for emoji in emojis_to_copy:
                await sink_guild.create_custom_emoji(name=emoji.name, image=await emoji.url.read(), reason='Created using EmojiSteal script.')
                console.print(f'Emoji created: [bold green]{emoji.name}')

        console.log(f'[bold green]Completed copying emojis!')
        console.print()
        console.print('[cyan]Thanks for using EmojiSteal script!')
        console.print('[cyan]Coded by @aintnoway1alex https://github.com/Alex360view')
        console.print('[i]thank you![/]')
        await exit_code()

    except Exception as e:
        console.print(f'[red]An error occurred: {e}[/]')
        await exit_code()

# Run the client
token = console.input('[[cyan]?[/]]Enter your [cyan bold]user token[/] : [green]')
client.run(token, bot=False)
