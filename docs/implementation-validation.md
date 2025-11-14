# 구현 검증

웹 UI에서 명세와 구현 진행 상태를 관리하고 확인하는 방법을 소개합니다.

> **주의**: Lombok을 사용하는 프로젝트라면 반드시 `annotationProcessor 'org.projectlombok:lombok'`를 빌드 설정에 포함해야 합니다. 이 설정이 없으면 `@ApiState` 메타데이터가 생성되지 않아 자동 검증이 동작하지 않습니다.

## 진행 상태 관리

- Progress 값은 SDK가 명세와 구현 상태를 비교해 자동으로 "mock" 또는 "completed"로 조정합니다.
- Tag 역시 스캔 결과에 따라 자동으로 업데이트되어 현재 구현 상태(implementing, bugfix 등)를 표시합니다.
- 변경 사항은 저장 직후 목록에 반영되어 진행 상황을 수동으로 조작할 필요가 없습니다.

## 상태 확인

목록 또는 상세 화면에서 API별 진행 상태를 한눈에 확인할 수 있으며, 상태에 따라 배지 색상이 표시됩니다.

- `mock`: Mock 응답만 제공 중
- `completed`: 실제 구현이 완료된 엔드포인트

## 자동 검증

사용자가 작성한 명세는 실행 중인 애플리케이션의 OpenAPI 스캔 결과와 자동으로 비교됩니다. 변경사항을 저장하면 SDK가 명세와 구현을 동기화하여 불일치 항목을 표시합니다.

- `x-ouroboros-diff`: 요청/응답/엔드포인트 차이를 자동 표시
- `x-ouroboros-progress`: 구현 완료 시 `completed`로 자동 조정
- 웹 UI에서 강조 표시된 필드를 통해 차이점을 바로 확인할 수 있습니다.
- Lombok을 사용하는 프로젝트라면 `annotationProcessor 'org.projectlombok:lombok'` 설정이 있어야 사용자의 lombok이 정상 동작합니다.

