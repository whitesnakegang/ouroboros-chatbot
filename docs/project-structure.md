# 프로젝트 구조

Ouroboros 프로젝트의 구조를 설명합니다.

## 패키지 구조

```
kr.co.ouroboros/
├── ui/
│   └── rest/
│       ├── spec/controller/     [REST API & Schema CRUD endpoints]
│       └── tryit/controller/    [Try/QA endpoints]
├── core/
│   ├── global/
│   │   ├── annotation/          [ApiState annotation]
│   │   ├── config/              [Auto-configuration]
│   │   ├── handler/             [Protocol strategy + SpecSyncPipeline]
│   │   ├── manager/             [OuroApiSpecManager - CENTRAL CACHE]
│   │   ├── mock/                [Mock data generation with Faker]
│   │   └── response/            [GlobalApiResponse wrapper]
│   └── rest/
│       ├── common/dto/          [OpenAPI 3.1.0 DTOs]
│       ├── common/yaml/         [RestApiYamlParser]
│       ├── spec/
│       │   ├── service/         [REST API & Schema services]
│       │   ├── validator/       [YAML structure validators]
│       │   └── exception/       [Custom exceptions]
│       ├── handler/             [Diff helpers & comparators]
│       ├── mock/                [Mock server filter & registry]
│       ├── filter/              [ApiState method filter]
│       └── tryit/               [OpenTelemetry tracing & Tempo integration]
│           ├── identification/  [Try request filter]
│           ├── infrastructure/  [Tracing, instrumentation, Tempo client]
│           ├── trace/           [Trace analysis & issue detection]
│           └── service/         [Try result services]
└── websocket/                   [WebSocket support - in progress]
```

## 핵심 컴포넌트

- **OuroApiSpecManager**: 명세서 캐시의 단일 소스 (중앙 캐시)
- **OuroProtocolHandler**: 프로토콜 전략 패턴 (REST, GraphQL, WebSocket 지원)
- **RestApiYamlParser**: OpenAPI 3.1.0 YAML 파싱
- **OuroborosMockFilter**: Mock 서버 필터
- **ApiState Filter**: 메소드 트래킹 필터

## 데이터 저장

모든 API 명세서는 다음 위치에 단일 파일로 저장됩니다:

```
{프로젝트}/src/main/resources/ouroboros/rest/ourorest.yml
```

