# 기본 사용법

Ouroboros 웹 UI에서 명세를 작성하고 활용하는 기본 흐름을 안내합니다.

## 전체 워크플로우

1. **웹 UI 접속**: 브라우저에서 `http://localhost:8080/ouroboros/`로 이동합니다.
2. **Schema 생성**: 왼쪽 사이드바의 "Schemas"를 선택하고 "New Schema" 버튼으로 재사용 가능한 데이터 모델을 등록합니다.
3. **API 명세 작성**: "APIs" 탭에서 경로·메서드·요약과 Schema를 연결해 엔드포인트를 만듭니다.
4. **Mock 테스트**: 명세 카드에서 "Try" 또는 "Copy cURL"을 활용해 Mock 응답을 확인합니다.
5. **상태 업데이트**: 구현이 완료되면 명세 우측 패널에서 진행 상태(Progress)를 "completed"로 변경합니다.

## 웹 UI 기능 요약

- **Schemas 탭**: JSON 형태로 스키마를 작성하고 필수 필드를 지정할 수 있습니다.
- **APIs 탭**: Path/Method 입력 후 Request Body, Response, Headers를 드래그&드롭 혹은 폼으로 설정합니다.
- **Import/Export**: 우측 상단 "Import YAML", "Export YAML" 버튼으로 OpenAPI 파일을 가져오거나 내보냅니다.
- **Try 패널**: API 상세 화면에서 파라미터를 입력한 뒤 "Send" 버튼으로 Mock 응답을 바로 확인합니다.

## 다음 단계

- [API 명세서 작성](/guide/api-spec) – UI에서 엔드포인트를 작성하는 방법
- [Schema 관리](/guide/schema) – 재사용 모델 등록
- [Mock API](/guide/mock-api) – Try 패널로 테스트하기

