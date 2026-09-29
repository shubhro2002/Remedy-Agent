import os
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("OPENROUTER_API_KEY")

if not api_key:
    raise ValueError("OPENROUTER_API_KEY environment variable is not set.")

llm = ChatOpenAI(
    model="openai/gpt-6-sol",
    api_key=api_key, # type: ignore
    base_url="https://openrouter.ai/api/v1",
    temperature=0.1,
    max_retries=3
)

if __name__ == "__main__":
    print(llm.invoke("What is the AWS CLI command to list S3 buckets?").content)