# Custom CLI Tool with Click

## Project Overview
**Difficulty:** Intermediate  
**Estimated Time:** 3-4 hours  
**Skills Practiced:** Python, Click Framework, CLI Design, User Experience

### What You'll Build
A production-grade CLI tool that:
- Uses Click framework for professional command structure
- Implements subcommands and command groups
- Handles options, arguments, and flags
- Provides helpful documentation and examples
- Includes auto-completion support
- Offers colorized output and progress bars
- Validates inputs and handles errors gracefully

### Why This Matters
CLIs are the primary interface for DevOps tools (docker, kubectl, terraform). This project teaches you to build professional command-line interfaces that are intuitive and maintainable.

### Prerequisites
- Python 3.8+ installed
- Basic understanding of command-line interfaces
- Familiarity with subcommands (like git, docker)

---

## Step-by-Step Implementation

### Step 1: Project Setup
```bash
mkdir devops-cli
cd devops-cli
python3 -m venv venv
source venv/bin/activate
pip install click rich tabulate pyyaml requests
```

**Package purposes:**
- `click` - CLI framework
- `rich` - Beautiful terminal output
- `tabulate` - Format tables
- `pyyaml` - Config file parsing
- `requests` - HTTP requests

### Step 2: Design CLI Structure

**Target command structure:**
```
devops-cli
├── server
│   ├── list
│   ├── status <name>
│   └── restart <name>
├── deploy
│   ├── app <name>
│   └── rollback <name>
├── config
│   ├── show
│   └── set <key> <value>
└── --version
```

### Step 3: Create Main CLI Entry Point

Create `cli.py`:
```python
import click
from rich.console import Console
from rich.table import Table

console = Console()

@click.group()
@click.version_option(version='1.0.0')
@click.pass_context
def cli(ctx):
    """
    DevOps CLI - Manage servers and deployments

    A comprehensive tool for DevOps operations.
    """
    # Ensure context object exists
    ctx.ensure_object(dict)

@cli.command()
def info():
    """Show CLI information"""
    console.print("[bold green]DevOps CLI v1.0.0[/bold green]")
    console.print("A powerful tool for DevOps operations")

if __name__ == '__main__':
    cli()
```

### Step 4: Implement Server Management Commands

```python
@cli.group()
def server():
    """Manage servers"""
    pass

@server.command('list')
@click.option('--status', type=click.Choice(['running', 'stopped', 'all']), 
              default='all', help='Filter by status')
@click.option('--format', type=click.Choice(['table', 'json', 'yaml']), 
              default='table', help='Output format')
def list_servers(status, format):
    """List all servers"""
    # Mock data - replace with actual server data
    servers = [
        {'name': 'web-01', 'status': 'running', 'ip': '10.0.1.10', 'cpu': '45%'},
        {'name': 'web-02', 'status': 'running', 'ip': '10.0.1.11', 'cpu': '38%'},
        {'name': 'db-01', 'status': 'stopped', 'ip': '10.0.2.10', 'cpu': '0%'},
    ]

    # Filter by status
    if status != 'all':
        servers = [s for s in servers if s['status'] == status]

    # Format output
    if format == 'table':
        table = Table(title="Servers")
        table.add_column("Name", style="cyan")
        table.add_column("Status", style="magenta")
        table.add_column("IP Address", style="green")
        table.add_column("CPU Usage")

        for server in servers:
            table.add_row(
                server['name'],
                server['status'],
                server['ip'],
                server['cpu']
            )
        console.print(table)

    elif format == 'json':
        import json
        console.print(json.dumps(servers, indent=2))

    elif format == 'yaml':
        import yaml
        console.print(yaml.dump(servers))

@server.command()
@click.argument('name')
@click.option('--detailed', is_flag=True, help='Show detailed information')
def status(name, detailed):
    """Check server status"""
    console.print(f"[bold]Checking status of server: {name}[/bold]")

    # Simulate API call
    server_info = {
        'name': name,
        'status': 'running',
        'uptime': '15 days',
        'load': '1.23, 1.45, 1.67'
    }

    if detailed:
        server_info.update({
            'memory': '8GB / 16GB (50%)',
            'disk': '120GB / 500GB (24%)',
            'network': '125 Mbps'
        })

    for key, value in server_info.items():
        console.print(f"  {key.capitalize()}: [green]{value}[/green]")

@server.command()
@click.argument('name')
@click.confirmation_option(prompt='Are you sure you want to restart?')
def restart(name):
    """Restart a server"""
    with console.status(f"[bold green]Restarting {name}..."):
        import time
        time.sleep(2)  # Simulate restart

    console.print(f"✓ [green]Server {name} restarted successfully[/green]")
```

### Step 5: Implement Deployment Commands

```python
@cli.group()
def deploy():
    """Manage deployments"""
    pass

@deploy.command('app')
@click.argument('app_name')
@click.option('--version', default='latest', help='App version to deploy')
@click.option('--environment', type=click.Choice(['dev', 'staging', 'prod']), 
              required=True, help='Target environment')
@click.option('--replicas', default=3, type=int, help='Number of replicas')
def deploy_app(app_name, version, environment, replicas):
    """Deploy an application"""
    console.print(f"[bold]Deploying {app_name} v{version} to {environment}[/bold]")

    steps = [
        "Pulling Docker image",
        "Updating configuration",
        "Rolling out deployment",
        "Verifying health checks",
        "Deployment complete"
    ]

    from rich.progress import Progress

    with Progress() as progress:
        task = progress.add_task("[cyan]Deploying...", total=len(steps))

        for step in steps:
            console.print(f"  → {step}")
            time.sleep(1)
            progress.update(task, advance=1)

    console.print(f"✓ [green]{app_name} v{version} deployed successfully[/green]")
    console.print(f"  Replicas: {replicas}")
    console.print(f"  Environment: {environment}")

@deploy.command('rollback')
@click.argument('app_name')
@click.option('--revision', type=int, help='Revision number to rollback to')
@click.confirmation_option(prompt='Are you sure you want to rollback?')
def rollback(app_name, revision):
    """Rollback an application deployment"""
    rev = revision if revision else 'previous'
    console.print(f"[yellow]Rolling back {app_name} to revision {rev}[/yellow]")

    with console.status("[bold yellow]Performing rollback..."):
        time.sleep(2)

    console.print(f"✓ [green]Rollback completed[/green]")
```

### Step 6: Implement Configuration Management

```python
import os
import yaml

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

@cli.group()
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
    console.print(f"✓ Set {key} = [green]{value}[/green]")

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
```

### Step 7: Add Input Validation

```python
def validate_ip(ctx, param, value):
    """Validate IP address"""
    import re
    if value:
        pattern = r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$'
        if not re.match(pattern, value):
            raise click.BadParameter('Invalid IP address format')
    return value

@server.command('add')
@click.argument('name')
@click.option('--ip', callback=validate_ip, required=True, help='Server IP address')
@click.option('--type', type=click.Choice(['web', 'db', 'cache']), required=True)
def add_server(name, ip, type):
    """Add a new server to inventory"""
    console.print(f"✓ Added server {name} ({ip}) as {type}")
```

### Step 8: Add Shell Completion

```python
# Add to setup.py for installation
from setuptools import setup

setup(
    name='devops-cli',
    version='1.0.0',
    py_modules=['cli'],
    install_requires=[
        'click',
        'rich',
        'tabulate',
        'pyyaml',
        'requests'
    ],
    entry_points={
        'console_scripts': [
            'devops-cli=cli:cli',
        ],
    },
)
```

Enable completion:
```bash
# Install in development mode
pip install -e .

# Enable bash completion
_DEVOPS_CLI_COMPLETE=bash_source devops-cli > ~/.devops-cli-complete.bash
echo 'source ~/.devops-cli-complete.bash' >> ~/.bashrc

# Or for zsh
_DEVOPS_CLI_COMPLETE=zsh_source devops-cli > ~/.devops-cli-complete.zsh
echo 'source ~/.devops-cli-complete.zsh' >> ~/.zshrc
```

### Step 9: Add Help Documentation

```python
# Enhanced help with examples
@cli.command()
def examples():
    """Show usage examples"""
    examples_text = """
    [bold]Common Usage Examples:[/bold]

    [cyan]List all running servers:[/cyan]
      devops-cli server list --status running

    [cyan]Deploy app to production:[/cyan]
      devops-cli deploy app myapp --environment prod --version 2.1.0

    [cyan]Check server status:[/cyan]
      devops-cli server status web-01 --detailed

    [cyan]Rollback deployment:[/cyan]
      devops-cli deploy rollback myapp --revision 5

    [cyan]Set configuration:[/cyan]
      devops-cli config set api_endpoint https://api.example.com
    """
    console.print(examples_text)
```

### Step 10: Test Your CLI

```bash
# List commands
devops-cli --help

# Test server commands
devops-cli server list
devops-cli server list --status running --format json
devops-cli server status web-01
devops-cli server status web-01 --detailed

# Test deploy commands
devops-cli deploy app myapp --environment dev --version 1.0.0
devops-cli deploy rollback myapp

# Test config
devops-cli config set api_key abc123
devops-cli config show
devops-cli config get api_key

# Show examples
devops-cli examples
```

---

## Success Criteria
- [ ] CLI has clear command structure with subcommands
- [ ] All commands have helpful documentation
- [ ] Input validation prevents invalid data
- [ ] Colorized output improves readability
- [ ] Progress indicators for long operations
- [ ] Configuration persists between sessions
- [ ] Shell completion works

## Extension Ideas
1. **Interactive Mode:** Add prompt-based interface
2. **API Integration:** Connect to real backend services
3. **Plugin System:** Allow custom command extensions
4. **Output Formatting:** Add CSV, XML formats
5. **Logging:** Add debug logging to file
6. **Remote Execution:** Run commands on remote servers
7. **Templating:** Generate config files from templates

---

**Completion Time:** 3-4 hours  
**Difficulty:** Intermediate  
**Next Project:** GitHub Repository Auditor
