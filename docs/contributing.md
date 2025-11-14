# 컨트리뷰션 가이드

Ouroboros 프로젝트에 기여하는 방법을 안내합니다.

## 브랜치 전략

- **Main Branch**: `develop` (not main)
- `feature/*` - 새로운 기능 (develop에서 브랜치)
- `fix/*` - 버그 수정 (develop에서 브랜치)
- `hotfix/*` - 긴급 프로덕션 수정 (main에서 브랜치)
- `release/*` - 릴리스 준비 (develop에서 브랜치)

## 커밋 컨벤션

```
<type>: <description under 50 chars>

Optional body explaining what and why
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`, `perf`, `ci`, `build`

## 코드 스타일

- 주석은 영어로 작성
- 작업 완료 후 package-info 작성
- Javadoc 주석 항상 작성

## 로컬 테스트

```bash
# 라이브러리 빌드
./gradlew build

# 로컬 Maven 저장소에 퍼블리시
./gradlew publishToMavenLocal

# 테스트 프로젝트에서 사용
dependencies {
    implementation 'io.github.whitesnakegang:ouroboros:1.0.1'
}
```

