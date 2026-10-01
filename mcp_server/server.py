import subprocess
import re
from pydantic import BaseModel, field_validator
from fastmcp import FastMCP

mcp = FastMCP("SecOps-AWS-CLI")

class AWSCommand(BaseModel):
    command: str

    @field_validator("command")
    @classmethod
    def validate_command(cls, v: str) -> str:
        v = v.strip()
        if v.startswith("aws "):
            v = v[4:].strip()
            
        if re.search(r'[;&|><]', v):
            raise ValueError("Command chaining or redirection is strictly prohibited.")
        
        if " rb " in v or "delete-bucket" in v or "rm " in v:
            raise ValueError("Destructive commands are blocked by SecOps guardrails.")
        
        valid_services = ["s3", "s3api", "ec2", "iam"]
        first_word = v.split()[0] if v else ""
        
        if first_word not in valid_services:
            raise ValueError(f"Command must start with a supported AWS service: {valid_services}. Got: '{first_word}'")
            
        return v

@mcp.tool()
def execute_aws_cli(command: str) -> str:
    """
    Executes an AWS CLI command against the LocalStack environment.
    Use this to investigate and remediate AWS resources.
    """
    try:
        # Explicitly pass the string through our Pydantic guardrail
        validated_input = AWSCommand(command=command)
    except Exception as e:
        # If Pydantic catches a violation, return the error safely to the LLM
        return f"Guardrail Error: {e}"
        
    full_command = f"aws --endpoint-url=http://localhost:4566 {validated_input.command}"
    
    try:
        result = subprocess.run(
            full_command, 
            shell=True, 
            check=True, 
            text=True, 
            capture_output=True
        )
        return result.stdout.strip() if result.stdout else "Command executed successfully with no output."
    except subprocess.CalledProcessError as e:
        return f"Command Failed!\nError: {e.stderr.strip()}"

if __name__ == "__main__":
    mcp.run(transport='stdio')