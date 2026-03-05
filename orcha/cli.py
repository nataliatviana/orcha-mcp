import typer 

app = typer.Typer(help="Orcha - Orchestrator CLI") 

@app.command() 
def run(): 
    """Run the orchestration.""" 
    typer.echo("Running Orcha...") 

def main(): 
    app() 

if __name__ == "__main__": 
    main()