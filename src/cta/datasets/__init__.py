"""Loaders that turn each command-history dataset into a common format."""

from cta.datasets.model import CommandEvent, History, program_name

__all__ = ["CommandEvent", "History", "program_name"]
