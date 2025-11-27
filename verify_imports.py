import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "backend"))

try:
    print("Importing app.main...")
    from app.main import app
    print("Successfully imported app.main")

    print("Importing app.api.routes.commesse...")
    from app.api.routes import commesse
    print("Successfully imported app.api.routes.commesse")

    print("Importing app.api.routes.dashboard...")
    from app.api.routes import dashboard
    print("Successfully imported app.api.routes.dashboard")

    print("Importing app.api.routes.computi...")
    from app.api.routes import computi
    print("Successfully imported app.api.routes.computi")

    print("Importing app.services.analysis...")
    from app.services.analysis import AnalysisService, ComparisonService, TrendsService, WbsAnalysisService
    print("Successfully imported app.services.analysis services")

    print("All imports successful!")
except Exception as e:
    print(f"Error during import: {e}")
    sys.exit(1)
