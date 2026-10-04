import unittest
import tempfile
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from pc_collector_sender import PersistentSequenceManager, PcCollectorSender
from host_device_pipeline import LoopbackSerial, ReferenceReceiver, PipelineError

class TestPcCollectorSender(unittest.TestCase):
    def test_persistent_sequence_lifecycle(self):
        with tempfile.TemporaryDirectory() as td:
            mgr = PersistentSequenceManager(td, "test-dev-1")
            
            # Uninitialized access must fail
            with self.assertRaises(PipelineError):
                mgr.reserve_next()

            # Explicit initialization to 1
            seq = mgr.initialize_new(1)
            self.assertEqual(seq, 1)

            # Reservation increments
            self.assertEqual(mgr.reserve_next(), 1)
            self.assertEqual(mgr.reserve_next(), 2)
            self.assertEqual(mgr.reserve_next(), 3)

            # Re-instantiating manager loads persisted state
            mgr2 = PersistentSequenceManager(td, "test-dev-1")
            self.assertEqual(mgr2.get_last_reserved(), 3)
            self.assertEqual(mgr2.reserve_next(), 4)

    def test_sequence_consumed_on_failed_transmission(self):
        with tempfile.TemporaryDirectory() as td:
            sender = PcCollectorSender(device_alias="failing-dev", state_dir=td)
            sender.seq_manager.initialize_new(10)

            # Class that fails on write
            class FailingSerial:
                def write(self, data):
                    raise IOError("Write failed mid-stream")

            try:
                sender.execute_send_step(loopback=FailingSerial())
            except IOError:
                pass

            # Sequence 10 must have been consumed!
            self.assertEqual(sender.seq_manager.get_last_reserved(), 10)
            
            # Next attempt must use 11
            loopback = LoopbackSerial()
            res = sender.execute_send_step(loopback=loopback)
            self.assertEqual(res["sequence"], 11)

    def test_contract_7_accept_1_reject_8_accept(self):
        """Contract requirement: 같은 receiver에 7 수락 -> 재시작 뒤 1 거부 -> 영속화한 8 수락 시험."""
        with tempfile.TemporaryDirectory() as td:
            receiver = ReferenceReceiver()
            sender = PcCollectorSender(device_alias="dev-contract-c3", state_dir=td)
            sender.seq_manager.initialize_new(7)

            # 1. Send seq 7 to receiver
            loopback = LoopbackSerial()
            res1 = sender.execute_send_step(loopback=loopback, sent_at="2026-09-10T00:00:00Z")
            self.assertEqual(res1["sequence"], 7)
            recv_res1 = receiver.receive(loopback.writes[0], reference_time="2026-09-10T00:00:00Z")
            self.assertTrue(recv_res1.accepted, "Sequence 7 must be accepted")
            self.assertEqual(receiver.state.sequence, 7)

            # 2. Simulate bad reset/restart attempting sequence 1 -> rejected!
            bad_sender = PcCollectorSender(device_alias="bad-dev", state_dir=td)
            bad_sender.seq_manager.initialize_new(1)
            bad_loopback = LoopbackSerial()
            res_bad = bad_sender.execute_send_step(loopback=bad_loopback, sent_at="2026-09-10T00:01:00Z")
            self.assertEqual(res_bad["sequence"], 1)
            recv_res_bad = receiver.receive(bad_loopback.writes[0], reference_time="2026-09-10T00:01:00Z")
            self.assertFalse(recv_res_bad.accepted, "Sequence 1 must be rejected by receiver")
            self.assertEqual(recv_res_bad.code, "OUT_OF_ORDER_SEQUENCE")
            self.assertEqual(receiver.state.sequence, 7)

            # 3. Normal restart with persisted state advances from 7 -> 8 -> accepted!
            loopback2 = LoopbackSerial()
            res2 = sender.execute_send_step(loopback=loopback2, sent_at="2026-09-10T00:02:00Z")
            self.assertEqual(res2["sequence"], 8)
            recv_res2 = receiver.receive(loopback2.writes[0], reference_time="2026-09-10T00:02:00Z")
            self.assertTrue(recv_res2.accepted, "Persisted sequence 8 must be accepted")
            self.assertEqual(receiver.state.sequence, 8)

    def test_legacy_collector_mode(self):
        with tempfile.TemporaryDirectory() as td:
            sender = PcCollectorSender(
                device_alias="legacy-dev",
                state_dir=td,
                reference_time="2026-09-11T00:00:00Z",
                use_legacy=True,
            )
            sender.seq_manager.initialize_new(0)
            frame, line = sender.collect_and_build(sequence=0, sent_at="2026-09-11T00:00:00Z")
            self.assertEqual(len(frame["payload"]["usage"]), 1)
            self.assertEqual(len(frame["payload"]["global_resets"]), 2)
            usage = frame["payload"]["usage"][0]
            self.assertEqual(usage["provider_id"], "codex")
            self.assertEqual(len(usage["windows"]), 2)
            self.assertEqual(usage["windows"][0]["percent_remaining"], 58.0)
            self.assertEqual(usage["windows"][1]["percent_remaining"], 82.0)


if __name__ == "__main__":
    unittest.main()



