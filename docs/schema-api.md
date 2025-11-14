# Schema 관리

웹 UI에서 스키마를 작성하고 유지하는 기본 절차를 정리했습니다.

## 웹 UI에서 Schema 관리

스키마 탭에서는 생성, 수정, 삭제가 모두 지원됩니다. REST API를 통한 제어는 [Schema 가이드](/guide/schema)에서 확인하세요.

## Schema 생성

1. 웹 UI에서 Schema 탭으로 이동
2. "New Schema" 버튼 클릭
3. Schema 이름과 속성 정의
4. 저장

## Schema 조회

웹 UI에서 생성된 모든 Schema 목록을 확인할 수 있습니다.

## Schema 수정

우측 패널에서 속성을 수정하면 `orders`, `required` 항목이 자동으로 정렬됩니다.

## Schema 삭제

웹 UI에서 Schema를 선택하고 삭제 버튼을 클릭하면 삭제됩니다.

## Schema 재사용

API 명세서 작성 시 생성한 Schema를 참조하여 재사용할 수 있습니다. `$ref`를 통해 Schema를 참조하세요.

## Mock 데이터 표현식

Schema의 각 속성에 `x-ouroboros-mock` 필드를 추가하여 Mock 데이터 생성 방식을 지정할 수 있습니다.

```json
{
  "properties": {
    "id": {
      "type": "string",
      "x-ouroboros-mock": "{{$random.uuid}}"
    },
    "name": {
      "type": "string",
      "x-ouroboros-mock": "{{$name.fullName}}"
    }
  }
}
```

## 관련 문서

- [Schema 관리 가이드](/guide/schema)
- [Mock API 사용법](/guide/mock-api)
- [API 명세서 작성](/guide/api-spec)

