# Ouroboros Try 기능 & Quick Start 통합 문서

---

# 1. Try 기능

별도 인프라 없이도 API 실행을 추적하고, 필요에 따라 메소드 단위까지 분석하는 방법을 정리했습니다.

## 동작 개요

- **기본값**: 설정 없이 in-memory 저장소로 즉시 사용 가능  
- **트리거**: `X-Ouroboros-Try: on` 헤더가 포함된 요청만 추적  
- **조회**: 응답 헤더의 `X-Ouroboros-Try-Id`로 성능 데이터를 조회  

## 웹 UI에서 사용하기

1. API 상세 화면의 **"Try" 탭**을 열고 파라미터를 입력
2. **Send** 클릭 → 헤더 자동 추가
3. 응답 패널에서 실행 시간, 상태 코드, Mock 여부 확인
4. 우측 **History**에서 최근 Try 이력 조회 가능

## 직접 요청 보내기

```bash
curl -X POST "http://localhost:8080/api/orders"   -H "Content-Type: application/json"   -H "X-Ouroboros-Try: on"   -d '{"amount": 1000}'
```

응답 헤더의 Try ID로 `/ouro/tries/{tryId}` 등 REST API에서 상세 데이터를 조회할 수 있음.

---

## 고급 설정 (선택)

### 1) Method Tracing

내부 메소드 호출까지 추적하려면:

```properties
ouroboros.method-tracing.enabled=true
ouroboros.method-tracing.allowed-packages=your.package
```

### 2) 트레이스 저장 기간

기본 저장소는 애플리케이션 **메모리 기반**이며 재시작하면 데이터 초기화됨.  
개발·테스트 시에는 이것만으로 충분.

### 3) Tempo 연동 (선택)

> 영구 저장 + 고급 분산 트레이싱이 필요할 때

```properties
# Tempo 연동 활성화
ouroboros.tempo.enabled=true
ouroboros.tempo.base-url=http://localhost:3200

# OpenTelemetry Exporter 설정
management.tracing.enabled=true
management.otlp.tracing.endpoint=http://localhost:4318/v1/traces
```

### 4) WebSocket Try 기능 활성화

> **중요:** WebSocket Try 기능 사용 시 메시지 브로커의 `/queue` prefix 허용 필수

---

## 관련 자료

- [Try & 성능 추적 API](/api/try)
- [공식 문서](https://ouroboros.co.kr)
- `OUROBOROS_TRY_SETUP.md`

---

# 2. Try & 성능 추적 API

Try 요청으로 생성된 실행 기록을 REST API로 조회하는 방법을 정리했습니다.

## 기본 흐름

1. 요청에 `X-Ouroboros-Try: on` 추가
2. 응답 헤더의 `X-Ouroboros-Try-Id` 확보
3. 아래 엔드포인트로 상세 데이터 조회

## 엔드포인트 요약

| Method | Path | 설명 |
|--------|------|------|
| GET | `/ouro/tries/{tryId}` | Try 요약 |
| GET | `/ouro/tries/{tryId}/methods` | 메서드 실행 목록 |
| GET | `/ouro/tries/{tryId}/trace` | 트레이스 트리 |

## 요약 예시

```json
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

---

## WebSocket STOMP로 Try 요청하기

### **중요: 서버 메시지 브로커에서 `/queue` prefix 허용 필요**

### 1) 클라이언트 설정 예시 (JS / stompjs)

```javascript
import { Client } from '@stomp/stompjs';

const client = new Client({
  brokerURL: 'ws://localhost:8080/ws',
  reconnectDelay: 5000
});

client.onConnect = () => {
  client.subscribe('/user/queue/ouro/try', (msg) => {
    console.log('Try 결과:', JSON.parse(msg.body));
  });
};

client.activate();
```

### 2) Try 요청 전송

```javascript
client.publish({
  destination: '/app/your-websocket-endpoint',
  body: JSON.stringify({ your: 'data' }),
  headers: { 'X-Ouroboros-Try': 'on' }
});
```

### 3) 서버 브로커 설정 참고

```java
@EnableWebSocketMessageBroker
public class WebSocketConfig implements WebSocketMessageBrokerConfigurer {
  @Override
  public void configureMessageBroker(MessageBrokerRegistry config) {
      config.enableSimpleBroker("/queue", "/topic");
  }
}
```

---

# 3. Quick Start

Ouroboros를 프로젝트에 추가해 동작시키는 가장 빠른 방법입니다.

---

## 전제 조건

- Java 17+
- Spring Boot 3.x
- Gradle or Maven

> Lombok 프로젝트의 경우 `annotationProcessor` 필수  
> springdoc 버전은 **2.8.13 이상** 권장

---

# 1단계: 설치

## Gradle

```gradle
dependencies {
    implementation 'io.github.whitesnakegang:ouroboros:1.0.1'
    implementation 'org.springframework.boot:spring-boot-starter-web'
}
```

## Maven

```xml
<dependency>
    <groupId>io.github.whitesnakegang</groupId>
    <artifactId>ouroboros</artifactId>
    <version>1.0.1</version>
</dependency>
```

---

# 2단계: 설정 (선택)

```yaml
ouroboros:
  enabled: true
  server:
    url: http://localhost:8080
    description: Local Dev
```

---

# 3단계: 애플리케이션 실행

```bash
./gradlew bootRun
```

---

# 4단계: 웹 UI 접속

```
http://localhost:8080/ouroboros/
```

---

# 5단계: 첫 번째 명세 작성

1. **New API**
2. 경로/HTTP 메서드 입력
3. 요청/응답 스키마 작성
4. 저장 → 자동 Mock API 생성

---

# 6단계: Mock API 테스트

```bash
curl http://localhost:8080/api/users
```

---

# 7단계: Try 기능 사용하기

```bash
curl -X GET "http://localhost:8080/api/your-endpoint"   -H "X-Ouroboros-Try: on"
```

웹 UI → Try 탭에서도 실행 가능.

### Method Tracing (선택)

```properties
ouroboros.method-tracing.enabled=true
ouroboros.method-tracing.allowed-packages=your.package
```

---

# 다음 단계

- [기본 사용법](/guide/basic-usage)
- [Mock API](/guide/mock-api)
- [Try 기능](/guide/try-feature)

---

# 참고: 명세 저장 위치

REST 명세는 모두:

```
src/main/resources/ouroboros/rest/ourorest.yml
```

`ReentrantReadWriteLock`으로 안전하게 읽기/쓰기 관리됨.
