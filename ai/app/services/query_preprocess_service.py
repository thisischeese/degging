from dataclasses import dataclass, field
from uuid import UUID

from app.models.query_preprocess import QueryPreprocessData


@dataclass(slots=True)
class PreprocessedQuery:
    normalized_query: str
    vector: list[float] = field(default_factory=list)
    menu_phrases: list[str] = field(default_factory=list)


class QueryPreprocessService:
    async def encode_query(self, query: str) -> list[float]:
        """
        Encode the incoming query text into a vector.
        The encoder integration is intentionally stubbed until the model is ready.
        """
        # encoder_client = get_query_encoder()
        # return await encoder_client.encode(query)
        return []

    async def extract_menu_phrases(self, query: str) -> list[str]:
        """
        Extract menu phrases from the incoming query.
        The NER integration is intentionally stubbed until the model is ready.
        """
        # ner_model = get_menu_ner_model()
        # return await ner_model.extract(query)
        return []

    async def preprocess(self, query: str) -> PreprocessedQuery:
        normalized_query = query.strip()
        vector = await self.encode_query(normalized_query)
        menu_phrases = await self.extract_menu_phrases(normalized_query)
        return PreprocessedQuery(
            normalized_query=normalized_query,
            vector=vector,
            menu_phrases=menu_phrases,
        )

    async def preprocess_query(self, query: str, user_id: UUID) -> QueryPreprocessData:
        """
        Return the public preprocess response payload.
        The current endpoint keeps returning empty extracted menus until menu resolution
        can be grounded with search candidates.
        """
        _ = user_id
        processed_query = await self.preprocess(query)

        return QueryPreprocessData(
            original_query=processed_query.normalized_query,
            vector=processed_query.vector,
            dimensions=len(processed_query.vector),
            extracted_menus={},
        )
