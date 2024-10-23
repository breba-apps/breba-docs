class Reporter:
    def __init__(self, document_report):
        self.document_report = document_report

    def print_report(self):
        # Print document report details
        print(f"Document Report: {self.document_report.file}\n")

        # Iterate over each goal in the document
        for goal_report in self.document_report.goal_reports:
            print(f"Goal: {goal_report.goal_name}")
            print(f"Description: {goal_report.goal_description}\n")

            # Iterate over command reports within each goal
            for command_report in goal_report.command_reports:
                print(f"  Command: {command_report.command}")
                print(f"  Success: {'Yes' if command_report.success else 'No'}")
                print(f"  Insights: {command_report.insights}\n")

