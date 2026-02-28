"""Setup script for curam-cer-ontology-agent."""

from setuptools import find_packages, setup

setup(
    name="curam-cer-ontology-agent",
    version="1.0.0",
    description="Agentic AI for government eligibility determination using OWL ontology and MCP",
    author="Pankaj Kumar",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.11",
    install_requires=[
        "rdflib>=7.0.0",
        "pydantic>=2.0.0",
        "python-dotenv>=1.0.0",
        "mcp[cli]>=1.0.0",
        "langchain>=0.3.0",
        "langchain-openai>=0.2.0",
        "langchain-anthropic>=0.2.0",
        "uvicorn[standard]>=0.30.0",
        "starlette>=0.38.0",
    ],
    extras_require={
        "dev": [
            "pytest>=8.0.0",
            "pytest-cov>=4.0.0",
            "black>=24.0.0",
            "isort>=5.13.0",
            "mypy>=1.11.0",
        ],
    },
)
