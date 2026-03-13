import click
import os
import yaml
from helpers import console

CONFIG_FILE = os.path.expanduser('~/.devops-cli/config.yaml')


def load_config():
    """Load configuration from file"""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return yaml.safe_load(f) or {}
    return {}


def save_config(config):
    """Save configuration to file"""
    os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
    with open(CONFIG_FILE, 'w') as f:
        yaml.dump(config, f)


@click.group()
def config():
    """Manage CLI configuration"""
    pass


@config.command('show')
def show_config():
    """Show current configuration"""
    cfg = load_config()

    if not cfg:
        console.print("[yellow]No configuration set[/yellow]")
        return

    console.print("[bold]Current Configuration:[/bold]")
    for key, value in cfg.items():
        console.print(f"  {key}: [green]{value}[/green]")


@config.command('set')
@click.argument('key')
@click.argument('value')
def set_config(key, value):
    """Set a configuration value"""
    cfg = load_config()
    cfg[key] = value
    save_config(cfg)
    console.print(f"Set {key} = [green]{value}[/green]")


@config.command('get')
@click.argument('key')
def get_config(key):
    """Get a configuration value"""
    cfg = load_config()
    value = cfg.get(key)

    if value:
        console.print(f"{key}: [green]{value}[/green]")
    else:
        console.print(f"[yellow]Key '{key}' not found[/yellow]")
