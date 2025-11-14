# Try 기능

별도 인프라 없이도 API 실행을 추적하고, 필요에 따라 메소드 단위까지 분석하는 방법을 정리했습니다.

## 동작 개요

- **기본값**: 설정 없이 in-memory 저장소로 즉시 사용 가능
- **트리거**: `X-Ouroboros-Try: on` 헤더가 포함된 요청만 추적
- **조회**: 응답 헤더의 `X-Ouroboros-Try-Id`로 성능 데이터를 조회

## 웹 UI에서 사용하기

1. API 상세 화면의 "Try" 탭을 열고 파라미터를 입력합니다.
2. "Send" 버튼을 누르면 헤더가 자동으로 추가되어 요청이 실행됩니다.
3. 응답 패널에서 실행 시간, 상태 코드, Mock 데이터 등을 확인합니다.
4. 우측 "History" 버튼에서 최근 Try 이력을 다시 조회할 수 있습니다.

## 직접 요청 보내기

도구(HTTPie, Postman 등)로 호출할 때는 헤더를 수동으로 추가합니다.

```bash
curl -X POST "http://localhost:8080/api/orders" \
  -H "Content-Type: application/json" \
  -H "X-Ouroboros-Try: on" \
  -d '{"amount": 1000}'
```

응답 헤더의 Try ID를 복사해 `/ouro/tries/{tryId}` 등 REST API로 세부 정보를 확인할 수 있습니다.

## 고급 설정 (선택)

### Method Tracing

내부 메소드 호출까지 추적하려면 아래 설정을 추가합니다.

```yaml
ouroboros.method-tracing.enabled=true
ouroboros.method-tracing.allowed-packages=your.package
management.tracing.sampling.probability=1.0
```

### 트레이스 저장 기간

기본 저장소는 애플리케이션 메모리이므로 재시작 시 Try 기록이 초기화됩니다. 장기 보관이 필요하다면 별도 저장소 연동 기능이 추가될 예정입니다.

## 관련 자료

- [Try & 성능 추적 API](/api/try) – REST API 상세 설명
- [공식 문서](https://ouroboros.co.kr) – 최신 가이드
- `OUROBOROS_TRY_SETUP.md` – Try 기능 설정 세부 가이드

