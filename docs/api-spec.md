# API 명세서 작성

Ouroboros 웹 UI에서 REST API 명세를 작성하고 관리하는 방법을 안내합니다.

## 새 API 추가

1. 좌측 사이드바에서 "APIs"를 선택한 뒤 "New API" 버튼을 누릅니다.
2. Path, Method, Summary, Description을 입력합니다.
3. Parameters, Request Body, Responses 영역에서 필요한 항목을 추가하거나 Schema를 연결합니다.
4. 오른쪽 상단 "Save" 버튼을 눌러 명세를 저장하면 Mock 엔드포인트가 즉시 생성됩니다.

## 명세 수정 및 관리

- 세부 화면에서 Summary, Description, Schema 연결 등을 수정한 뒤 저장하면 즉시 반영됩니다.
- "Duplicate" 기능으로 유사한 엔드포인트를 빠르게 복제할 수 있습니다.
- Progress(진행 상태)를 "mock" → "completed"로 바꾸어 구현 완료 여부를 표시하세요.
- "Delete" 버튼으로 명세를 삭제하면 관련 Mock 엔드포인트도 함께 제거됩니다.

## Import / Export

상단 메뉴의 "Import YAML", "Export YAML" 버튼으로 OpenAPI 3.1 YAML 파일을 가져오거나 내보낼 수 있습니다. 기존 명세가 있는 상태에서 Import하면 UI가 자동으로 병합 결과를 안내합니다.

## 유용한 팁

- Schema를 먼저 등록한 뒤 API에서 참조하면 반복 입력을 줄일 수 있습니다.
- Mock 응답 예시는 상세 화면 하단 "Try" 탭에서 바로 확인할 수 있습니다.
- 가져온 YAML이 많을 경우 좌측 필터를 사용해 태그/상태별로 명세를 빠르게 찾을 수 있습니다.

