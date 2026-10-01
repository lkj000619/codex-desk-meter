# Host-to-device 시험 도구 안내

frame canonical bytes·CRC·sequence·영속 sender·수동 갱신·USB timing의 원본은
[제품 계약](../PRODUCT_CONTRACT.md)의 §3~§4다. 이 문서는 운영자용 도구 범위를 설명한다.
후보는 제품 계약과 [frame schema](../../experiments/schema/cdm-frame.schema.json)를 읽는다.

`FixtureRegistry`와 `ReferenceReceiver`는 host-only conformance oracle이다.
실제 firmware receiver·USB 전송·LCD 관측 증거가 아니다. host write receipt는 device ACK가 아니다.
`run-host-device-pipeline.py`의 기본은 dry-run이며 보드에 접근하지 않는다.
실제 전송에는 명시적인 port와 운영자가 승인한 serial backend가 필요하다.
LoopbackSerial은 시험용이며 실물 수락으로 표현하지 않는다.

예제의 host_simulated/reference_model_only·I3/I4 not_run·product_pass=false 의미를 유지한다.
합성 입력·host 시험 성공을 실시간 계정 수집 성공이나 실물 제품 합격으로 승격하지 않는다.
이전 상세 도구 설명은 Git의 `d6da44a:docs/experiments/host-device-pipeline-contract.md`에서 복구한다.
