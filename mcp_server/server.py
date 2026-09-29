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
        # 1. Block shell injection characters
        if re.search(r'[;&|><]', v):
            raise ValueError("Command chaining or redirection is strictly prohibited for security reasons.")
        
        # 2. Block destructive AWS commands
        if " rb " in v or "delete-bucket" in v or "rm " in v:
            raise ValueError("Destructive commands (like deleting buckets or objects) are blocked by SecOps guardrails.")
        
        # 3. Restrict to specific, approved AWS services
        valid_services = ["s3", "s3api", "ec2", "iam"]
        first_word = v.strip().split()[0] if v.strip() else ""
        
        if first_word not in valid_services:
            raise ValueError(f"Command must start with a supported AWS service: {valid_services}")
            
        return v

@mcp.tool()
def execute_aws_cli(command_input: AWSCommand) -> str:
    """
    Executes an AWS CLI command against the LocalStack environment.
    Use this to investigate and remediate AWS resources.
    """
    
    # FastMCP automatically validates command_input against the Pydantic model.
    # If it fails validation, FastMCP returns the error to the LLM automatically!
    full_command = f"aws --endpoint-url=http://localhost:4566 {command_input.command}"
    
    try:
        result = subprocess.run(
            full_command, 
            shell=True, 
            check=True, 
            text=True, 
            capture_output=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        return f"Command Failed!\nError: {e.stderr.strip()}"

if __name__ == "__main__":
    mcp.run(transport='stdio')