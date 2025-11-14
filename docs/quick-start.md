# Quick Start

Ouroboros를 프로젝트에 추가하고 기본 기능을 동작시키는 절차를 정리합니다.

## 전제 조건

- Java 17 이상
- Spring Boot 3.x
- Gradle 또는 Maven

> **주의**: Lombok을 사용하는 프로젝트라면 `annotationProcessor 'org.projectlombok:lombok'` 설정이 필수입니다. 누락되면 `@ApiState` 스캔이 이루어지지 않아 명세-구현 자동 검증이 동작하지 않습니다.
>
> Swagger UI (springdoc-openapi)를 함께 사용하는 경우, `springdoc-openapi-starter-webmvc-ui` 버전이 **2.8.13 이상**이어야 합니다. 2.2.0 같은 낮은 버전에서는 충돌이 발생할 수 있습니다. 자세한 내용은 [알려진 버그](/guide/known-issues)를 참고하세요.

## 1단계: 설치

### Gradle

```gradle
dependencies {
    implementation 'io.github.whitesnakegang:ouroboros:1.0.1'
    implementation 'org.springframework.boot:spring-boot-starter-web'
}
```

### Maven

```xml
<dependency>
    <groupId>io.github.whitesnakegang</groupId>
    <artifactId>ouroboros</artifactId>
    <version>1.0.1</version>
</dependency>
```

라이브러리는 내부적으로 `spring-boot-starter-actuator`와 `spring-boot-starter-aop`를 함께 제공합니다. Mock 서버와 REST API 컨트롤러는 자동 구성으로 등록되므로 별도 설정 없이 사용할 수 있습니다.

Lombok을 사용한다면 반드시 `annotationProcessor 'org.projectlombok:lombok'`를 추가해야 `@ApiState` 기반 자동 스캔이 정상 동작합니다.

## 2단계: 설정 (선택사항)

`application.yml` 또는 `application.properties`에 다음 설정을 추가할 수 있습니다:

```yaml
ouroboros:
  enabled: true  # 기본값: true
  server:
    url: http://localhost:8080
    description: Local Development Server
```

설정을 비활성화하면 모든 컨트롤러, 필터, 자동 구성이 등록되지 않습니다. (예: `ouroboros.enabled=false`)

## 3단계: 애플리케이션 실행

```bash
./gradlew bootRun
```

또는 IDE에서 Spring Boot 애플리케이션을 실행하세요.

## 4단계: 웹 UI 접속

브라우저에서 다음 주소로 접속하세요:

```
http://localhost:8080/ouroboros/
```

웹 UI에서 API 명세를 생성하고 관리할 수 있습니다.

## 5단계: 첫 번째 API 명세서 작성

웹 UI에서:

1. "New API" 버튼 클릭
2. 경로, HTTP 메서드, 요약 등 입력
3. 요청/응답 스키마 정의
4. 저장

저장하면 자동으로 Mock API가 생성되어 바로 테스트할 수 있습니다.

## 6단계: Mock API 테스트

명세서의 `x-ouroboros-progress`가 `mock`인 경우, 해당 엔드포인트로 요청하면 자동으로 Mock 응답이 반환됩니다.

```bash
curl http://localhost:8080/api/users
```

Mock 엔드포인트 판정은 `x-ouroboros-progress` 값이 `mock`인 경우에만 이루어집니다.

## 7단계: Try 기능 사용하기

Try 기능은 API 요청의 실행 시간을 추적하고 기록합니다. **별도 설정 없이 기본으로 활성화**되어 있으며, 메모리 기반 저장소를 사용해 즉시 결과를 확인할 수 있습니다.

### 기본 사용

- 웹 UI의 "Try" 탭에서 실행하면 헤더가 자동으로 추가됩니다.
- 직접 호출 시 `X-Ouroboros-Try: on` 헤더를 붙이세요.

```bash
curl -X GET "http://localhost:8080/api/your-endpoint" \
  -H "X-Ouroboros-Try: on"
```

응답 헤더의 `X-Ouroboros-Try-Id` 값을 사용해 조회 API에서 상세 정보를 확인할 수 있습니다.

### 웹 UI에서 확인

1. API 상세 화면에서 "Try" 탭 선택
2. 요청 파라미터 입력 후 "Send" 클릭
3. 결과 영역과 "History" 패널에서 실행 이력 확인

### 선택 사항: Method Tracing

메소드 수준까지 추적하려면 다음 설정을 추가합니다. (Try 기능 기본 사용에는 필요 없음)

```yaml
ouroboros.method-tracing.enabled=true
ouroboros.method-tracing.allowed-packages=your.package
management.tracing.sampling.probability=1.0
```

상세 설정은 [Try 기능 가이드](/guide/try-feature)와 `OUROBOROS_TRY_SETUP.md`를 참고하세요.

## 다음 단계

- [기본 사용법](/guide/basic-usage) - API 명세 관리의 기본 워크플로우
- [API 명세서 작성](/guide/api-spec) - 상세한 명세서 작성 방법
- [Mock API](/guide/mock-api) - Mock 서버 사용법
- [Try 기능](/guide/try-feature) - 성능 추적 및 분석

## 참고: 명세 저장 위치

모든 REST 명세는 애플리케이션 루트 기준 `src/main/resources/ouroboros/rest/ourorest.yml` 파일 하나에 저장됩니다. 라이브러리는 **ReentrantReadWriteLock**을 사용해 해당 파일을 안전하게 읽고 쓰며, 저장 시 자동으로 `x-ouroboros-*` 확장 필드를 채워 넣습니다.

