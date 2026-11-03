"""One-off script: connect to Neo4j using .env config and run
schema.py + seed_data.py."""
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from graph.connection import get_driver, close_driver
from graph.schema import apply_schema
from graph.seed_data import seed_all

if __name__ == "__main__":
    driver = get_driver()
    try:
        driver.verify_connectivity()
        print("Connected to Neo4j. Applying schema...")
        apply_schema(driver)
        print("Seeding roles, skills, and progressions...")
        seed_all(driver)
        print("Seed complete.")
    finally:
        close_driver()
