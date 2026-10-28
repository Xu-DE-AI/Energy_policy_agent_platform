"""CLI entry point for corpus validation and index refresh."""
from app.pipeline.flow import run_pipeline
if __name__ == "__main__": print(run_pipeline())
