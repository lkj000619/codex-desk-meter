# Host-to-device 시험 도구 안내

frame canonical bytes·CRC·sequence·영속 sender·수동 갱신·USB timing의 원본은
[제품 계약](../PRODUCT_CONTRACT.md)의 §3~§4다. 이 문서는 운영자용 도구 범위를 설명한다.
후보는 제품 계약과 [frame schema](../../experiments/schema/cdm-frame.schema.json)를 읽는다.

`FixtureRegistry`는 fixture를 모으는 host 도구이며, `ReferenceReceiver`는 frame/CRC/sequence를
검사하는 host 기준 모델이다. snapshot의 schema 검사는 수행하지만 source 시각의 의미와
firmware의 단조 수신 시계를 모두 검증하는 모델은 아니다.
`ReferenceReceiver.stale`은 envelope의 sent_at 기준이므로 제품의 source-age와
receive-age 합격 근거로 사용하지 않는다. source 의미 검사는
`validate-end-to-end-result.py`의 `validate_snapshot(..., reference_time=...)`로 대조하고,
실제 runtime 경로의 시험은 [평가 계약](evaluation-contract.md)에서 연결한다.
실제 firmware receiver·USB 전송·LCD 관측은 별도 증거가 필요하다. host write receipt는 device ACK가 아니다.
`run-host-device-pipeline.py`의 기본은 dry-run이며 보드에 접근하지 않는다.
실제 전송에는 명시적인 port와 운영자가 승인한 serial backend가 필요하다.
LoopbackSerial은 시험용이며 실물 수락으로 표현하지 않는다.

예제의 host_simulated/reference_model_only·I3/I4 not_run·product_pass=false 의미를 유지한다.
합성 입력·host 시험 성공을 실시간 계정 수집 성공이나 실물 제품 합격으로 승격하지 않는다.
이전 상세 도구 설명은 Git의 `d6da44a:docs/experiments/host-device-pipeline-contract.md`에서 복구한다.
