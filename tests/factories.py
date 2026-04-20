"""Polyfactory factories for building Pydantic model fixtures in tests."""

from __future__ import annotations

from polyfactory.factories.pydantic_factory import ModelFactory

from magick_mind.models.v1.blueprint import Blueprint, ValidateBlueprintResponse
from magick_mind.models.v1.corpus import QueryCorpusResponse
from magick_mind.models.v1.persona import Persona, PersonaVersion, PreparePersonaResponse
from magick_mind.models.v1.runtime import EffectivePersonality


class BlueprintFactory(ModelFactory):
    __model__ = Blueprint
    __random_seed__ = 1


class ValidateBlueprintResponseFactory(ModelFactory):
    __model__ = ValidateBlueprintResponse
    __random_seed__ = 1


class PersonaFactory(ModelFactory):
    __model__ = Persona
    __random_seed__ = 1


class PersonaVersionFactory(ModelFactory):
    __model__ = PersonaVersion
    __random_seed__ = 1


class PreparePersonaResponseFactory(ModelFactory):
    __model__ = PreparePersonaResponse
    __random_seed__ = 1


class EffectivePersonalityFactory(ModelFactory):
    __model__ = EffectivePersonality
    __random_seed__ = 1


class QueryCorpusResponseFactory(ModelFactory):
    __model__ = QueryCorpusResponse
    __random_seed__ = 1
