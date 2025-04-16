from django.core.management.base import BaseCommand

from amoneyplan.api.schema import schema


class Command(BaseCommand):
    help = "Exports the GraphQL schema to a file."

    def add_arguments(self, parser):
        parser.add_argument("--output", type=str, default="schema.graphql", help="The output file path.")

    def handle(self, *args, **options):
        output_path = options["output"]

        # Generate the schema string
        schema_str = schema.as_str()

        # Write the schema to the specified file
        with open(output_path, "w") as file:
            file.write(schema_str)

        self.stdout.write(self.style.SUCCESS(f"Schema successfully exported to {output_path}"))
