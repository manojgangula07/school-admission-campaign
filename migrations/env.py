from __future__ import with_statement
import sys
from alembic import context
from sqlalchemy import engine_from_config, pool
from app import create_app, db
from app.models import *

# This will add the application's model metadata to the migration context
app = create_app()
app.app_context().push()

# This is the main function that runs migrations
def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix='sqlalchemy.',
        poolclass=pool.NullPool)
    
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=db.metadata
        )

        with context.begin_transaction():
            context.run_migrations()

run_migrations_online()
