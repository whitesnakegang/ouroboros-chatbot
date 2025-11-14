# OpenAPI 확장

Ouroboros 커스텀 확장 필드와 자동 보정 규칙을 정리했습니다.

## Operation-level 확장

- `x-ouroboros-id`: 고유 식별자 (UUID)
- `x-ouroboros-progress`: 진행 상태 (`mock` / `completed`)
- `x-ouroboros-tag`: 개발 태그 (none, implementing, bugfix)
- `x-ouroboros-diff`: 명세-구현 차이 (none, request, response, endpoint, both)
- `x-ouroboros-isvalid`: 검증 상태 플래그 (웹 UI에서 사용)

초기 생성 시 모든 값은 자동으로 채워지며, 명세를 수정하면 `diff`가 `none`으로 재설정됩니다.

## Schema-level 확장

- `x-ouroboros-mock`: Mock 데이터 생성 표현식 (DataFaker 문법)
- `x-ouroboros-orders`: 필드 순서 정의 (JSON 응답 키 순서)

`SchemaValidator`가 누락된 항목을 자동으로 채우며, `minItems > maxItems`와 같은 오류를 보정합니다.

