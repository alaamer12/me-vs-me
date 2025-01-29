from rich.console import Console
from rich.panel import Panel
from rich import print as rprint
from rich.progress import track
import os
import subprocess
from typing import Optional, final

# Initialize rich console
console = Console()

GITIGNORE = """
# Operating System Files
.DS_Store
Thumbs.db
desktop.ini

# IDE/Editor Files
.idea/
.vscode/
*.suo
*.ntvs*
*.njsproj
*.sln
*.swp
*~

# Build Output
node_modules/
dist/
build/
*.o
*.obj
*.class

# Dependency Directories
vendor/
jspm_packages/
typings/
*.jar
*.war

# Logs and Temporary Files
*.log
*.tmp
*.temp

# System Files
*.dll
*.exe
*.pdb
*.lib
*.so
*.dylib

# Configuration Files
.env
.DS_Store
.project
.classpath
.settings/

# IDE/Editor Specific
.idea/
.vscode/
*.sublime-project
*.sublime-workspace
*.idea/

# Miscellaneous
.dockerignore
.npmignore
.babelrc
.eslintrc
.gitattributes

# Custom Logs or Data Files
# Add any other file or directory specific to your project
"""

def run_command(command: list[str], cwd: str = None) -> tuple[str, str]:
    """Run a command and return its output."""
    try:
        result = subprocess.run(command, check=True, cwd=cwd, capture_output=True, text=True)
        return result.stdout, result.stderr
    except subprocess.CalledProcessError as e:
        console.print(f"[red]Error running command:[/red] {' '.join(command)}")
        console.print(f"[red]Error message:[/red] {e.stderr}")
        raise

def get_username() -> str:
    """Get GitHub username from auth status."""
    try:
        stdout, _ = run_command(["gh", "auth", "status"], cwd=current_directory)
        first_index = stdout.find("account") + len("account") + 1
        last_index = stdout.find("(") - 1
        username = stdout[first_index:last_index].strip()
        console.print(f"[green]✓[/green] Logged in as: [bold blue]{username}[/bold blue]")
        return username
    except subprocess.CalledProcessError:
        console.print("[red]❌ Not logged in to GitHub. Please run 'gh auth login' first.[/red]")
        raise

def verify_directory_name(directory_name: str) -> str:
    """Verify and fix directory name if needed."""
    if " " in directory_name:
        console.print("[yellow]⚠ Warning: Directory name contains spaces[/yellow]")
        with console.status("[bold yellow]Fixing directory name..."):
            fixed_name = directory_name.replace(" ", "-")
        console.print(Panel(
            f"[green]Directory name fixed:[/green]\n[red]{directory_name}[/red] → [green]{fixed_name}[/green]",
            title="Directory Name Update"
        ))
        return fixed_name
    return directory_name

def handle_existing_remote() -> bool:
    """Handle existing remote origin with user choices."""
    try:
        stdout, _ = run_command(["git", "remote", "get-url", "origin"], current_directory)
        current_remote = stdout.strip()
        
        console.print(Panel(
            f"[yellow]Remote origin already exists:[/yellow]\n[blue]{current_remote}[/blue]",
            title="⚠ Existing Remote"
        ))
        
        console.print("\nChoose how to handle the existing remote:")
        console.print("[1] [green]Safe remove[/green] (remove remote only, keep repo)")
        console.print("[2] [red]Hard remove[/red] (remove remote and delete repo)")
        console.print("[3] [blue]Skip[/blue] (keep current remote)")
        
        choice = input("\nEnter your choice (1-3): ").strip()
        
        if choice == "1":
            run_command(["git", "remote", "remove", "origin"], current_directory)
            console.print("[green]✓[/green] Remote origin safely removed")
            return True
        elif choice == "2":
            # Get the owner and repo name from the remote URL
            parts = current_remote.split("/")
            if len(parts) >= 2:
                repo_path = "/".join(parts[-2:]).replace(".git", "")
                try:
                    run_command(["gh", "repo", "delete", repo_path, "--yes"], current_directory)
                    console.print("[green]✓[/green] Remote repository deleted")
                except subprocess.CalledProcessError:
                    console.print("[yellow]⚠[/yellow] Failed to delete remote repository, but continuing...")
            
            run_command(["git", "remote", "remove", "origin"], current_directory)
            console.print("[green]✓[/green] Remote origin removed")
            return True
        elif choice == "3":
            console.print("[blue]ℹ[/blue] Keeping current remote")
            return False
        else:
            console.print("[red]Invalid choice. Keeping current remote.[/red]")
            return False
            
    except subprocess.CalledProcessError:
        # No remote exists
        return True

def commit_and_push(message: Optional[str] = None) -> None:
    """Commit and push changes to GitHub."""
    if not message:
        message = "Update repository"
    
    try:
        with console.status("[bold green]Initializing repository...") as status:
            # Initialize repository if needed
            if not os.path.exists(".git"):
                run_command(["git", "init"], current_directory)
                console.print("[green]✓[/green] Git repository initialized")
            
            if not os.path.exists(".gitignore"):
                status.update("[bold green]Creating .gitignore...")
                with open(".gitignore", "w") as f:
                    f.write(GITIGNORE)
            
            status.update("[bold green]Adding files...")
            run_command(["git", "add", "."], current_directory)
            
            status.update("[bold green]Committing changes...")
            run_command(["git", "commit", "-m", message], current_directory)
            
            status.update("[bold green]Checking remote...")
            if handle_existing_remote():
                status.update("[bold green]Setting up remote...")
                run_command(["git", "remote", "add", "origin", repo_url], current_directory)
            
            status.update("[bold green]Pushing to GitHub...")
            run_command(["git", "push", "-u", "origin", "main"], current_directory)
        
        console.print("\n[bold green]✨ Successfully pushed to GitHub![/bold green]")
        console.print(f"[blue]Repository URL:[/blue] {repo_url}")
        
    except subprocess.CalledProcessError as e:
        console.print("[red]Failed to push to GitHub. Error details above.[/red]")
        raise

# Get the current directory name
current_directory = os.getcwd()
directory_name = os.path.basename(current_directory)

if __name__ == "__main__":
    console.print(Panel.fit(
        "[bold blue]GitHub Repository Setup[/bold blue]",
        subtitle="[italic]Automated with ♥[/italic]"
    ))
    
    try:
        directory_name = verify_directory_name(directory_name)
        username = get_username()
        repo_url = f"https://github.com/{username}/{directory_name}.git"
        
        commit_msg = input("\nEnter commit message (press Enter for default): ").strip()
        commit_and_push(commit_msg if commit_msg else None)
        
    except Exception as e:
        console.print("\n[red]Process failed. Please fix the errors above and try again.[/red]")
        exit(1)
    finally:
        console.print("\n[bold green]✨ Process completed successfully![/bold green]")
        i = input("\nPress Enter to exit...")
