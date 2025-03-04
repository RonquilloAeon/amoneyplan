"""
Management command to initialize the database for the Money Plan app.
"""

from django.apps import apps
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Initialize the database for the Money Plan app"

    def handle(self, *args, **kwargs):
        """
        Create the necessary database tables for event sourcing.
        """
        self.stdout.write("Initializing database for Money Plan app...")

        # Create the tables for event sourcing
        try:
            # TODO remove?
            # Initialize the infrastructure
            # env = Environment("amoneyplan")
            # factory = Factory.construct(env)

            # with connection.schema_editor() as schema_editor:

            #     tables = factory.

            #     for table in tables:
            #         self.stdout.write(f"Created table: {table}")

            # self.stdout.write(self.style.SUCCESS("Database initialization completed successfully!"))

            # Optionally create a default Money Plan for testing
            create_sample = kwargs.get("sample", False)
            if create_sample:
                self._create_sample_plan()

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error initializing database: {e}"))

    def add_arguments(self, parser):
        parser.add_argument("--sample", action="store_true", help="Create a sample Money Plan for testing")

    def _create_sample_plan(self):
        """
        Create a sample Money Plan for testing.
        """
        self.stdout.write("Creating sample Money Plan...")

        try:
            service = apps.get_app_config("money_plans").money_planner

            # Create a new plan with initial balance
            plan_id = service.create_plan(initial_balance=1000.00, notes="Sample Money Plan for testing")

            # Add some accounts and buckets
            service.add_account(
                plan_id=plan_id,
                name="Checking Account",
                buckets=[
                    {"bucket_name": "Bills", "category": "Expenses", "allocated_amount": 500.00},
                    {"bucket_name": "Food", "category": "Expenses", "allocated_amount": 200.00},
                ],
            )

            service.add_account(
                plan_id=plan_id,
                name="Savings Account",
                buckets=[
                    {
                        "bucket_name": "Emergency Fund",
                        "category": "Savings",
                        "allocated_amount": 200.00,
                    },
                    {"bucket_name": "Vacation", "category": "Savings", "allocated_amount": 100.00},
                ],
            )

            # Commit the plan
            service.commit_plan(plan_id)

            self.stdout.write(self.style.SUCCESS(f"Created sample Money Plan with ID: {plan_id}"))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error creating sample plan: {e}"))
