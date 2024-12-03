from breba_docs.agent.graph_agent import GraphAgent
from breba_docs.analyzer.reporter import Reporter
from breba_docs.services.document import Document
from breba_docs.services.reports import DocumentReport


def create_document_report(doc: Document):
    graph = GraphAgent(doc)  # agent(doc)
    goal_reports = graph.invoke()['goal_reports']
    #     TODO: give document name other than Some Document
    document_report: DocumentReport = DocumentReport("Some Document", goal_reports)
    Reporter(document_report).print_report()

    return document_report