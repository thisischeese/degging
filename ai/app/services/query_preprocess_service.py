from uuid import UUID

from app.models.query_preprocess import QueryPreprocessData


class QueryPreprocessService:
    async def encode_query(self, query: str) -> list[float]:
        """
        향후 사용자 질의를 encoder 모델로 벡터화한다.
        현재는 encoder가 준비되지 않아 빈 벡터를 반환한다.
        """
        # encoder_client = get_query_encoder()
        # return await encoder_client.encode(query)
        return []

    async def extract_menus(self, query: str) -> list[str]:
        """
        향후 NER 모델을 호출해 사용자 질의에서 메뉴 엔티티를 추출한다.
        현재는 NER 모델이 준비되지 않아 빈 목록을 반환한다.
        """
        # ner_model = get_menu_ner_model()
        # return await ner_model.extract(query)
        return []

    async def preprocess_query(self, query: str, user_id: UUID) -> QueryPreprocessData:
        """
        사용자 질의를 정규화한 뒤, 벡터화/메뉴 추출 결과를 명세 형태로 반환한다.
        user_id는 현재 로직에서 사용하지 않지만 요청 계약 유지를 위해 받는다.
        """
        _ = user_id
        normalized_query = query.strip()
        vector = await self.encode_query(normalized_query)
        extracted_menus = await self.extract_menus(normalized_query)

        return QueryPreprocessData(
            original_query=normalized_query,
            vector=vector,
            dimensions=len(vector),
            extracted_menus=extracted_menus,
            menu_count=len(extracted_menus),
        )
