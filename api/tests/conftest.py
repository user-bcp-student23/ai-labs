import os

# Debe definirse antes de importar app.main, que crea la app al cargarse.
os.environ["WORKSHOP_TOKEN_SECRET"] = "test-only-secret-not-for-production"
