# API 문서

Ouroboros는 REST API로 명세와 스키마를 제어할 수 있는 엔드포인트를 제공합니다.

## REST API 명세 관리

엔드포인트 요약입니다. 모든 응답은 `GlobalApiResponse` 포맷으로 반환됩니다.

| Method | Path | 설명 |
|--------|------|------|
| POST | `/ouro/rest-specs` | REST API 명세 생성 (중복 path+method는 409 반환) |
| GET | `/ouro/rest-specs` | 모든 명세 조회 |
| GET | `/ouro/rest-specs/{id}` | ID로 명세 상세 조회 |
| PUT | `/ouro/rest-specs/{id}` | 명세 업데이트 (필드별 부분 수정 지원) |
| DELETE | `/ouro/rest-specs/{id}` | 명세 삭제 (경로 내 마지막 메서드이면 path도 삭제) |
| POST | `/ouro/rest-specs/import` | OpenAPI 3.1 YAML 파일 Import (중복 항목은 -import 접미사로 저장) |
| GET | `/ouro/rest-specs/export/yaml` | 현재 저장된 `ourorest.yml` 다운로드 |

상세 제약과 예시는 [backend/docs/endpoints](https://github.com/whitesnakegang/ouroboros/tree/develop/backend/docs/endpoints) 문서에서 확인할 수 있습니다.

## 스키마 관리

| Method | Path | 설명 |
|--------|------|------|
| POST | `/ouro/rest-specs/schemas` | 스키마 생성 (`schemaName` 중복 시 409) |
| GET | `/ouro/rest-specs/schemas` | 스키마 전체 조회 |
| GET | `/ouro/rest-specs/schemas/{schemaName}` | 단일 스키마 조회 |
| PUT | `/ouro/rest-specs/schemas/{schemaName}` | 스키마 수정 (제공된 필드만 교체) |
| DELETE | `/ouro/rest-specs/schemas/{schemaName}` | 스키마 삭제 |

스키마는 재사용 가능한 `#/components/schemas` 항목으로 저장되며, 누락된 참조는 자동으로 placeholder가 생성됩니다.

## 응답 포맷

### 성공 응답

```json
{
  "status": 200,
  "data": { ... },
  "message": "REST API specification created successfully",
  "error": null
}
```

### 에러 응답

```json
{
  "status": 409,
  "data": null,
  "message": "API specification already exists",
  "error": {
    "code": "DUPLICATE_API",
    "details": "An API specification with the same path and method already exists"
  }
}
```

## API 명세서 확인 방법

저장된 명세서는 다음 방법으로 확인할 수 있습니다:

- 웹 UI에서 목록 조회 및 상세 보기
- `GET /ouro/rest-specs/export/yaml`로 다운로드
- `ourorest.yml` 파일 직접 확인

## 관련 문서

- [API 명세서 작성 가이드](/guide/api-spec)
- [Schema 관리 가이드](/guide/schema)
- [Mock API 사용법](/guide/mock-api)

## Try & 성능 추적 API

웹 UI에서 Try 기능을 실행하면 아래 엔드포인트로 성능 데이터를 확인할 수 있습니다.

| Method | Path | 설명 |
|--------|------|------|
| GET | `/ouro/tries/{tryId}` | Try 요약 (상태, HTTP 코드, 총 소요 시간, span 수) |
| GET | `/ouro/tries/{tryId}/methods` | 메서드 실행 목록 (self duration 기준 내림차순, 페이징) |
| GET | `/ouro/tries/{tryId}/trace` | 트레이스 트리 (부모/자식 스팬 구조) |

Try 요청은 웹 UI에서 "Send" 버튼을 눌렀을 때 자동으로 기록되며, 기록된 `tryId`는 응답 헤더 `X-Ouroboros-Try-Id`에서 확인할 수 있습니다.

