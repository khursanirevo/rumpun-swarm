"""s193 w1: the light lanes record, forty-eighth iteration.

Ground truth measured 2026-09-22 (solo):

- the fifty guards re-ran green solo: the guide lint (4), the
  readme verbs lint (2), the route-probe serve table (2), the s139
  record (2), the s140 record (2), the s147 record (2), the s148
  record (2), the s149 record (2), the s150 record (2), the s152
  record (2), the s153 record (2), the s154 record (2), the s155
  record (2), the s156 record (2), the s157 record (2), the s158
  record (2), the s159 record (2), the s160 record (2), the s161
  record (2), the s162 record (2), the s163 record (2), the s164
  record (2), the s165 record (2), the s166 record (2), the s167
  record (2), the s168 record (2), the s169 record (2), the s170
  record (2), the s171 record (2), the s172 record (2), the s173
  record (2), the s174 record (2), the s175 record (2), the s176
  record (2), the s177 record (2), the s178 record (2), the s179
  record (2), the s180 record (2), the s181 record (2), the s182
  record (2), the s183 record (2), the s184 record (2), the s185
  record (2), the s186 record (2), the s187 record (2), the s188
  record (2), the s189 record (2), the s190
  record (2), the s191 record (2), the s192 record (2): 102 passed, rc 0,
  /tmp/s193-w1-guards.log.
- one bounded route probe re-confirmed the serve table: the exact
  glm route shape (.rumpun/rumpun.yaml line 38), --model glm-5.3
  (the s125/s132/s139/s140/s145/s146/s147/s148/s149/s150/s152/s153/
  s154/s155/s156/s157/s158/s159/s160/s161/s162/s163/s164/s165/s166/
  s167/s168/s169/s170/s171/s172/s173/s174/s175/s176/s177/s178/s179/
  s180/s181/s182/s183/s184/s185/s186/s187/s188/s189/s190/s191/s192/s193 precedent),
  one call, rc 0, stdout reply `ok`. The stderr carried the known
  catalog warning (CLI-side text, the s125 classification; 788
  bytes, cmp-identical to the s192 trail). Trail:
  /tmp/s193-w1-probe.out and /tmp/s193-w1-probe.err (prompt:
  /tmp/s193-w1-probe-prompt.txt, rc: /tmp/s193-w1-probe.rc).
- drift: none. All 49 guards shared with the s192 sweep are
  byte-identical to it (fresh sha256 each, compared against the
  rows in tests/test_s192_light_lanes_48.py); the s192 record
  joined the guards at
  7d8a52a12777501070afb9548184c93e83807c2c15cbaa2f20d7e2fd1aee6064.

The record: the guards' versions (sha256 of each guard file's
bytes), the probe result, the sweep date. Reads only: no network,
no writes.

A red on the versions pin means a guard moved since this sweep; the
next steady-state cycle re-runs the guard and refreshes the record.
"""

from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path

SWEEP_DATE = "2026-09-22"
GUARD_VERSIONS = {
    "tests/test_s136_full_guide_lint.py":
        "208e9054eedc61cc7d590d99caf5fbc50821ccc81d8d793e81d7fbd36a77642e",
    "tests/test_s128_readme_verbs_lint.py":
        "5795fa17b6831697116554833514f41547b42d3642ef1da183c28051b2bc1378",
    "tests/test_s136_route_probes.py":
        "9ecd825b54025199a8f308d7ff5ea580bd31763f96bc71d059b4eb48f4ccef02",
    "tests/test_s139_light_lanes_sweep.py":
        "a329b1d9a30884e986e80ab32d48faac165b806cfec8ce5467909ec76ad13539",
    "tests/test_s140_steady_sweep_2.py":
        "0bae2fc3e78f11ff4ac6c70da6bd0dcffbf0be8c2ea23cf26b2d3b0a74fab26a",
    "tests/test_s147_light_lanes_3.py":
        "9992877f3ecfb6028ca2bffb40ba32f9add4af3ccdad2cf7dda13ce2b5e9cc14",
    "tests/test_s148_light_lanes_4.py":
        "d24a5c5688562be620305dc0b884b5311971535736ace2282b8e898060f54912",
    "tests/test_s149_light_lanes_5.py":
        "fe40794b7d93b152123c33dad44ec3aeccd83298e5a2203574424e3bc0029554",
    "tests/test_s150_light_lanes_6.py":
        "be4bd73a28df1cb74f62087b86d77dfc304b3d05e9e01b6412796ac193595be6",
    "tests/test_s152_light_lanes_8.py":
        "d691c2f7e16ff87a06d44365771c9246a8c47ab68712ef713eeb658f713b1590",
    "tests/test_s153_light_lanes_9.py":
        "9592e9c244ed8328d06cbad3e4ebd0c36546f203ddcf0d4e1701570de7c1b786",
    "tests/test_s154_light_lanes_10.py":
        "70da5afea95c628a4f73f6cf0fa25c17776cfc444ad37ee143a009a4f1b6a9b3",
    "tests/test_s155_light_lanes_11.py":
        "35590aa85b5c2dd9c948c7ebd9b183194fda2e1c4546fbc1e070ce9d95abada2",
    "tests/test_s156_light_lanes_12.py":
        "dc243d25d70502e0f45ca5a553da0e06f52a489943fdfc6e5875ab54cf96b613",
    "tests/test_s157_light_lanes_13.py":
        "b50cdb9bb01880334211ad9ddf68f6fefd3f34d134f5f443f6cebe3ba260dbcb",
    "tests/test_s158_light_lanes_14.py":
        "4bcb6e8ac8e9814192feeaf3cda04866cdc3d295716e92dddfa0199ae416678c",
    "tests/test_s159_light_lanes_15.py":
        "b5a395943c69039c9b3a73c23d580f2926a5b6e5b13426c18f24ee8e849f4d7f",
    "tests/test_s160_light_lanes_16.py":
        "dd804828429bea869d997725b285fd9447ce24544970f67cbd6459b5cebbc6ff",
    "tests/test_s161_light_lanes_17.py":
        "9c11fc5ca902b8bf4461b25721e793854de769f1d17632f62b6aac6f54c3bd90",
    "tests/test_s162_light_lanes_18.py":
        "566b094e86c868adf74d01c6ce941976fa88b6806b0794ed411a5ef21283712f",
    "tests/test_s163_light_lanes_19.py":
        "11ba35d7547b714c187d79d4624f95fd98713d0b706f558ac8b59db35c8c5afd",
    "tests/test_s164_light_lanes_20.py":
        "ace442c3a395ff0dd6d1cc1d58a62cc59f818a2609df1e5d1dba4e86509c3a27",
    "tests/test_s165_light_lanes_21.py":
        "e703a22945c0d3a365d462c18a9e544659d82bd876320044a8206b339d80ab16",
    "tests/test_s166_light_lanes_22.py":
        "cb9ec237a77dadc7f709ce97d7d6a78579863de0959f5a12bbc58176e799f07e",
    "tests/test_s167_light_lanes_23.py":
        "fb31d085498162ca9681d7a0b9bb727c84359916f18b9069eb1ce8cf89160b0f",
    "tests/test_s168_light_lanes_24.py":
        "7c726ba52f390c51a519556a8ffdc623d3b3698cfc403157c8ec7befe19a45b4",
    "tests/test_s169_light_lanes_25.py":
        "289486657fbdc838d506fbae2a84808a5f6a28d10d2462b7cb0baa343fe5d4d9",
    "tests/test_s170_light_lanes_26.py":
        "ce4361e15e35f9dfaeadb9aadd01590ca0604fb0955dca5e288d97e71e21bbd3",
    "tests/test_s171_light_lanes_27.py":
        "7bbfd7fbeeccce80b02985d1fd3222beaac901c1ab87d16f6f1ee1e0a2f2d177",
    "tests/test_s172_light_lanes_28.py":
        "fa0440459e10353c9c30fa54260c4c1c8aaebfb5771614f3e66d078dac0fb069",
    "tests/test_s173_light_lanes_29.py":
        "7116cde889e7e704cebd77bdcbac43fe2a23b0d28e07f5e80389d7181218386a",
    "tests/test_s174_light_lanes_30.py":
        "9e0d152b95ed3e6fe0e715bc7401290cf9632015ebe23418185d3417f6acc767",
    "tests/test_s175_light_lanes_31.py":
        "72e4f1dd8facea5e9d8c758b4336f7116de834deed1f31c6b25d484a4fb7fbe2",
    "tests/test_s176_light_lanes_32.py":
        "6cd4c5de415ccdbd7114d96a4fc0c53be37616d50c5d1d434d9e03516aa4e41f",
    "tests/test_s177_light_lanes_33.py":
        "544cf6b518603fff8a2669a296ed68ed9e9f6cd305bb57fc325f050b652eaaca",
    "tests/test_s178_light_lanes_34.py":
        "edd242b5e4a7717a0583e7299f57fffc70b3f913b44381161db7279df4585bb1",
    "tests/test_s179_light_lanes_35.py":
        "272c6c9c4893c8bd420dd23e5ec52a4de1eec4420d47b81eab87b13b186593c6",
    "tests/test_s180_light_lanes_36.py":
        "4c60e1e17db465225c68f5487f083bbdb11845ea96dd4820753207f4305c11ed",
    "tests/test_s181_light_lanes_37.py":
        "acf23f7e6cab3d3e1ffd807db6dd43eaf0857bf4364bc1f5d6e4cd94e82656d3",
    "tests/test_s182_light_lanes_38.py":
        "aa4985288594eefa9ce0e07635b96b23340045e59e2a0a88afb432da6a8b533d",
    "tests/test_s183_light_lanes_39.py":
        "d78ba8e9319c5b03e58eb5161accb253f9694eabfa2999f59d992a88acc95bbf",
    "tests/test_s184_light_lanes_40.py":
        "6e4b43cbc6e01b4e204c866081a200a39421f1c29145bc17ecac222e2caa945f",
    "tests/test_s185_light_lanes_41.py":
        "fc28f922833faffa21002f35afc588a81be839e84b9ad18d5934c4350b06ff0f",
    "tests/test_s186_light_lanes_42.py":
        "1a63705ec3480dc9164ce0da1e4e13d8577a2f4468bf57e61ca0075e9c28373c",
    "tests/test_s187_light_lanes_43.py":
        "08d1c50c95508a256bf0189924f704f99267b8a557f4968a311e65a209c5e0a6",
    "tests/test_s188_light_lanes_44.py":
        "06e071de2e2c7f4fad6c409f3d8d61a662e23b4c1c9b83c247eb7ace5c84a132",
    "tests/test_s189_light_lanes_45.py":
        "760a184eb8ba2c2b063fee1b41b2b6f8dd0a1911ec4d02560e751f9e8f9ac18e",
    "tests/test_s190_light_lanes_46.py":
        "00f975aadbef1a6f051ed3d03f02eef6f244d69f44caefda68b954b392e0c48b",
    "tests/test_s191_light_lanes_47.py":
        "5e481d7e048570cb1d8d1befbf8e13d03dd38242644371f6a8c9f2bddf0e4188",
    "tests/test_s192_light_lanes_48.py":
        "7d8a52a12777501070afb9548184c93e83807c2c15cbaa2f20d7e2fd1aee6064",
}

# The bounded probe result (one call, 2026-09-22).
PROBE = {
    "route": "glm",
    "model": "glm-5.3",
    "rc": 0,
    "reply": "ok",
}

S136 = Path(__file__).resolve().parent / "test_s136_route_probes.py"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_guard_versions_still_current() -> None:
    """Each recorded guard hash still matches the file's bytes."""
    repo = Path(__file__).resolve().parents[1]
    moved = [
        rel
        for rel, recorded in GUARD_VERSIONS.items()
        if _sha256(repo / rel) != recorded
    ]
    assert not moved, f"guards moved since the {SWEEP_DATE} sweep: {moved}"


def test_serve_table_still_claims_serving() -> None:
    """The s136 serve table's glm verdict still claims serving glm-5.3."""
    spec = importlib.util.spec_from_file_location("_s193_s136", S136)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    verdict = module._SERVE_TABLE[PROBE["route"]]
    assert verdict.startswith("serving"), f"the glm verdict drifted: {verdict!r}"
    assert PROBE["model"] in verdict, f"the verdict lost the model: {verdict!r}"
