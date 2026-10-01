# PC 수집기·ESP32 통합 계약 안내

현행 제품의 I1~I4·provider identity·global snapshot 매핑·USB wire·복구 규칙은
[제품 계약](../PRODUCT_CONTRACT.md)의 §1~§3이 소유한다. 후보에게는 그 문서만 제공한다.
이 안내는 운영자용이며 별도 제품 요구사항을 정의하지 않는다.

기계 계약은 [UsageSnapshot schema](../../experiments/schema/usage-snapshot.schema.json)와
[cdm frame schema](../../experiments/schema/cdm-frame.schema.json)다.
실험 결과의 필드·검증은 [평가 안내](evaluation-contract.md)를 따른다.
host oracle의 성공은 실제 firmware receiver·USB·LCD 증거를 대신하지 않는다.

이전 upstream 비교·설계 초안은 Git의 `d6da44a:docs/experiments/integration-contract.md`에
보존돼 있다. 다른 제품의 성공·API·소스는 현재 후보의 고정 입력이나 합격 증거가 아니다.
