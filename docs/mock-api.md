# Mock API

웹 UI에서 Mock 응답을 확인하고 활용하는 방법을 안내합니다.

## Mock 테스트

1. API 상세 화면에서 "Try" 탭을 선택합니다.
2. 필요한 Path/Query/Header 값을 입력합니다.
3. Request Body가 있으면 예시 JSON을 수정한 뒤 "Send" 버튼을 클릭합니다.
4. 우측 하단에서 Mock 응답 본문과 헤더를 바로 확인할 수 있습니다.

## Mock 데이터 관리

- Schema에서 `x-ouroboros-mock` 값을 지정하면 Try 응답에 반영됩니다.
- Response 탭에서 예시 JSON을 직접 편집해 API 문서에서 공유할 Mock 예시를 구성할 수 있습니다.
- "Copy cURL" 버튼을 이용하면 동일한 Mock 호출을 터미널에서 재현할 수 있습니다.

