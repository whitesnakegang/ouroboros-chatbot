# Schema 관리

웹 UI에서 재사용 가능한 데이터 모델(Schema)을 작성하고 활용하는 방법을 소개합니다.

## Schema 생성

1. 좌측 사이드바에서 "Schemas"를 선택합니다.
2. "New Schema" 버튼을 눌러 이름과 설명을 입력합니다.
3. Properties 영역에서 필드를 추가하고 타입, 필수 여부, Mock 값을 설정합니다.
4. 저장을 누르면 Schema가 등록되고, API 작성 시 바로 참조할 수 있습니다.

## Schema 관리

- 목록에서 Schema를 선택하면 오른쪽 패널에서 상세 정보를 수정할 수 있습니다.
- 필요 시 "Duplicate"로 비슷한 구조를 복제하거나 "Delete"로 삭제 가능합니다.
- Schema 이름은 API에서 `$ref` 선택 목록에 바로 표시됩니다.

## Mock 데이터

각 필드는 `x-ouroboros-mock`에 기본값을 지정할 수 있으며, Try 패널에서 Mock 응답을 확인할 때 사용됩니다. 예: `{{$internet.emailAddress}}`, `{{$random.uuid}}`

