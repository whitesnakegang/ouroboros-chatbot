# 알려진 버그

Ouroboros 사용 시 주의해야 할 알려진 이슈와 해결 방법을 정리합니다.

## Swagger UI와의 충돌

**문제:** Swagger UI (springdoc-openapi)가 프로젝트에 설치되어 있으면 Ouroboros와 충돌이 발생할 수 있습니다.

**증상:**
- 애플리케이션 시작 시 에러 발생
- OpenAPI 스키마 파싱 오류
- 웹 UI 접속 불가

**원인:** Swagger UI와 Ouroboros가 모두 OpenAPI 스키마를 처리하려고 할 때 경로 충돌이나 빈 설정 충돌이 발생합니다. 특히 `springdoc-openapi-starter-webmvc-ui` 버전이 **2.8.13 미만** (예: 2.2.0)인 경우 호환성 문제가 발생합니다.

### 해결 방법

`springdoc-openapi-starter-webmvc-ui`를 **2.8.13 이상**으로 업그레이드하세요.

```gradle
// Gradle
implementation 'org.springdoc:springdoc-openapi-starter-webmvc-ui:2.8.13'
```

```xml
// Maven
<dependency>
    <groupId>org.springdoc</groupId>
    <artifactId>springdoc-openapi-starter-webmvc-ui</artifactId>
    <version>2.8.13</version>
</dependency>
```

> **참고:** Ouroboros는 자체 웹 UI를 제공하므로 Swagger UI와 함께 사용할 필요가 없습니다. Ouroboros의 웹 UI에서 API 명세를 관리하고 Mock 서버를 사용할 수 있습니다.

## Spring Boot 4.0.0 미지원

**문제:** Ouroboros는 현재 Spring Boot 4.0.0에서 작동하지 않습니다.

**지원 버전:** Ouroboros는 **Spring Boot 3.5.7 이하** 버전만 지원합니다.

**원인:** Spring Boot 4.0.0에서 패키지 경로가 변경되어 Ouroboros가 기존 경로를 참조하는 부분에서 호환성 문제가 발생합니다.

### 해결 방법

Spring Boot 버전을 **3.5.7 이하**로 다운그레이드하거나, Spring Boot 4.0.0 지원이 추가될 때까지 기다려주세요.

```gradle
// Gradle
implementation platform('org.springframework.boot:spring-boot-dependencies:3.5.7')
```

```xml
// Maven
<parent>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-parent</artifactId>
    <version>3.5.7</version>
</parent>
```

## 버그 리포트

다른 버그를 발견하셨거나 개선 사항이 있으시면 GitHub Issues에 리포트해 주세요.

[GitHub Issues 열기](https://github.com/whitesnakegang/ouroboros/issues)

