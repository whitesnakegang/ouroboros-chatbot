# Try & 성능 추적 API

Try 요청으로 생성된 실행 기록을 REST API로 조회하는 방법을 정리했습니다. 현재 SDK는 애플리케이션 메모리에 기록을 저장하며, 별도 외부 저장소 연동은 제공하지 않습니다.

## 기본 흐름

1. 요청에 `X-Ouroboros-Try: on` 헤더를 추가해 실행합니다.
2. 응답 헤더의 `X-Ouroboros-Try-Id` 값이 추적 식별자가 됩니다.
3. 아래 엔드포인트를 사용해 Try 요약, 메서드 목록, 트레이스를 확인합니다.

## 엔드포인트 요약

| Method | Path | 설명 |
|--------|------|------|
| GET | `/ouro/tries/{tryId}` | Try 요약 (상태, HTTP 코드, 총 소요 시간, span 수 등) |
| GET | `/ouro/tries/{tryId}/methods` | 메서드 실행 목록 (selfDuration 기준 내림차순, page/size 파라미터 지원) |
| GET | `/ouro/tries/{tryId}/trace` | 트레이스 트리 (부모/자식 스팬 구조와 소요 시간) |

## 요약 응답 예시

```
GET /ouro/tries/{tryId}

{
  "status": 200,
  "data": {
    "tryId": "a2b4...",
    "traceId": "1b8f...",
    "status": "COMPLETED",
    "statusCode": 200,
    "totalDurationMs": 153,
    "spanCount": 12
  }
}
```

메서드 목록 API는 `page`, `size` 파라미터를 지원하며, `hasMore` 필드를 통해 다음 페이지 여부를 제공합니다.

