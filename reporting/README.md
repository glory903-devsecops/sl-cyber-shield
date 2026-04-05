# Hybrid Report Pipeline

이 디렉터리는 보고서를 아래 흐름으로 고정 산출물로 변환합니다.

1. Python 시뮬레이션이 구조화된 JSON을 `03.FinalReport/data/`에 저장
2. Node 기반 React 정적 렌더러가 HTML을 생성
3. Tailwind CSS를 빌드하여 HTML에 인라인 주입
4. Google Chrome headless가 가능하면 PDF도 함께 생성

핵심 원칙:

- 런타임 서버 없이 정적 HTML만 배포
- 제출용 데모는 항상 빌드 완료 산출물만 사용
- 새 파이프라인 실패 시 기존 HTML 파일은 fallback으로 유지

샘플 빌드:

```bash
npm install
npm run reports:sample
```
